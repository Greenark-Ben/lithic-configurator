# -*- coding: utf-8 -*-
"""LITHIC AFKC native snapshot builder, executed inside Revit by pyRevit.
No HTTP listener, eval, external project edits or automatic warning suppression.
This builder makes fixed-size families; it does NOT claim native parameter flex.
"""
from __future__ import division
import datetime
import hashlib
import io
import json
import os
import sys
import traceback
from pyrevit import DB, forms, revit

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from contract import BUILDER, validate, expected_parts, verification_sizes, native_specs
from authoring import create_forms, create_plan_symbols, authoring_checks, lock_host_depth
from drawings import create_review_views, export_review_views

MM = 1.0 / 304.8
VOLUME = 304.8 ** 3
TOL_MM = 0.1
VOLUME_TOL = 0.001

def xyz(values, exterior=1):
    # Preview X / height Y / exterior depth Z -> Revit X / exterior Y / height Z.
    return DB.XYZ(values[0]*MM, values[2]*MM*exterior, values[1]*MM)

def loop(points):
    curves = DB.CurveArray()
    for i in range(len(points)):
        curves.Append(DB.Line.CreateBound(points[i], points[(i+1) % len(points)]))
    return curves

def solids(element):
    result = []
    def collect(geometry):
        for item in geometry:
            if isinstance(item, DB.Solid) and item.Volume > 1e-10:
                result.append(item)
            elif isinstance(item, DB.GeometryInstance):
                collect(item.GetInstanceGeometry())
    collect(element.get_Geometry(DB.Options()))
    return result

def volume(element):
    return sum(s.Volume for s in solids(element))*VOLUME

def warning_text(document):
    return [w.GetDescriptionText() for w in document.GetWarnings()]

def save(document, path):
    options = DB.SaveAsOptions()
    options.OverwriteExistingFile = False
    document.SaveAs(path, options)

def file_hash(path):
    with open(path, 'rb') as source:
        return hashlib.sha256(source.read()).hexdigest()

def fixed_parameter(document, name, value):
    manager = document.FamilyManager
    builtin = {'Width': DB.BuiltInParameter.FAMILY_WIDTH_PARAM, 'Height': DB.BuiltInParameter.FAMILY_HEIGHT_PARAM}.get(name)
    parameter = manager.get_Parameter(builtin) if builtin is not None else next((p for p in manager.Parameters if p.Definition.Name == name), None)
    if builtin is not None and parameter is None:
        raise ValueError('The Window template lacks its built-in '+name+' parameter.')
    if parameter is None:
        parameter = manager.AddParameter(name, DB.GroupTypeId.Geometry, DB.SpecTypeId.Length, False)
    if parameter.IsInstance:
        raise ValueError('Template parameter '+name+' must be a type parameter.')
    manager.SetFormula(parameter, str(value)+' mm')

def text_parameter(document, name, value):
    manager = document.FamilyManager
    parameter = next((p for p in manager.Parameters if p.Definition.Name == name), None)
    if parameter is None:
        parameter = manager.AddParameter(name, DB.GroupTypeId.IdentityData, DB.SpecTypeId.String.Text, False)
    manager.Set(parameter, value)

def material(document, name, color, transparency=0):
    mid = DB.Material.Create(document, name)
    mat = document.GetElement(mid)
    mat.Color = DB.Color(*color)
    mat.Transparency = transparency
    return mid

