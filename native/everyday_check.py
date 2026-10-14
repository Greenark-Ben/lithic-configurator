# -*- coding: utf-8 -*-
"""Desktop-only use audit of a downloaded cloud model, in isolated documents.

Call run(application, active, input_folder, output_folder, native_root) through
pyRevit. Never loads anything into, saves or transacts on the active project.
"""
from __future__ import division
import datetime
import hashlib
import io
import json
import os
import sys
import traceback
from System.Collections.Generic import List
from pyrevit import DB

MM = 1.0 / 304.8
MATERIALS = ['Timber Material', 'Aluminium Material', 'Glazing Material',
             'Glazing Spacer Material', 'Glazing Seal Material']


class OrientedInstance(object):
    """Use geometric hand/facing axes, including Revit's flip state."""
    def __init__(self, instance, exterior):
        self.instance = instance
        self.Document = instance.Document
        self.transform = DB.Transform.Identity
        self.transform.Origin = instance.GetTransform().Origin
        self.transform.BasisX = instance.HandOrientation
        self.transform.BasisY = instance.FacingOrientation.Multiply(exterior)
        self.transform.BasisZ = instance.GetTransform().BasisZ

    def GetTransform(self):
        return self.transform

    def get_Geometry(self, options):
        return self.instance.get_Geometry(options)


class CaptureFailures(DB.IFailuresPreprocessor):
    def __init__(self, messages):
        self.messages = messages

    def PreprocessFailures(self, accessor):
        for message in accessor.GetFailureMessages():
            self.messages.append({'severity': str(message.GetSeverity()),
                                  'description': message.GetDescriptionText()})
        if any(m['severity'] == 'Error' for m in self.messages):
            return DB.FailureProcessingResult.ProceedWithRollBack
        return DB.FailureProcessingResult.Continue


def snapshot(document):
    return {'title': document.Title, 'path': document.PathName,
            'modified': document.IsModified,
            'elements': DB.FilteredElementCollector(document).GetElementCount(),
            'activeView': document.ActiveView.UniqueId}


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.sha256(stream.read()).hexdigest()


def helpers(native_root):
    # Load only the checked builder's definitions, never its interactive main.
    sys.path.insert(0, native_root)
    path = os.path.join(native_root, 'script.py')
    with io.open(path, encoding='utf-8') as stream:
        code = stream.read().replace('\r\n', '\n').split('\ndef main():\n')[0]
    scope = {'__file__': path}
    exec(compile(code, path, 'exec'), scope)
    return scope


def schedule(project):
    view = DB.ViewSchedule.CreateSchedule(project, DB.ElementId(DB.BuiltInCategory.OST_Windows))
    view.Name = 'AFKC everyday window schedule'
    definition = view.Definition
    definition.IsItemized = True
    fields = {field.GetName(project): field for field in definition.GetSchedulableFields()}
    names = ['Family and Type', 'Mark', 'Width', 'Height', 'Sill Height']
    missing = [name for name in names if name not in fields]
    if missing:
        raise ValueError('Missing schedulable fields: '+str(missing))
    for name in names:
        field = definition.AddField(fields[name])
        field.ColumnHeading = name
    return view, [name for name in MATERIALS if name not in fields]


def schedule_cells(view):
    data = view.GetTableData().GetSectionData(DB.SectionType.Body)
    return [[view.GetCellText(DB.SectionType.Body, row, col)
             for col in range(data.FirstColumnNumber, data.LastColumnNumber+1)]
            for row in range(data.FirstRowNumber, data.LastRowNumber+1)]


