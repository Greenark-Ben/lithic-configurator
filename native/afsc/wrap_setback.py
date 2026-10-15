# -*- coding: utf-8 -*-
"""Native hosted placement wrapper for the fixed-size AFSC assembly."""
import os,io,json,traceback
from pyrevit import DB
from System.Collections.Generic import List

def build(application,active,assembly_report,template,output,source,helpers,builder):
    if os.path.exists(output):raise ValueError('A new output directory is required')
    os.makedirs(output);f=None;p=None;child=None;tx=None
    report={'status':'running','activeBefore':builder.snapshot(active),'widthHeightFlex':False,'openingMovementVerified':False,'source':source}
    MM=builder.MM;point=builder.point
    def write(stage=None):
        if stage:report['stage']=stage
        with io.open(os.path.join(output,'proof.json'),'w',encoding='utf-8') as stream:stream.write(json.dumps(report,indent=2))
    try:
        write('create-hosted-wrapper')
        f=application.NewFamilyDocument(template)
        child=application.OpenDocumentFile(assembly_report['files']['family'])
        loaded=child.LoadFamily(f);child.Close(False);child=None
        symbol=f.GetElement(list(loaded.GetFamilySymbolIds())[0])
        tx=DB.Transaction(f,'LITHIC native window setback');tx.Start();handler=builder.fail_closed(tx,report)
        fm=f.FamilyManager
        if fm.CurrentType is None:fm.NewType('AFSC M9x12 closed setback study')
        width,height=source['frameSizeMm'];half=width/2
        for key,value in [(DB.BuiltInParameter.FAMILY_WIDTH_PARAM,width),(DB.BuiltInParameter.FAMILY_HEIGHT_PARAM,height)]:fm.SetFormula(fm.get_Parameter(key),str(value)+' mm')
        sill=next(q for q in fm.Parameters if q.Definition.Name=='Default Sill Height');z=fm.CurrentType.AsDouble(sill)/MM
        host=next(e for e in DB.FilteredElementCollector(f).OfClass(DB.Wall));exterior=1 if host.Orientation.Y>0 else -1
        if exterior!=1:raise ValueError('Wrapper adapter currently requires the inspected +Y exterior template')
        shared=helpers.shared_parameters(f,source)
        fm=f.FamilyManager
        shared={q.Definition.Name:q for q in fm.Parameters if q.Definition.Name in shared}
        symbol.Activate();inst=f.FamilyCreate.NewFamilyInstance(point(0,0,z),symbol,DB.Structure.StructuralType.NonStructural)
        f.Regenerate()
        from System import Guid
        report['nestedParameterBindings']=[]
        for entry in source['authoringRules']['sharedParameterSchema']['parameters']:
            ep=inst.get_Parameter(Guid(entry['guid']));fp=shared[entry['name']]
            if entry['dataType']=='material':fm.Set(fp,ep.AsElementId())
            else:fm.Set(fp,ep.AsString() or '')
            if entry['dataType']=='material':
                fm.AssociateElementParameterToFamilyParameter(ep,fp)
                linked=fm.GetAssociatedFamilyParameter(ep)
                passed=linked is not None and linked.Id==fp.Id
            else:
                # Immutable provenance is copied to the wrapper. Revit correctly
                # disallows associating the non-user-modifiable nested fields.
                passed=fm.CurrentType.AsString(fp)==ep.AsString()
            report['nestedParameterBindings'].append({'name':entry['name'],'passed':passed,'method':'associated' if entry['dataType']=='material' else 'immutable-copy'})
        if not all(r['passed'] for r in report['nestedParameterBindings']):raise ValueError('Nested shared material/provenance binding failed')
        for opening in list(DB.FilteredElementCollector(f).OfClass(DB.Opening)):f.Delete(opening.Id)
        f.FamilyCreate.NewOpening(host,builder.curves([point(-half,0,z),point(half,0,z),point(half,0,z+height),point(-half,0,z+height)]))
        view=next(v for v in DB.FilteredElementCollector(f).OfClass(DB.ViewPlan) if not v.IsTemplate)
        outside=DB.HostObjectUtils.GetSideFaces(host,DB.ShellLayerType.Exterior)[0]
        references=inst.GetReferences(DB.FamilyInstanceReferenceType.CenterFrontBack)
        if not references.Count:raise ValueError('Nested assembly needs a Centre Front/Back reference')
        refs=DB.ReferenceArray();refs.Append(outside);refs.Append(references[0])
        dimension=f.FamilyCreate.NewDimension(view,DB.Line.CreateBound(point(-half-150,-500,0),point(-half-150,500,0)),refs)
        setback=fm.AddParameter('Window Setback',DB.GroupTypeId.Geometry,DB.SpecTypeId.Length,True)
        fm.SetDescription(setback,'Distance inward from host wall exterior face to front of timber frame; aluminium projects beyond this datum. Placement only; frame size is fixed.')
        dimension.FamilyLabel=setback;f.Regenerate()
        report['datum']='Exterior host wall face to front of timber frame; positive inward; aluminium projection excluded'
        report['familySetbackChecks']=[]
        baseline=builder.signature(inst)
        initial_y=inst.Location.Point.Y/MM
        for value in [0,50,100,200,50]:
            fm.Set(setback,value*MM);f.Regenerate()
            expected_y=host.Width/2/MM-value
            actual=builder.signature(inst);dy=inst.Location.Point.Y/MM-initial_y
            geometry=len(actual)==len(baseline) and all(abs(a-b)<=max(.1,abs(b)*1e-6) for r,s in zip(actual,baseline) for a,b in zip(r,[s[0],s[1],s[2],s[3]+dy,s[4]+dy,s[5],s[6]]))
            report['familySetbackChecks'].append({'valueMm':value,'actualDatumYmm':inst.Location.Point.Y/MM,'expectedDatumYmm':expected_y,'rigidGeometryPassed':geometry,'passed':geometry and abs(inst.Location.Point.Y/MM-expected_y)<.1})
        if not all(r['passed'] for r in report['familySetbackChecks']):raise ValueError('Native setback did not move the full assembly rigidly')
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Wrapper rolled back; inspect transactionFailures')
        tx=None
        report['familyWarnings']=[w.GetDescriptionText() for w in f.GetWarnings()]
        uid=inst.UniqueId;expected=builder.signature(inst)
        family=os.path.join(output,'LITHIC-AFSC-M9x12-880x1180-SETBACK-STUDY.rfa');f.SaveAs(family,DB.SaveAsOptions());f.Close(False);f=None
        write('reopen-wrapper-and-place')
        f=application.OpenDocumentFile(family);nested=f.GetElement(uid)
        report['familyPersistencePassed']=expected==builder.signature(nested)
        p=application.NewProjectDocument(DB.UnitSystem.Metric);loaded=f.LoadFamily(p);sym=p.GetElement(list(loaded.GetFamilySymbolIds())[0])
        tx=DB.Transaction(p,'LITHIC isolated setback proof');tx.Start();handler=builder.fail_closed(tx,report);sym.Activate();level=DB.Level.Create(p,0)
        wt=next(t for t in DB.FilteredElementCollector(p).OfClass(DB.WallType) if t.Kind==DB.WallKind.Basic and t.Width>0)
        wall=DB.Wall.Create(p,DB.Line.CreateBound(point(-2200,0,0),point(2200,0,0)),wt.Id,level.Id,3000*MM,0,False,False);p.Regenerate();uncut=sum(s.Volume for s in builder.solids(wall))
        placed=p.Create.NewFamilyInstance(point(0,0,900),sym,wall,level,DB.Structure.StructuralType.NonStructural);p.Regenerate()
        if placed.FacingOrientation.DotProduct(wall.Orientation)<0:placed.flipFacing();p.Regenerate()
        fp=placed.LookupParameter('Window Setback')
        report['projectSetbackChecks']=[]
        report['nativeSillDatumMm']=z
        # Read physical geometry in parent coordinates, independently of parameter labels.
        expected_volume=sum(row[0] for row in expected)
        for value in [0,50,100,200,50]:
            fp.Set(value*MM);p.Regenerate();tr=placed.GetTransform();actual=builder.signature(placed,tr.Inverse)
            # Parent template host thickness is recorded below, never assumed to be the project host.
            base_y=report['familySetbackChecks'][-1]['actualDatumYmm']
            delta=wt.Width/2/MM-value-base_y
            shifted=sorted([[r[0],r[1],r[2],r[3]+delta,r[4]+delta,r[5],r[6]] for r in expected])
            rigid=len(actual)==len(shifted) and all(abs(a-b)<=max(.1,abs(b)*1e-6) for r,s in zip(actual,shifted) for a,b in zip(r,s))
            removed=(uncut-sum(s.Volume for s in builder.solids(wall)))/MM**3
            opening_passed=abs(removed-width*height*wt.Width/MM)<max(1,width*height*wt.Width/MM*.001)
            report['projectSetbackChecks'].append({'valueMm':value,'rigidGeometryPassed':rigid,'openingPassed':opening_passed,'components':len(actual),'passed':rigid and opening_passed})
        report['hostThicknessChecks']=[]
        for thickness in [100,200,300,500]:
            test_type=wt.Duplicate('LITHIC isolated '+str(thickness)+' mm')
            layers=List[DB.CompoundStructureLayer]();layers.Add(DB.CompoundStructureLayer(thickness*MM,DB.MaterialFunctionAssignment.Structure,DB.ElementId.InvalidElementId))
            test_type.SetCompoundStructure(DB.CompoundStructure.CreateSimpleCompoundStructure(layers))
            wall.ChangeTypeId(test_type.Id);p.Regenerate()
            for value in [0,50,100]:
                fp.Set(value*MM);p.Regenerate();actual=builder.signature(placed,placed.GetTransform().Inverse)
                delta=thickness/2-value-base_y
                shifted=sorted([[r[0],r[1],r[2],r[3]+delta,r[4]+delta,r[5],r[6]] for r in expected])
                rigid=len(actual)==len(shifted) and all(abs(a-b)<=max(.1,abs(b)*1e-6) for r,s in zip(actual,shifted) for a,b in zip(r,s))
                cut_volume=sum(s.Volume for s in builder.solids(wall))/MM**3
                expected_cut=(4400*3000-width*height)*thickness
                opening_passed=abs(cut_volume-expected_cut)<max(1,expected_cut*.001)
                report['hostThicknessChecks'].append({'hostMm':thickness,'setbackMm':value,'rigidGeometryPassed':rigid,'openingPassed':opening_passed,'passed':rigid and opening_passed})
        wall.ChangeTypeId(wt.Id);fp.Set(50*MM);p.Regenerate()
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Project placement rolled back')
        tx=None
        project=os.path.join(output,'LITHIC-AFSC-setback-review.rvt');p.SaveAs(project,DB.SaveAsOptions())
        report['files']={'family':family,'project':project};report['familySignatures']=assembly_report['familySignatures'];report['assembly']=assembly_report['files']['family']
        report['nestedUniqueId']=uid;report['projectInstanceUniqueId']=placed.UniqueId;report['projectWarnings']=[w.GetDescriptionText() for w in p.GetWarnings()]
        report['status']='setback-study-created-review-required' if report['familyPersistencePassed'] and all(r['passed'] for r in report['projectSetbackChecks']+report['hostThicknessChecks']) and not report['familyWarnings'] and not report['projectWarnings'] else 'technical-checks-failed'
    except:report['status']='failed';report['traceback']=traceback.format_exc()
    finally:
        if tx is not None and tx.GetStatus()==DB.TransactionStatus.Started:tx.RollBack()
        for owned in [p,f,child]:
            if owned is not None and owned.IsValidObject:owned.Close(False)
        report['activeAfter']=builder.snapshot(active);report['activeProjectPreserved']=report['activeBefore']==report['activeAfter'];write()
    return report