def family_checks(document, specs, elements, exterior, materials, source):
    checks=[]
    for spec in specs:
        element=elements[spec['id']];shape=solids(element)
        vertices=[edge.AsCurve().GetEndPoint(i) for solid in shape for edge in solid.Edges for i in [0,1]]
        actual=[min(v.X/MM for v in vertices),max(v.X/MM for v in vertices),min(v.Z/MM for v in vertices),max(v.Z/MM for v in vertices),min(v.Y/MM for v in vertices),max(v.Y/MM for v in vertices)]
        p,size=spec['position'],spec['size'];depth=sorted([(p[2]-size[2]/2)*exterior,(p[2]+size[2]/2)*exterior])
        expected=[p[0]-size[0]/2,p[0]+size[0]/2,p[1]-size[1]/2,p[1]+size[1]/2,depth[0],depth[1]]
        actual_volume=volume(element);minimum=spec['expectedVolumeMm3'];maximum=spec.get('maximumJoinedVolumeMm3',minimum)
        tolerance=max(1,minimum*VOLUME_TOL)
        mat_ok=all(mid==materials[spec['role']] for mid in element.GetMaterialIds(False)) and len(element.GetMaterialIds(False))>0
        native_type=element.GetType().Name
        passed=len(shape)==1 and max(abs(a-b) for a,b in zip(actual,expected))<=TOL_MM and minimum-tolerance<=actual_volume<=maximum+tolerance and mat_ok and native_type==spec['nativeType']
        checks.append({'id':spec['id'],'boundsMm':actual,'expectedBoundsMm':expected,'volumeMm3':actual_volume,'expectedVolumeMm3':minimum,'maximumJoinedVolumeMm3':maximum,'volumeRule':'bounded native join of overlapping source returns' if maximum!=minimum else 'analytic polygon volume','nativeType':native_type,'material':document.GetElement(materials[spec['role']]).Name,'passed':passed})
    return checks

def hosted_geometry_checks(instance,specs,exterior):
    inverse=instance.GetTransform().Inverse
    shapes=solids(instance);checks=[];unused=list(range(len(shapes)))
    for spec in specs:
        p,size=spec['position'],spec['size'];depth=sorted([(p[2]-size[2]/2)*exterior,(p[2]+size[2]/2)*exterior])
        expected=[p[0]-size[0]/2,p[0]+size[0]/2,p[1]-size[1]/2,p[1]+size[1]/2,depth[0],depth[1]]
        choices=[]
        for index in unused:
            solid=shapes[index];vertices=[inverse.OfPoint(edge.AsCurve().GetEndPoint(i)) for edge in solid.Edges for i in [0,1]]
            actual=[min(v.X/MM for v in vertices),max(v.X/MM for v in vertices),min(v.Z/MM for v in vertices),max(v.Z/MM for v in vertices),min(v.Y/MM for v in vertices),max(v.Y/MM for v in vertices)]
            choices.append((max(abs(a-b) for a,b in zip(actual,expected)),index,actual,solid.Volume*VOLUME))
        if not choices:
            checks.append({'id':spec['id'],'passed':False,'error':'Missing hosted solid'});continue
        distance,index,actual,actual_volume=min(choices,key=lambda c:c[0]);unused.remove(index)
        minimum=spec['expectedVolumeMm3'];maximum=spec.get('maximumJoinedVolumeMm3',minimum);tolerance=max(1,minimum*VOLUME_TOL)
        checks.append({'id':spec['id'],'boundsMm':actual,'volumeMm3':actual_volume,'passed':distance<=TOL_MM and minimum-tolerance<=actual_volume<=maximum+tolerance})
    return {'solidCount':len(shapes),'parts':checks,'passed':len(shapes)==22 and not unused and all(c['passed'] for c in checks)}

def plan_line_key(style,curve,transform):
    points=[transform.OfPoint(curve.GetEndPoint(i)) for i in [0,1]]
    return [style,sorted([[round(p.X/MM,3),round(p.Y/MM,3)] for p in points])]

def family_plan_signatures(family):
    result={lod:[] for lod in ['coarse','medium','fine']}
    for element in DB.FilteredElementCollector(family).OfClass(DB.CurveElement):
        if not isinstance(element,DB.SymbolicCurve):continue
        visibility=element.GetVisibility()
        for lod,shown in [('coarse',visibility.IsShownInCoarse),('medium',visibility.IsShownInMedium),('fine',visibility.IsShownInFine)]:
            if shown:result[lod].append(plan_line_key(element.LineStyle.GraphicsStyleCategory.Name,element.GeometryCurve,DB.Transform.Identity))
    for lines in result.values():lines.sort()
    return result

