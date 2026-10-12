# -*- coding: utf-8 -*-
"""LITHIC AFKC native snapshot builder, executed inside Revit by pyRevit.
No HTTP listener, eval, external project edits or automatic warning suppression.
This first builder makes fixed-size families; it does NOT claim native parameter flex.
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
from contract import BUILDER, validate, expected_parts, verification_sizes, volume_mm3

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

def create_form(document, part, exterior, material_id):
    if 'sweep' in part:
        sweep = part['sweep']
        origin, inward = sweep['originMm'], sweep['inward']
        vertices = [xyz([origin[i]+inward[i]*u+(z if i == 2 else 0) for i in range(3)], exterior) for u, z in sweep['pointsMm']]
        normal = xyz(sweep['axis'], exterior).Normalize()
        length = sweep['lengthMm']
    else:
        x, h, z = part['position']
        w, height, depth = part['size']
        start = z-depth/2
        vertices = [xyz(v, exterior) for v in [[x-w/2, h-height/2, start], [x+w/2, h-height/2, start], [x+w/2, h+height/2, start], [x-w/2, h+height/2, start]]]
        normal, length = DB.XYZ(0, exterior, 0), depth
    plane = DB.SketchPlane.Create(document, DB.Plane.CreateByNormalAndOrigin(normal, vertices[0]))
    loops = DB.CurveArrArray()
    loops.Append(loop(vertices))
    # A straight polygon sweep is exactly representable as a native extrusion.
    element = document.FamilyCreate.NewExtrusion(True, loops, plane, length*MM)
    element.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM).Set(material_id)
    category = document.Settings.Categories.NewSubcategory(document.OwnerFamily.FamilyCategory, 'LITHIC '+part['id'])
    element.Subcategory = category
    return element

def family_checks(document, parts, elements, exterior, materials):
    checks = []
    for part, element in zip(parts, elements):
        bbox = element.get_BoundingBox(None)
        actual = [bbox.Min.X/MM, bbox.Max.X/MM, bbox.Min.Z/MM, bbox.Max.Z/MM, bbox.Min.Y/MM, bbox.Max.Y/MM]
        p, size = part['position'], part['size']
        z = sorted([(p[2]-size[2]/2)*exterior, (p[2]+size[2]/2)*exterior])
        expected = [p[0]-size[0]/2, p[0]+size[0]/2, p[1]-size[1]/2, p[1]+size[1]/2, z[0], z[1]]
        actual_volume, expected_volume = volume(element), volume_mm3(part)
        shape_ok = max(abs(a-b) for a, b in zip(actual, expected)) <= TOL_MM and abs(actual_volume-expected_volume) <= max(1, expected_volume*VOLUME_TOL)
        mat_id = element.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM).AsElementId()
        mat_ok = mat_id == materials[part['role']]
        checks.append({'id': part['id'], 'boundsMm': actual, 'expectedBoundsMm': expected, 'volumeMm3': actual_volume, 'expectedVolumeMm3': expected_volume, 'material': document.GetElement(mat_id).Name, 'passed': shape_ok and mat_ok and len(solids(element)) == 1})
    return checks

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
        parts = expected_parts(source, width, height)
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
                'glazing': material(family, 'LITHIC Glazing unresolved 48 mm assembly', (181, 197, 194), 72)}
            elements = [create_form(family, part, exterior, materials[part['role']]) for part in parts]
            opening_profile = loop([DB.XYZ(x*MM, 0, z*MM) for x, z in [(-width/2, 0), (width/2, 0), (width/2, height), (-width/2, height)]])
            family.FamilyCreate.NewOpening(host, opening_profile)
            family.Regenerate()
            result['parts'] = family_checks(family, parts, elements, exterior, materials)
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
        reopened = {e.Subcategory.Name: e for e in DB.FilteredElementCollector(family).OfClass(DB.GenericForm) if e.Subcategory is not None}
        result['reopenedParts'] = family_checks(family, parts, [reopened['LITHIC '+part['id']] for part in parts], exterior, materials)
        result['persistenceGeometryPassed'] = len(reopened) == 9 and all(p['passed'] for p in result['reopenedParts'])
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
            if tx.Commit() != DB.TransactionStatus.Committed:
                raise ValueError('Placement transaction did not commit.')
        except Exception:
            if tx.GetStatus() == DB.TransactionStatus.Started:
                tx.RollBack()
            raise
        result['projectWarnings'] = warning_text(project)
        save(project, project_path)
        project.Close(False)
        project = application.OpenDocumentFile(project_path)
        persisted_instance = project.GetElement(result['instanceId'])
        persisted_wall = project.GetElement(result['wallId'])
        result['projectReopened'] = True
        result['hostPersisted'] = persisted_instance.Host.Id == persisted_wall.Id
        result['openingPersisted'] = abs((uncut-volume(persisted_wall))-expected_removed) <= max(1, expected_removed*VOLUME_TOL)
        result['reopenedWarnings'] = warning_text(family)+warning_text(project)
        result['familyFile'] = os.path.basename(family_path)
        result['familySha256'] = file_hash(family_path)
        result['projectFile'] = os.path.basename(project_path)
        result['projectSha256'] = file_hash(project_path)
        required = ['scheduleDimensionsPassed', 'provenancePassed', 'hostPassed', 'openingPassed', 'exteriorPassed', 'familyReopened', 'projectReopened', 'persistenceGeometryPassed', 'hostPersisted', 'openingPersisted']
        result['status'] = 'passed' if all(result.get(k) is True for k in required) and all(p['passed'] for p in result['parts']) and not result['familyWarnings'] and not result['projectWarnings'] and not result['reopenedWarnings'] else 'failed'
    except Exception as error:
        result['error'] = str(error)
        result['traceback'] = traceback.format_exc()
    finally:
        for document in [project, family]:
            if document is not None and document.IsValidObject:
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
    report = {'kind': 'lithic-native-report', 'schemaVersion': '0.1', 'builder': BUILDER, 'requestSha256': digest, 'createdAt': datetime.datetime.utcnow().isoformat()+'Z', 'revitVersion': application.VersionNumber, 'geometryMode': 'fixed-size-snapshot', 'nativeParameterFlex': False, 'manufacturerApproved': False, 'templateSha256': file_hash(template), 'cases': []}
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