def inspect(project, case, specs, exterior, plans, expected_plans, h):
    cases = [{'instanceId': case['instanceId'], 'wallId': case['wallId'],
              'uncutWallMm3': case['uncutWallMm3'],
              'expectedOpeningMm3': case['expectedOpeningMm3']}] + case['hostThicknessCases']
    results = []
    for host_case in cases:
        instance = project.GetElement(host_case['instanceId'])
        wall = project.GetElement(host_case['wallId'])
        frame = OrientedInstance(instance, exterior)
        geometry = h['hosted_geometry_checks'](frame, specs, exterior)
        graphics = h['hosted_plan_checks'](frame, plans, expected_plans)
        removed = host_case['uncutWallMm3'] - h['volume'](wall)
        expected = host_case['expectedOpeningMm3']
        opening = abs(removed-expected) <= max(1, expected*.001)
        bindings = {}
        for name in MATERIALS:
            parameter = instance.Symbol.LookupParameter(name)
            material = project.GetElement(parameter.AsElementId()) if parameter else None
            bindings[name] = material.Name if isinstance(material, DB.Material) else None
        actual_materials = sorted(project.GetElement(mid).Name for mid in instance.GetMaterialIds(False))
        material_passed = None not in bindings.values() and sorted(bindings.values()) == actual_materials
        width = instance.Symbol.get_Parameter(DB.BuiltInParameter.FAMILY_WIDTH_PARAM).AsDouble()/MM
        height = instance.Symbol.get_Parameter(DB.BuiltInParameter.FAMILY_HEIGHT_PARAM).AsDouble()/MM
        results.append({'instanceId': instance.UniqueId, 'wallThicknessMm': wall.WallType.Width/MM,
                        'mirrored': instance.Mirrored, 'handFlipped': instance.HandFlipped,
                        'facingFlipped': instance.FacingFlipped,
                        'geometry': geometry, 'plans': graphics,
                        'openingPassed': opening, 'removedWallMm3': removed,
                        'expectedOpeningMm3': expected,
                        'materialParameters': bindings, 'actualMaterials': actual_materials,
                        'materialsPassed': material_passed,
                        'widthMm': width, 'heightMm': height,
                        'dimensionsPassed': abs(width-1200)<.1 and abs(height-1500)<.1,
                        'hostPassed': instance.Host.Id == wall.Id,
                        'passed': geometry['passed'] and opening and material_passed
                                  and all(p['passed'] for p in graphics.values())
                                  and abs(width-1200)<.1 and abs(height-1500)<.1
                                  and instance.Host.Id == wall.Id})
    return results


def elevations(project, instance):
    level = project.GetElement(instance.LevelId)
    types = {t.ViewFamily: t for t in DB.FilteredElementCollector(project).OfClass(DB.ViewFamilyType)}
    plan = DB.ViewPlan.Create(project, types[DB.ViewFamily.FloorPlan].Id, level.Id)
    plan.Name = 'AFKC elevation placement plan'
    result = []
    for side in ['first', 'second']:
        marker = DB.ElevationMarker.CreateElevationMarker(project, types[DB.ViewFamily.Elevation].Id,
                                                         DB.XYZ(0, 0, 0), 50)
        view = marker.CreateElevation(project, plan.Id, 0)
        project.Regenerate()
        if abs(view.ViewDirection.Y) < .99:
            DB.ElementTransformUtils.RotateElement(project, marker.Id,
                DB.Line.CreateBound(DB.XYZ.Zero, DB.XYZ.BasisZ), 3.141592653589793/2)
            project.Regenerate()
        if side == 'second':
            DB.ElementTransformUtils.RotateElement(project, marker.Id,
                DB.Line.CreateBound(DB.XYZ.Zero, DB.XYZ.BasisZ), 3.141592653589793)
            project.Regenerate()
        direction = view.ViewDirection
        DB.ElementTransformUtils.MoveElement(project, marker.Id, direction.Negate()*2000*MM)
        project.Regenerate()
        view.Name = 'AFKC '+side+' elevation 1-50'
        view.Scale = 50
        view.DetailLevel = DB.ViewDetailLevel.Fine
        view.DisplayStyle = DB.DisplayStyle.HLR
        far = view.get_Parameter(DB.BuiltInParameter.VIEWER_BOUND_OFFSET_FAR)
        if far and not far.IsReadOnly:
            far.Set(3000*MM)
        box = view.CropBox
        inverse = box.Transform.Inverse
        tr = instance.GetTransform()
        points = [inverse.OfPoint(tr.OfPoint(DB.XYZ(x*MM, y*MM, z*MM)))
                  for x in [-600, 600] for y in [-80, 80] for z in [0, 1500]]
        box.Min = DB.XYZ(min(p.X for p in points)-200*MM,
                         min(p.Y for p in points)-200*MM, box.Min.Z)
        box.Max = DB.XYZ(max(p.X for p in points)+200*MM,
                         max(p.Y for p in points)+200*MM, box.Max.Z)
        view.CropBox = box
        view.CropBoxActive = True
        view.CropBoxVisible = False
        for cat in [DB.BuiltInCategory.OST_Levels, DB.BuiltInCategory.OST_Sections]:
            view.SetCategoryHidden(DB.ElementId(cat), True)
        duplicate = project.GetElement(view.Duplicate(DB.ViewDuplicateOption.Duplicate))
        duplicate.Name = 'AFKC '+side+' elevation 1-20'
        duplicate.Scale = 20
        result.extend([view, duplicate])
    return result