def hosted_plan_checks(instance,views,expected):
    inverse=instance.GetTransform().Inverse;result={}
    for lod,view in views.items():
        actual=[];options=DB.Options();options.View=view
        def collect(geometry):
            for item in geometry:
                if isinstance(item,DB.GeometryInstance):collect(item.GetInstanceGeometry())
                elif isinstance(item,DB.Curve):
                    style=instance.Document.GetElement(item.GraphicsStyleId)
                    if style and style.GraphicsStyleCategory.Name.startswith('LITHIC Plan'):
                        actual.append(plan_line_key(style.GraphicsStyleCategory.Name,item,inverse))
        collect(instance.get_Geometry(options));actual.sort()
        digest=lambda lines:hashlib.sha256(json.dumps(lines,separators=(',',':')).encode('utf-8')).hexdigest()
        result[lod]={'curveCount':len(actual),'expectedCount':len(expected[lod]),'sha256':digest(actual),'expectedSha256':digest(expected[lod]),'passed':actual==expected[lod]}
    return result

def create_host_cases(project,symbol,level,width,height,specs,exterior,expected_plans):
    from System.Collections.Generic import List
    base=next(t for t in DB.FilteredElementCollector(project).OfClass(DB.WallType) if t.Kind==DB.WallKind.Basic and t.GetCompoundStructure() is not None)
    cases=[];plan_views={}
    plan_type=next(t for t in DB.FilteredElementCollector(project).OfClass(DB.ViewFamilyType) if t.ViewFamily==DB.ViewFamily.FloorPlan)
    for lod,detail in [('coarse',DB.ViewDetailLevel.Coarse),('medium',DB.ViewDetailLevel.Medium),('fine',DB.ViewDetailLevel.Fine)]:
        view=DB.ViewPlan.Create(project,plan_type.Id,level.Id);view.Name='LITHIC host symbol check '+lod;view.DetailLevel=detail
        plan_views[lod]=view
    for n,thickness in enumerate([100,200,300,500]):
        typ=base.Duplicate('LITHIC proof host '+str(thickness)+' mm');structure=typ.GetCompoundStructure()
        layers=List[DB.CompoundStructureLayer]();layers.Add(DB.CompoundStructureLayer(thickness*MM,DB.MaterialFunctionAssignment.Structure,DB.ElementId.InvalidElementId));structure.SetLayers(layers);typ.SetCompoundStructure(structure)
        x=(n+1)*8000*MM;wall=DB.Wall.Create(project,DB.Line.CreateBound(DB.XYZ(x-3000*MM,0,0),DB.XYZ(x+3000*MM,0,0)),typ.Id,level.Id,5000*MM,0,False,False)
        project.Regenerate();uncut=volume(wall)
        instance=project.Create.NewFamilyInstance(DB.XYZ(x,0,900*MM),symbol,wall,level,DB.Structure.StructuralType.NonStructural);project.Regenerate()
        for view in plan_views.values():
            vr=view.GetViewRange();vr.SetOffset(DB.PlanViewPlane.TopClipPlane,instance.GetTransform().Origin.Z+(height+100)*MM-level.Elevation);vr.SetOffset(DB.PlanViewPlane.CutPlane,instance.GetTransform().Origin.Z+height/2*MM-level.Elevation);vr.SetOffset(DB.PlanViewPlane.BottomClipPlane,0);vr.SetOffset(DB.PlanViewPlane.ViewDepthPlane,0);view.SetViewRange(vr)
        project.Regenerate();plans=hosted_plan_checks(instance,plan_views,expected_plans)
        geometry=hosted_geometry_checks(instance,specs,exterior);removed=uncut-volume(wall);expected=width*height*thickness
        opening=abs(removed-expected)<=max(1,expected*VOLUME_TOL)
        cases.append({'wallThicknessMm':thickness,'instanceId':instance.UniqueId,'wallId':wall.UniqueId,'geometry':geometry,'planSymbols':plans,'openingPassed':opening,'uncutWallMm3':uncut,'expectedOpeningMm3':expected,'passed':geometry['passed'] and opening and instance.Host.Id==wall.Id and all(p['passed'] for p in plans.values())})
    return cases,{lod:view.UniqueId for lod,view in plan_views.items()}

