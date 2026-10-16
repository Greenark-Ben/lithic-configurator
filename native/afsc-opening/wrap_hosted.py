# -*- coding: utf-8 -*-
"""Wall-hosted AFSC study wrapper; keeps the proven native opening mechanism."""
import os,io,json,math,traceback
from pyrevit import DB
from System.Collections.Generic import List

def build(application,active,rig_report,source,template,output,builder):
    if os.path.exists(output):raise ValueError('Use a fresh output directory')
    os.makedirs(output);f=None;p=None;child=None;tx=None
    b=builder;MM=b.MM;point=b.point;width,height=source['frameSizeMm'];half=width/2
    report={'status':'running','activeBefore':b.snapshot(active),'fixedSizeSnapshot':True,'manufacturerMechanismVerified':False,'maximumOpeningVerified':False,'headCornerCheckResolved':False,'nativeRightHandControlVerified':False,'sourceRig':rig_report['files']['family'],'familyChecks':[],'placementChecks':[]}
    def write(stage=None):
        if stage:report['stage']=stage
        with io.open(os.path.join(output,'proof.json'),'w',encoding='utf-8') as stream:stream.write(json.dumps(report,indent=2))
    def matches(actual,expected):
        return len(actual)==len(expected) and all(abs(a-z)<max(.15,abs(z)*1e-6) for rr,ss in zip(actual,expected) for a,z in zip(rr,ss))
    try:
        write('read-source-angle-geometry')
        child=application.OpenDocumentFile(rig_report['files']['family'])
        tx=DB.Transaction(child,'Read isolated angle baselines');tx.Start();handler=b.fail_closed(tx,report)
        cm=child.FamilyManager;ca=next(q for q in cm.Parameters if q.Definition.Name=='Opening Angle');baselines={}
        for degrees in [0,15,45,90]:
            cm.Set(ca,math.radians(degrees));child.Regenerate()
            baselines[degrees]=sorted(b.signature(child.GetElement(rig_report['sashUid']))+b.signature(child.GetElement(rig_report['frameUid'])))
            if len(baselines[degrees])!=29:raise ValueError('Source rig lacks 29 native solids')
        tx.RollBack();tx=None
        f=application.NewFamilyDocument(template);loaded=child.LoadFamily(f);child.Close(False);child=None
        symbol=f.GetElement(list(loaded.GetFamilySymbolIds())[0])
        write('create-wall-opening-and-controls')
        tx=DB.Transaction(f,'LITHIC hosted opening and setback');tx.Start();handler=b.fail_closed(tx,report)
        if str(f.OwnerFamily.FamilyPlacementType)!='OneLevelBasedHosted':raise ValueError('A wall-hosted family template is required')
        fm=f.FamilyManager
        if fm.CurrentType is None:fm.NewType('AFSC 880x1180 hosted opening study')
        for bip,value in [(DB.BuiltInParameter.FAMILY_WIDTH_PARAM,width),(DB.BuiltInParameter.FAMILY_HEIGHT_PARAM,height)]:fm.SetFormula(fm.get_Parameter(bip),str(value)+' mm')
        sill=next(q for q in fm.Parameters if q.Definition.Name=='Default Sill Height');z=fm.CurrentType.AsDouble(sill)/MM
        host=next(e for e in DB.FilteredElementCollector(f).OfClass(DB.Wall))
        if host.Orientation.Y<0:raise ValueError('Expected inspected +Y exterior template')
        symbol.Activate();inst=f.FamilyCreate.NewFamilyInstance(point(0,0,z),symbol,DB.Structure.StructuralType.NonStructural);f.Regenerate()
        angle=fm.AddParameter('Opening Angle',DB.GroupTypeId.Constraints,DB.SpecTypeId.Angle,True)
        fm.SetDescription(angle,'Outward opening study about the source-observed hinge axis; tested 0 to 90 degrees, manufacturer maximum and mechanism unverified.')
        fm.Set(angle,0.0);fm.AssociateElementParameterToFamilyParameter(inst.LookupParameter('Opening Angle'),angle)
        linked=fm.GetAssociatedFamilyParameter(inst.LookupParameter('Opening Angle'))
        report['angleAssociationPassed']=linked is not None and linked.Id==angle.Id
        if not report['angleAssociationPassed']:raise ValueError('Opening Angle was not associated')
        for opening in list(DB.FilteredElementCollector(f).OfClass(DB.Opening)):f.Delete(opening.Id)
        opening=f.FamilyCreate.NewOpening(host,b.curves([point(-half,0,z),point(half,0,z),point(half,0,z+height),point(-half,0,z+height)]))
        report['nativeOpeningUniqueId']=opening.UniqueId
        view=next(v for v in DB.FilteredElementCollector(f).OfClass(DB.ViewPlan) if not v.IsTemplate)
        refs=DB.ReferenceArray();refs.Append(DB.HostObjectUtils.GetSideFaces(host,DB.ShellLayerType.Exterior)[0])
        nested_refs=inst.GetReferences(DB.FamilyInstanceReferenceType.CenterFrontBack)
        if not nested_refs.Count:raise ValueError('Nested mechanism lacks front/back datum')
        refs.Append(nested_refs[0])
        dim=f.FamilyCreate.NewDimension(view,DB.Line.CreateBound(point(-half-150,-500,0),point(-half-150,500,0)),refs)
        setback=fm.AddParameter('Window Setback',DB.GroupTypeId.Geometry,DB.SpecTypeId.Length,True)
        fm.SetDescription(setback,'Distance inward from the exterior host wall face to the front timber frame datum; aluminium projection excluded. Fixed-size placement control.')
        dim.FamilyLabel=setback
        for offset in [0,50,100]:
            fm.Set(setback,offset*MM)
            for degrees in [0,15,45,90]:
                fm.Set(angle,math.radians(degrees));f.Regenerate();front=host.Width/2/MM-offset
                actual=b.signature(inst,DB.Transform.CreateTranslation(point(0,-front,-z)))
                passed=matches(actual,baselines[degrees]) and abs(inst.Location.Point.Y/MM-front)<.1
                report['familyChecks'].append({'setbackMm':offset,'degrees':degrees,'solids':len(actual),'passed':passed})
                if not passed:raise ValueError('Hosted family changed mechanism geometry')
        fm.Set(setback,50*MM);fm.Set(angle,0.0);f.Regenerate()
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Hosted family transaction rolled back')
        tx=None;report['familyWarnings']=[w.GetDescriptionText() for w in f.GetWarnings()]
        uid=inst.UniqueId;expected=b.signature(inst)
        family=os.path.join(output,'LITHIC-AFSC-880x1180-HOSTED-OPENING-STUDY.rfa');f.SaveAs(family,DB.SaveAsOptions());f.Close(False);f=None
        write('reopen-hosted-family-and-place-in-wall')
        f=application.OpenDocumentFile(family);report['familyPersistencePassed']=matches(b.signature(f.GetElement(uid)),expected)
        report['familyPlacementType']=str(f.OwnerFamily.FamilyPlacementType)
        report['nativeOpeningCount']=DB.FilteredElementCollector(f).OfClass(DB.Opening).GetElementCount()
        p=application.NewProjectDocument(DB.UnitSystem.Metric);loaded=f.LoadFamily(p);sym=p.GetElement(list(loaded.GetFamilySymbolIds())[0])
        tx=DB.Transaction(p,'LITHIC isolated hosted opening proof');tx.Start();handler=b.fail_closed(tx,report);sym.Activate();level=DB.Level.Create(p,0)
        wt=next(t for t in DB.FilteredElementCollector(p).OfClass(DB.WallType) if t.Kind==DB.WallKind.Basic and t.Width>0)
        wall=DB.Wall.Create(p,DB.Line.CreateBound(point(-2000,0,0),point(5000,0,0)),wt.Id,level.Id,3000*MM,0,False,False)
        placed=p.Create.NewFamilyInstance(point(0,0,900),sym,wall,level,DB.Structure.StructuralType.NonStructural);p.Regenerate()
        if placed.FacingOrientation.DotProduct(wall.Orientation)<0:placed.flipFacing();p.Regenerate()
        report['hostPassed']=placed.Host is not None and placed.Host.Id==wall.Id
        report['outsideFacingPassed']=placed.FacingOrientation.DotProduct(wall.Orientation)>.999
        sp=placed.LookupParameter('Window Setback');ap=placed.LookupParameter('Opening Angle');types={}
        for thickness in [100,200,300,500]:
            test_type=wt.Duplicate('LITHIC opening proof '+str(thickness)+' mm');layers=List[DB.CompoundStructureLayer]();layers.Add(DB.CompoundStructureLayer(thickness*MM,DB.MaterialFunctionAssignment.Structure,DB.ElementId.InvalidElementId));test_type.SetCompoundStructure(DB.CompoundStructure.CreateSimpleCompoundStructure(layers));types[thickness]=test_type
            wall.ChangeTypeId(test_type.Id);p.Regenerate()
            for offset in [0,50,100]:
                sp.Set(offset*MM)
                for degrees in [0,15,45,90]:
                    ap.Set(math.radians(degrees));p.Regenerate();tr=placed.GetTransform()
                    normalize=DB.Transform.CreateTranslation(point(0,-(thickness/2-offset),-z)).Multiply(tr.Inverse)
                    actual=b.signature(placed,normalize);rigid=matches(actual,baselines[degrees])
                    remaining=sum(s.Volume for s in b.solids(wall))/MM**3;expected_wall=(7000*3000-width*height)*thickness
                    cut=abs(remaining-expected_wall)<max(1,expected_wall*1e-6)
                    physical=tr.OfPoint(point(0,0,z)).Z/MM;reported=placed.get_Parameter(DB.BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM).AsDouble()/MM+level.Elevation/MM
                    row={'wallMm':thickness,'setbackMm':offset,'degrees':degrees,'hostPassed':placed.Host.Id==wall.Id,'geometryPassed':rigid,'openingPassed':cut,'removedWallMm3':7000*3000*thickness-remaining,'expectedRemovedWallMm3':width*height*thickness,'sillPassed':abs(physical-reported)<.1,'passed':rigid and cut and abs(physical-reported)<.1}
                    report['placementChecks'].append(row)
                    if not row['passed']:raise ValueError('Native hosted placement matrix failed')
        wall.ChangeTypeId(types[300].Id);sp.Set(50*MM);ap.Set(math.radians(45));p.Regenerate()
        instances=[(placed,45,0)]
        for degrees,x in [(0,1600),(90,3200)]:
            other=p.Create.NewFamilyInstance(point(x,0,900),sym,wall,level,DB.Structure.StructuralType.NonStructural);p.Regenerate()
            if other.FacingOrientation.DotProduct(wall.Orientation)<0:other.flipFacing();p.Regenerate()
            other.LookupParameter('Opening Angle').Set(math.radians(degrees));other.LookupParameter('Window Setback').Set(50*MM);instances.append((other,degrees,x))
        p.Regenerate();rvol=sum(s.Volume for s in b.solids(wall))/MM**3
        report['threeOpeningVolumePassed']=abs(rvol-(7000*3000-3*width*height)*300)<max(1,rvol*1e-6)
        vtype=next(t for t in DB.FilteredElementCollector(p).OfClass(DB.ViewFamilyType) if t.ViewFamily==DB.ViewFamily.ThreeDimensional)
        for item,degrees,x in instances:
            v=DB.View3D.CreateIsometric(p,vtype.Id);v.Name='AFSC hosted - '+str(degrees)+' degrees';v.DetailLevel=DB.ViewDetailLevel.Fine;v.DisplayStyle=DB.DisplayStyle.ShadingWithEdges
            target=point(x,0,1500);eye=target+DB.XYZ(3,4,2);forward=(target-eye).Normalize();right=forward.CrossProduct(DB.XYZ.BasisZ).Normalize();up=right.CrossProduct(forward).Normalize();v.SetOrientation(DB.ViewOrientation3D(eye,up,forward))
            box=DB.BoundingBoxXYZ();box.Min=point(x-650,-500,700);box.Max=point(x+650,1100,2250);v.SetSectionBox(box);v.IsSectionBoxActive=True;v.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Levels),True)
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Hosted project transaction rolled back')
        tx=None;report['projectWarnings']=[w.GetDescriptionText() for w in p.GetWarnings()]
        persisted=[{'uid':item.UniqueId,'degrees':degrees,'signature':b.signature(item),'host':wall.UniqueId} for item,degrees,x in instances]
        project=os.path.join(output,'LITHIC-AFSC-HOSTED-OPENING-REVIEW.rvt');p.SaveAs(project,DB.SaveAsOptions());p.Close(False);p=None
        write('reopen-project-and-verify-host-cut');p=application.OpenDocumentFile(project);report['projectPersistenceChecks']=[]
        for row in persisted:
            item=p.GetElement(row['uid']);passed=matches(b.signature(item),row['signature']) and item.Host.UniqueId==row['host'] and abs(math.degrees(item.LookupParameter('Opening Angle').AsDouble())-row['degrees'])<1e-6
            report['projectPersistenceChecks'].append({'degrees':row['degrees'],'passed':passed})
        saved_wall=p.GetElement(persisted[0]['host']);remaining=sum(s.Volume for s in b.solids(saved_wall))/MM**3;report['reopenedWallCutPassed']=abs(remaining-(7000*3000-3*width*height)*300)<max(1,remaining*1e-6)
        report['files']={'family':family,'project':project};report['nativeSillDatumMm']=z
        passed=report['hostPassed'] and report['outsideFacingPassed'] and report['familyPersistencePassed'] and report['nativeOpeningCount']==1 and report['threeOpeningVolumePassed'] and report['reopenedWallCutPassed'] and all(c['passed'] for c in report['projectPersistenceChecks']) and not report['familyWarnings'] and not report['projectWarnings']
        report['status']='hosted-opening-cut-verified-review-required' if passed else 'technical-checks-failed'
    except Exception as error:report.update({'status':'failed','error':str(error),'traceback':traceback.format_exc()})
    finally:
        if tx and tx.GetStatus()==DB.TransactionStatus.Started:tx.RollBack()
        for own in [p,f,child]:
            if own is not None and own.IsValidObject:own.Close(False)
        report['activeAfter']=b.snapshot(active);report['activeProjectPreserved']=report['activeBefore']==report['activeAfter'];write()
    return report