def run(application, active, input_folder, output_folder, native_root, scenario_names=None):
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    report = {'kind': 'lithic-everyday-use-report', 'createdAtUtc': datetime.datetime.utcnow().isoformat()+'Z',
              'revitVersion': application.VersionNumber, 'sizeMm': [1200, 1500],
              'nativeParameterFlex': False, 'manufacturerApproved': False,
              'visualReviewPassed': False, 'activeBefore': snapshot(active), 'cases': []}
    project = family = None
    try:
        with io.open(os.path.join(input_folder, 'cloud-proof-report.json'), encoding='utf-8') as stream:
            cloud = json.load(stream)
        case = cloud['cases'][0]
        if case['sizeMm'] != [1200, 1500]:
            raise ValueError('This audit is scoped to the checked 1200 x 1500 configuration.')
        family_path = os.path.join(input_folder, case['familyFile'])
        project_path = os.path.join(input_folder, case['projectFile'])
        active_path = os.path.normcase(os.path.abspath(active.PathName)) if active.PathName else None
        if active_path in [os.path.normcase(os.path.abspath(family_path)), os.path.normcase(os.path.abspath(project_path))]:
            raise ValueError('Audit inputs must be separate from the active document.')
        if digest(family_path) != case['familySha256'] or digest(project_path) != case['projectSha256']:
            raise ValueError('Input files do not match the cloud report hashes.')
        report['inputFamilySha256'] = digest(family_path)
        report['inputProjectSha256'] = digest(project_path)
        h = helpers(native_root)
        with io.open(os.path.join(native_root, 'afkc-source.json'), encoding='utf-8') as stream:
            source = json.load(stream)
        specs = h['native_specs'](source, 1200, 1500)
        family = application.OpenDocumentFile(family_path)
        host = next(iter(DB.FilteredElementCollector(family).OfClass(DB.Wall)))
        exterior = 1 if host.Orientation.Y > 0 else -1
        expected_plans = h['family_plan_signatures'](family)
        family.Close(False)
        family = None
        for name in scenario_names or ['baseline', 'flip-hand', 'flip-facing', 'mirror-left-right', 'mirror-front-back', 'materials']:
            entry = {'name': name, 'status': 'failed'}
            report['cases'].append(entry)
            with io.open(os.path.join(output_folder, 'progress.json'), 'w', encoding='utf-8') as stream:
                stream.write(json.dumps({'case': name, 'stage': 'starting'}))
            try:
                project = application.OpenDocumentFile(project_path)
                working_case = json.loads(json.dumps(case))
                # Reference the hash-verified, unmodified cloud opening once;
                # reuse this reference for the modified and reopened model.
                working_case['uncutWallMm3'] = h['volume'](project.GetElement(case['wallId'])) + case['expectedOpeningMm3']
                instances = [project.GetElement(case['instanceId'])] + [project.GetElement(c['instanceId']) for c in case['hostThicknessCases']]
                host_type_ids = [i.Host.WallType.Id for i in instances]
                entry['beforeOrientation'] = [{'mirrored': i.Mirrored, 'facingFlipped': i.FacingFlipped} for i in instances]
                plans = {lod: project.GetElement(uid) for lod, uid in case['hostSymbolViewIds'].items()}
                tx = DB.Transaction(project, 'LITHIC isolated everyday use '+name)
                tx.Start()
                entry['transactionFailures'] = []
                failure_capture = CaptureFailures(entry['transactionFailures'])
                options = tx.GetFailureHandlingOptions()
                options.SetFailuresPreprocessor(failure_capture)
                options.SetClearAfterRollback(True)
                tx.SetFailureHandlingOptions(options)
                try:
                    for n, instance in enumerate(instances):
                        instance.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).Set('AFKC-'+name+'-'+str(n+1))
                    if name in ['flip-hand', 'flip-facing']:
                        can = 'CanFlipHand' if name == 'flip-hand' else 'CanFlipFacing'
                        if not all(getattr(instance, can) for instance in instances):
                            entry['status'] = 'not-supported'
                            entry['reason'] = can+' is false for this fixed-window family.'
                            tx.RollBack()
                            continue
                        for instance in instances:
                            if name == 'flip-hand':
                                instance.flipHand()
                            else:
                                instance.flipFacing()
                    elif name.startswith('mirror-'):
                        entry['mirrorScope'] = 'host-and-window-assemblies'
                        normal = DB.XYZ.BasisX if name == 'mirror-left-right' else DB.XYZ.BasisY
                        ids = List[DB.ElementId]()
                        for instance in instances:
                            ids.Add(instance.Id); ids.Add(instance.Host.Id)
                        DB.ElementTransformUtils.MirrorElements(project, ids,
                            DB.Plane.CreateByNormalAndOrigin(normal, DB.XYZ.Zero), False)
                    elif name == 'materials':
                        for n, material_name in enumerate(MATERIALS):
                            mid = DB.Material.Create(project, 'AFKC audit '+material_name)
                            mat = project.GetElement(mid)
                            mat.Color = DB.Color(40+n*30, 80+n*20, 100+n*15)
                            if material_name == 'Glazing Material': mat.Transparency = 72
                            instances[0].Symbol.LookupParameter(material_name).Set(mid)
                    project.Regenerate()
                    windows = list(DB.FilteredElementCollector(project).OfClass(DB.FamilyInstance))
                    instances = []
                    for n in range(5):
                        mark = 'AFKC-'+name+'-'+str(n+1)
                        matches = [i for i in windows if i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK)
                                   and i.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).AsString() == mark]
                        if len(matches) != 1: raise ValueError('Expected exactly one instance for '+mark)
                        instances.append(matches[0])
                    working_case['instanceId'] = instances[0].UniqueId
                    for i, host_case in zip(instances[1:], working_case['hostThicknessCases']):
                        host_case['instanceId'] = i.UniqueId
                    drawing_views = []
                    if name == 'baseline':
                        for view in list(DB.FilteredElementCollector(project).OfClass(DB.View)):
                            if view.Name in ['AFKC coarse plan 1-50', 'AFKC medium plan 1-50', 'AFKC fine plan 1-10', 'AFKC sill section', 'AFKC head section']:
                                if 'section' in view.Name: view.Scale = 10
                                drawing_views.append(view)
                                if 'fine plan' in view.Name:
                                    for scale in [20, 50]:
                                        dup = project.GetElement(view.Duplicate(DB.ViewDuplicateOption.Duplicate))
                                        dup.Name = 'AFKC fine plan 1-'+str(scale)+' everyday'; dup.Scale = scale
                                        drawing_views.append(dup)
                        drawing_views.extend(elevations(project, instances[0]))
                        for plan_view in DB.FilteredElementCollector(project).OfClass(DB.ViewPlan):
                            if not plan_view.IsTemplate:
                                plan_view.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Elev), True)
                    else:
                        drawing_views = [view for view in DB.FilteredElementCollector(project).OfClass(DB.View3D)
                                         if view.Name in ['AFKC left bottom corner', 'AFKC right bottom corner']]
                    table, missing_material_fields = schedule(project)
                    entry['nonSchedulableMaterialParameters'] = missing_material_fields
                    if tx.Commit() != DB.TransactionStatus.Committed:
                        raise ValueError('Everyday-use transaction did not commit.')
                except Exception:
                    if tx.GetStatus() == DB.TransactionStatus.Started: tx.RollBack()
                    raise
                # Revit may replace mirrored instances during transaction commit,
                # after the in-transaction element/UniqueId lookup. Resolve the
                # committed instances by their unchanged, unique host walls.
                if name.startswith('mirror-'):
                    walls = list(DB.FilteredElementCollector(project).OfClass(DB.Wall))
                    committed_walls = []
                    for type_id in host_type_ids:
                        matches = [wall for wall in walls if wall.WallType.Id == type_id]
                        if len(matches) != 1: raise ValueError('Expected one committed wall per test host type')
                        committed_walls.append(matches[0])
                    working_case['wallId'] = committed_walls[0].UniqueId
                    for wall, host_case in zip(committed_walls[1:], working_case['hostThicknessCases']):
                        host_case['wallId'] = wall.UniqueId
                    ids = [wall.UniqueId for wall in committed_walls]
                    windows = list(DB.FilteredElementCollector(project).OfClass(DB.FamilyInstance))
                    instances = []
                    for wall_uid in ids:
                        matches = [i for i in windows if i.Host is not None and i.Host.UniqueId == wall_uid]
                        if len(matches) != 1: raise ValueError('Expected one committed window on host '+wall_uid)
                        instances.append(matches[0])
                    mark_tx = DB.Transaction(project, 'Label committed mirrored instances')
                    mark_tx.Start()
                    for n, instance in enumerate(instances):
                        instance.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).Set('AFKC-'+name+'-'+str(n+1))
                    if mark_tx.Commit() != DB.TransactionStatus.Committed:
                        raise ValueError('Mirrored-instance labeling did not commit.')
                    working_case['instanceId'] = instances[0].UniqueId
                    for instance, host_case in zip(instances[1:], working_case['hostThicknessCases']):
                        host_case['instanceId'] = instance.UniqueId
                    view_tx = DB.Transaction(project, 'Orient mirrored review cameras to the aluminium side')
                    view_tx.Start()
                    side = instances[0].FacingOrientation.Y
                    origin = instances[0].GetTransform().Origin
                    for view in drawing_views:
                        sign = -1 if 'left' in view.Name else 1
                        target = origin + DB.XYZ(sign*560*MM, side*50*MM, 40*MM)
                        eye = target + DB.XYZ(sign*.9, side*1.2, .7)
                        forward = (target-eye).Normalize()
                        right = forward.CrossProduct(DB.XYZ.BasisZ).Normalize()
                        up = right.CrossProduct(forward).Normalize()
                        view.SetOrientation(DB.ViewOrientation3D(eye, up, forward))
                    view_tx.Commit()
                entry['initial'] = inspect(project, working_case, specs, exterior, plans, expected_plans, h)
                entry['scheduleCells'] = schedule_cells(table)
                entry['scheduleColumns'] = table.Definition.GetFieldCount()
                text = json.dumps(entry['scheduleCells'])
                entry['schedulePassed'] = entry['scheduleColumns'] == 5 and all('AFKC-'+name+'-'+str(n+1) in text for n in range(5))
                entry['operationApplied'] = (all(row['mirrored'] != before['mirrored'] for row, before in zip(entry['initial'], entry['beforeOrientation'])) if name.startswith('mirror-') else
                                             all(row['facingFlipped'] != before['facingFlipped'] for row, before in zip(entry['initial'], entry['beforeOrientation'])) if name == 'flip-facing' else
                                             all(value.startswith('AFKC audit ') for row in entry['initial'] for value in row['materialParameters'].values()) if name == 'materials' else True)
                table.Export(output_folder, name+'-schedule.txt', DB.ViewScheduleExportOptions())
                entry['views'] = h['export_review_views'](project, drawing_views, output_folder, name)
                entry['warnings'] = [warning.GetDescriptionText() for warning in project.GetWarnings()]
                output = os.path.join(output_folder, 'AFKC-everyday-'+name+'.rvt')
                h['save'](project, output)
                project.Close(False); project = None
                project = application.OpenDocumentFile(output)
                reopened_plans = {lod: project.GetElement(uid) for lod, uid in case['hostSymbolViewIds'].items()}
                entry['reopened'] = inspect(project, working_case, specs, exterior, reopened_plans, expected_plans, h)
                reopened_table = next(view for view in DB.FilteredElementCollector(project).OfClass(DB.ViewSchedule)
                                      if view.Name == 'AFKC everyday window schedule')
                entry['schedulePersisted'] = schedule_cells(reopened_table) == entry['scheduleCells']
                entry['reopenedWarnings'] = [warning.GetDescriptionText() for warning in project.GetWarnings()]
                entry['savedProjectSha256'] = digest(output)
                entry['status'] = 'passed' if all(row['passed'] for row in entry['initial']+entry['reopened']) and entry['operationApplied'] and entry['schedulePassed'] and entry['schedulePersisted'] and not entry['warnings'] and not entry['reopenedWarnings'] else 'failed'
            except Exception:
                entry['error'] = traceback.format_exc()
            finally:
                if project is not None and project.IsValidObject: project.Close(False)
                project = None
                with io.open(os.path.join(output_folder, 'progress.json'), 'w', encoding='utf-8') as stream:
                    stream.write(json.dumps({'case': name, 'stage': 'complete', 'status': entry['status']}))
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        for document in [family, project]:
            if document is not None and document.IsValidObject: document.Close(False)
        report['activeAfter'] = snapshot(active)
        report['activeProjectPreserved'] = report['activeBefore'] == report['activeAfter']
        report['status'] = 'passed-awaiting-visual-review' if report['cases'] and not report.get('error') and all(c['status'] in ['passed', 'not-supported'] for c in report['cases']) and report['activeProjectPreserved'] else 'failed'
        with io.open(os.path.join(output_folder, 'everyday-use-report.json'), 'w', encoding='utf-8') as stream:
            stream.write(json.dumps(report, indent=2))
    return report