def build_case(application, template, output, request, source, width, height, digest):
    family, project = None, None
    label = str(width).replace('.', '_')+'x'+str(height).replace('.', '_')
    family_path = os.path.join(output, 'LITHIC-AFKC-'+label+'.rfa')
    project_path = os.path.join(output, 'LITHIC-AFKC-'+label+'-verification.rvt')
    result = {'sizeMm': [width, height], 'status': 'failed', 'geometryMode': 'fixed-size-snapshot', 'nativeParameterFlex': False}
    try:
        family = application.NewFamilyDocument(template)
        if family.OwnerFamily.FamilyCategory.Id != DB.ElementId(DB.BuiltInCategory.OST_Windows) or str(family.OwnerFamily.FamilyPlacementType) != 'OneLevelBasedHosted':
            raise ValueError('Choose an empty wall-hosted Window .rft template.')
        hosts = list(DB.FilteredElementCollector(family).OfClass(DB.Wall))
        if len(hosts) != 1 or abs(abs(hosts[0].Orientation.Y)-1) > 0.001:
            raise ValueError('Template must have one host wall aligned to the X axis.')
        if list(DB.FilteredElementCollector(family).OfClass(DB.GenericForm)):
            raise ValueError('Template contains existing geometry. Use an empty Window template.')
        host = hosts[0]
        exterior = 1 if host.Orientation.Y > 0 else -1
        parts = native_specs(source, width, height)
        tx = DB.Transaction(family, 'LITHIC source-derived fixed-size AFKC')
        tx.Start()
        try:
            for opening in DB.FilteredElementCollector(family).OfClass(DB.Opening).ToElements():
                family.Delete(opening.Id)
            manager = family.FamilyManager
            if manager.CurrentType is None:
                manager.NewType('AFKC '+label)
            for name, value in [('Width', width), ('Height', height), ('AFKC Timber Depth', 105), ('AFKC Frame Sightline', 53.5), ('AFKC Glazing Assembly Depth', 48)]:
                fixed_parameter(family, name, value)
            for name, value in [('LITHIC Request SHA256', digest), ('LITHIC Evidence Status', 'UNAPPROVED_MANUFACTURER_SOURCE_PROTOTYPE'), ('LITHIC Source Drawing', '61-37-F221 rev A'), ('LITHIC Builder', BUILDER), ('LITHIC Geometry Mode', 'fixed-size-snapshot')]:
                text_parameter(family, name, value)
            finishes = request['configuration']
            materials = {
                'timber': material(family, 'LITHIC Timber '+finishes['interior'], (219, 195, 164) if finishes['interior'] == 'timber' else (231, 229, 222)),
                'aluminium': material(family, 'LITHIC Aluminium '+finishes['exterior'], (60, 66, 64) if finishes['exterior'] == 'graphite' else (217, 220, 214)),
                'glazing': material(family, 'LITHIC Glass Panes', (181, 197, 194), 72),
                'spacer': material(family, 'LITHIC Glazing Spacer Aluminium', (135,145,151)),
                'seal': material(family, 'LITHIC Glazing Seal - prototype elastomer', (34,35,37))}
            elements,input_checks = create_forms(family, source, width, height, exterior, materials)
            result['planSymbolCounts'] = create_plan_symbols(family,source,width,height,exterior,elements['aluminium-head-jamb-return'])
            element_ids = {name:element.UniqueId for name,element in elements.items()}
            opening_profile = loop([DB.XYZ(x*MM, 0, z*MM) for x, z in [(-width/2, 0), (width/2, 0), (width/2, height), (-width/2, height)]])
            family.FamilyCreate.NewOpening(host, opening_profile)
            family.Regenerate()
            result['hostDepthConstraints']=lock_host_depth(family,host)
            result['parts'] = family_checks(family, parts, elements, exterior, materials, source)
            if tx.Commit() != DB.TransactionStatus.Committed:
                raise ValueError('Family transaction did not commit.')
        except Exception:
            if tx.GetStatus() == DB.TransactionStatus.Started:
                tx.RollBack()
            raise
        result['familyWarnings'] = warning_text(family)
        save(family, family_path)
        family.Close(False)
        family = application.OpenDocumentFile(family_path)
        result['familyReopened'] = True
        reopened = {name:family.GetElement(uid) for name,uid in element_ids.items()}
        result['reopenedParts'] = family_checks(family, parts, reopened, exterior, materials, source)
        result['persistenceGeometryPassed'] = len(reopened) == 22 and all(p['passed'] for p in result['reopenedParts'])
        result.update(authoring_checks(family,source,width,height,exterior,reopened,input_checks))
        project = application.NewProjectDocument(DB.UnitSystem.Metric)
        loaded = family.LoadFamily(project)
        symbol_ids = list(loaded.GetFamilySymbolIds())
        if len(symbol_ids) != 1:
            raise ValueError('Template must have exactly one family type.')
        symbol = project.GetElement(symbol_ids[0])
        result['scheduleDimensionsPassed'] = abs(symbol.get_Parameter(DB.BuiltInParameter.FAMILY_WIDTH_PARAM).AsDouble()/MM-width) <= TOL_MM and abs(symbol.get_Parameter(DB.BuiltInParameter.FAMILY_HEIGHT_PARAM).AsDouble()/MM-height) <= TOL_MM
        result['provenancePassed'] = symbol.LookupParameter('LITHIC Request SHA256').AsString() == digest and symbol.LookupParameter('LITHIC Evidence Status').AsString() == 'UNAPPROVED_MANUFACTURER_SOURCE_PROTOTYPE'
        wall_type = next(t for t in DB.FilteredElementCollector(project).OfClass(DB.WallType) if t.Kind == DB.WallKind.Basic and t.Width > 0)
        tx = DB.Transaction(project, 'LITHIC isolated host and opening check')
        tx.Start()
        try:
            level = DB.Level.Create(project, 0)
            wall = DB.Wall.Create(project, DB.Line.CreateBound(DB.XYZ(-4000*MM, 0, 0), DB.XYZ(4000*MM, 0, 0)), wall_type.Id, level.Id, 5000*MM, 0, False, False)
            project.Regenerate()
            uncut = volume(wall)
            symbol.Activate()
            project.Regenerate()
            instance = project.Create.NewFamilyInstance(DB.XYZ(0, 0, 900*MM), symbol, wall, level, DB.Structure.StructuralType.NonStructural)
            project.Regenerate()
            if instance.FacingOrientation.DotProduct(wall.Orientation) < 0:
                if not instance.CanFlipFacing:
                    raise ValueError('Could not orient the aluminium towards the exterior.')
                instance.flipFacing()
                project.Regenerate()
            cut = volume(wall)
            expected_removed = width*height*wall_type.Width/MM
            result['hostPassed'] = instance.Host is not None and instance.Host.Id == wall.Id
            result['openingRemovedMm3'] = uncut-cut
            result['expectedOpeningMm3'] = expected_removed
            result['openingPassed'] = abs((uncut-cut)-expected_removed) <= max(1, expected_removed*VOLUME_TOL)
            transform = instance.GetTransform()
            exterior_world = transform.OfVector(DB.XYZ(0, exterior, 0))
            result['exteriorPassed'] = exterior_world.DotProduct(wall.Orientation) > 0.999
            result['instanceId'] = instance.UniqueId
            result['wallId'] = wall.UniqueId
            expected_plans=family_plan_signatures(family)
            result['hostThicknessCases'],result['hostSymbolViewIds']=create_host_cases(project,symbol,level,width,height,parts,exterior,expected_plans)
            views = create_review_views(project,instance,width,height,exterior)
            view_ids = [v.UniqueId for v in views]
            if tx.Commit() != DB.TransactionStatus.Committed:
                raise ValueError('Placement transaction did not commit.')
        except Exception:
            if tx.GetStatus() == DB.TransactionStatus.Started:
                tx.RollBack()
            raise
        result['drawingEvidence'] = export_review_views(project,views,output,label)
        result['projectWarnings'] = warning_text(project)
        save(project, project_path)
        project.Close(False)
        project = application.OpenDocumentFile(project_path)
        persisted_instance = project.GetElement(result['instanceId'])
        persisted_wall = project.GetElement(result['wallId'])
        result['projectReopened'] = True
        result['hostPersisted'] = persisted_instance.Host.Id == persisted_wall.Id
        result['drawingViewsPersisted'] = all(project.GetElement(uid) is not None for uid in view_ids)
        result['visualReviewStatus'] = 'exported-views-await-visual-review'
        result['openingPersisted'] = abs((uncut-volume(persisted_wall))-expected_removed) <= max(1, expected_removed*VOLUME_TOL)
        for case in result['hostThicknessCases']:
            persisted=project.GetElement(case['instanceId']);persisted_host=project.GetElement(case['wallId'])
            case['reopenedGeometry']=hosted_geometry_checks(persisted,parts,exterior)
            case['reopenedPlanSymbols']=hosted_plan_checks(persisted,{lod:project.GetElement(uid) for lod,uid in result['hostSymbolViewIds'].items()},expected_plans)
            case['reopenedOpeningPassed']=abs((case['uncutWallMm3']-volume(persisted_host))-case['expectedOpeningMm3'])<=max(1,case['expectedOpeningMm3']*VOLUME_TOL)
            case['savedReopenedPassed']=case['reopenedGeometry']['passed'] and case['reopenedOpeningPassed'] and persisted.Host.Id==persisted_host.Id and all(p['passed'] for p in case['reopenedPlanSymbols'].values())
        result['hostedGeometryStablePassed']=all(c['passed'] and c['savedReopenedPassed'] for c in result['hostThicknessCases'])
        result['reopenedWarnings'] = warning_text(family)+warning_text(project)
        result['familyFile'] = os.path.basename(family_path)
        result['familySha256'] = file_hash(family_path)
        result['projectFile'] = os.path.basename(project_path)
        result['projectSha256'] = file_hash(project_path)
        required = ['scheduleDimensionsPassed', 'provenancePassed', 'hostPassed', 'openingPassed', 'exteriorPassed', 'familyReopened', 'projectReopened', 'persistenceGeometryPassed', 'hostPersisted', 'openingPersisted','nativeAuthoringPassed','materialsBoundPassed','cornerChecksPassed','cavitiesEmptyPassed','planVisibilityPassed','drawingViewsPersisted','hostedGeometryStablePassed']
        result['status'] = 'passed' if all(result.get(k) is True for k in required) and all(p['passed'] for p in result['parts']) and not result['familyWarnings'] and not result['projectWarnings'] and not result['reopenedWarnings'] else 'failed'
    except Exception as error:
        result['error'] = str(error)
        result['traceback'] = traceback.format_exc()
    finally:
        for document in [project, family]:
            if document is not None and document.IsValidObject and document.PathName != revit.uidoc.Document.PathName:
                document.Close(False)
    return result

def main():
    # Running in a fresh isolated document avoids touching the user's active project.
    request_path = forms.pick_file(file_ext='json', title='Choose request.json from your LITHIC handoff')
    if not request_path:
        return
    bundle = os.path.dirname(request_path)
    with open(request_path, 'rb') as stream:
        raw = stream.read()
    with io.open(os.path.join(bundle, 'manifest.json'), encoding='utf-8') as stream:
        manifest = json.load(stream)
    with io.open(os.path.join(HERE, 'afkc-source.json'), encoding='utf-8') as stream:
        source = json.load(stream)
    request, digest = validate(raw, manifest, source)
    template = forms.pick_file(file_ext='rft', title='Choose an empty wall-hosted Window template')
    if not template:
        return
    folder = forms.pick_folder(title='Choose where to save the LITHIC Revit results')
    if not folder:
        return
    application = revit.doc.Application
    if int(application.VersionNumber) < 2024:
        raise ValueError('This handoff requires Revit 2024 or later.')
    output = os.path.join(folder, 'LITHIC-AFKC-'+datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')+'-'+digest[:8])
    os.mkdir(output)
    report = {'kind': 'lithic-native-report', 'schemaVersion': '0.2', 'builder': BUILDER, 'requestSha256': digest, 'createdAt': datetime.datetime.utcnow().isoformat()+'Z', 'revitVersion': application.VersionNumber, 'geometryMode': 'fixed-size-snapshot', 'nativeParameterFlex': False, 'manufacturerApproved': False, 'templateSha256': file_hash(template), 'cases': []}
    for width, height in verification_sizes(request):
        report['cases'].append(build_case(application, template, output, request, source, width, height, digest))
    report['status'] = 'passed' if all(case['status'] == 'passed' for case in report['cases']) else 'failed'
    with io.open(os.path.join(output, 'native-report.json'), 'w', encoding='utf-8') as stream:
        stream.write(json.dumps(report, indent=2, ensure_ascii=False))
    forms.alert('Revit checks: '+report['status']+'\n\nResults: '+output+'\n\nImport native-report.json into LITHIC. These are fixed-size prototype families; native parameter flex is not implemented.', title='LITHIC native handoff')

try:
    main()
except Exception as error:
    forms.alert(str(error)+'\n\nNo verified family is claimed.\n'+traceback.format_exc(), title='LITHIC handoff stopped')
