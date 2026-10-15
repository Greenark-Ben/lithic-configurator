# -*- coding: utf-8 -*-
"""Isolated AFSC mechanism study. Native reference-line control, sweeps and cuts.

Input component reports must be from build_closed(..., assembly_only=True),
with openingStudyGeometryGroup selecting each component. Does not author a
wall-hosted production family. A native angle success does not approve frame
corner geometry or the manufacturer's hinge mechanism.
"""
import os,io,json,math,traceback
from pyrevit import DB
from System.Collections.Generic import List

def build(application,active,component_base,hinge_path,template,output,builder):
    if os.path.exists(output):raise ValueError('A fresh output directory is required')
    b=builder;doc=active;base=component_base;out=output;os.makedirs(out)
    with io.open(os.path.join(base,'sash/proof.json'),encoding='utf-8') as stream:sr=json.load(stream)
    with io.open(os.path.join(base,'frame/proof.json'),encoding='utf-8') as stream:fr=json.load(stream)
    with io.open(hinge_path,encoding='utf-8') as stream:hinge=json.load(stream)
    r={'status':'running','activeBefore':b.snapshot(doc),'samples':[],'manufacturerMechanismVerified':False,'maximumOpeningVerified':False,'widthHeightFlex':False,'frameInputStatus':fr['status'],'frameAnalyticVolumeChecks':fr['analyticVolumeChecks']}
    f=None;child=None;p=None;state={'tx':None}
    axis=b.point(440-hinge['candidateAxisRelativeToFrameLeftFrontMm'][0],-hinge['candidateAxisRelativeToFrameLeftFrontMm'][1],0)
    def write(stage=None):
     if stage:r['stage']=stage
     with io.open(os.path.join(out,'proof.json'),'w',encoding='utf-8') as stream:stream.write(json.dumps(r,indent=2))
    def commit():
     result=state['tx'].Commit();state['tx']=None
     if result!=DB.TransactionStatus.Committed:raise ValueError('Native transaction rolled back; inspect transactionFailures')
    def start(d,label):
     state['tx']=DB.Transaction(d,label);state['tx'].Start();state['handler']=b.fail_closed(state['tx'],r)
    def transform_rows(t):return [[getattr(v,a) for a in ['X','Y','Z']] for v in [t.Origin,t.BasisX,t.BasisY,t.BasisZ]]
    try:
     if sr['status']!='assembly-created-review-required':raise ValueError('Moving sash must pass its source geometry checks')
     write('prepare-native-workplane-sash')
     child=doc.Application.OpenDocumentFile(sr['files']['family']);start(child,'Prepare native sash reference-line attachment')
     ids=List[DB.ElementId]();[ids.Add(e.Id) for e in DB.FilteredElementCollector(child).OfClass(DB.GenericForm)]
     DB.ElementTransformUtils.MoveElements(child,ids,-axis)
     DB.ElementTransformUtils.RotateElements(child,ids,DB.Line.CreateBound(DB.XYZ.Zero,DB.XYZ.BasisX),-math.pi/2)
     child.OwnerFamily.get_Parameter(DB.BuiltInParameter.FAMILY_WORK_PLANE_BASED).Set(1)
     child.OwnerFamily.get_Parameter(DB.BuiltInParameter.FAMILY_ALWAYS_VERTICAL).Set(0)
     child.Regenerate();commit()
     r['sashPlacementType']=str(child.OwnerFamily.FamilyPlacementType)
     sash_path=os.path.join(out,'LITHIC-AFSC-NATIVE-MOVING-SASH.rfa');child.SaveAs(sash_path,DB.SaveAsOptions());child.Close(False);child=None
     f=doc.Application.NewFamilyDocument(template)
     child=doc.Application.OpenDocumentFile(sash_path);loaded=child.LoadFamily(f);child.Close(False);child=None
     sash_symbol=f.GetElement(list(loaded.GetFamilySymbolIds())[0])
     child=doc.Application.OpenDocumentFile(fr['files']['family']);loaded=child.LoadFamily(f);child.Close(False);child=None
     frame_symbol=f.GetElement(list(loaded.GetFamilySymbolIds())[0])
     write('create-native-reference-line-control');start(f,'LITHIC native rotating sash study')
     f.OwnerFamily.FamilyCategory=f.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Windows)
     view=next(v for v in DB.FilteredElementCollector(f).OfClass(DB.ViewPlan) if not v.IsTemplate)
     fm=f.FamilyManager;fm.NewType('AFSC 880x1180 opening study')
     a=math.pi/6;sp=DB.SketchPlane.Create(f,DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisZ,DB.XYZ.Zero))
     direction=DB.XYZ(math.cos(a),-math.sin(a),0)
     line=f.FamilyCreate.NewModelCurve(DB.Line.CreateBound(axis,axis+direction),sp);line.ChangeToReferenceLine();f.Regenerate()
     def plane_x(x):return f.FamilyCreate.NewReferencePlane(DB.XYZ(x,-3,0),DB.XYZ(x,3,0),DB.XYZ.BasisZ,view)
     def plane_y(y):return f.FamilyCreate.NewReferencePlane(DB.XYZ(-3,y,0),DB.XYZ(3,y,0),DB.XYZ.BasisZ,view)
     px=plane_x(axis.X);py=plane_y(axis.Y);px.Pinned=True;py.Pinned=True
     bx=plane_x(axis.X-2);by=plane_y(axis.Y-2);bx.Pinned=True;by.Pinned=True
     ex=plane_x(axis.X+direction.X);ey=plane_y(axis.Y+direction.Y);f.Regenerate()
     for ref in [px.GetReference(),py.GetReference()]:f.FamilyCreate.NewAlignment(view,ref,line.GeometryCurve.GetEndPointReference(0))
     for ref in [ex.GetReference(),ey.GetReference()]:f.FamilyCreate.NewAlignment(view,ref,line.GeometryCurve.GetEndPointReference(1))
     param=fm.AddParameter('Opening Angle',DB.GroupTypeId.Constraints,DB.SpecTypeId.Angle,True);fm.Set(param,a)
     fm.SetDescription(param,'Diagnostic outward opening about a source-observed hinge-axis candidate. Manufacturer mechanism and maximum travel unverified; frame size fixed.')
     length=fm.AddParameter('Opening Rig Length',DB.GroupTypeId.Constraints,DB.SpecTypeId.Length,False);fm.SetFormula(length,'304.8 mm')
     for name,p1,p2,startpt,endpt,value,formula in [
      ('Opening Rig X',bx,ex,DB.XYZ(axis.X-2,-2,0),DB.XYZ(axis.X+direction.X,-2,0),2+direction.X,'Opening Rig Length * (2 + cos(Opening Angle))'),
      ('Opening Rig Y',by,ey,DB.XYZ(-2,axis.Y-2,0),DB.XYZ(-2,axis.Y+direction.Y,0),2+direction.Y,'Opening Rig Length * (2 - sin(Opening Angle))')]:
      refs=DB.ReferenceArray();refs.Append(p1.GetReference());refs.Append(p2.GetReference())
      d=f.FamilyCreate.NewLinearDimension(view,DB.Line.CreateBound(startpt,endpt),refs)
      fp=fm.AddParameter(name,DB.GroupTypeId.Constraints,DB.SpecTypeId.Length,True);fm.Set(fp,value);d.FamilyLabel=fp;fm.SetFormula(fp,formula)
     f.Regenerate();sash_symbol.Activate();frame_symbol.Activate()
     ref=DB.Reference.ParseFromStableRepresentation(f,line.UniqueId+':1:7:SURFACE')
     sash=f.FamilyCreate.NewFamilyInstance(ref,axis,direction,sash_symbol)
     fixed=f.FamilyCreate.NewFamilyInstance(DB.XYZ.Zero,frame_symbol,DB.Structure.StructuralType.NonStructural)
     f.Regenerate();r['initialSashTransform']=transform_rows(sash.GetTransform());commit()
     original=sorted(row for rows in sr['familySignatures'].values() for row in rows)
     def check(deg):
      fm.Set(param,math.radians(deg));f.Regenerate()
      rotation=DB.Transform.CreateRotationAtPoint(DB.XYZ.BasisZ,-math.radians(deg),axis)
      actual=b.signature(sash,rotation.Inverse)
      rigid=len(actual)==len(original) and all(abs(v-w)<max(.15,abs(w)*1e-6) for rr,ss in zip(actual,original) for v,w in zip(rr,ss))
      line_dir=line.GeometryCurve.Direction
      return {'requestedDegrees':deg,'actualLineDegrees':-math.degrees(math.atan2(line_dir.Y,line_dir.X)),'rigidGeometryPassed':rigid,'solidCount':len(actual),'transform':transform_rows(sash.GetTransform()),'actualNeutralSignatures':actual if not rigid else None}
     for deg in [30,0,15,45,90,0]:
      write('flex-native-sash-'+str(deg));start(f,'Flex complete native sash '+str(deg));row=check(deg);commit();r['samples'].append(row);write()
      if not row['rigidGeometryPassed']:raise ValueError('Moving sash did not follow native reference line rigidly')
     r['warnings']=[w.GetDescriptionText() for w in f.GetWarnings()]
     r['nativeOpeningParameterVerified']=True
     r['nativeRightHandControlVerified']=False
     r['continuousTravelVerified']=False
     r['status']='native-opening-rig-passed-frame-review-required'
     family=os.path.join(out,'LITHIC-AFSC-880x1180-NATIVE-OPENING-STUDY.rfa');f.SaveAs(family,DB.SaveAsOptions())
     r['files']={'family':family,'movingSash':sash_path};r['sashUid']=sash.UniqueId;r['frameUid']=fixed.UniqueId
    except Exception as e:r.update({'status':'failed','error':str(e),'traceback':traceback.format_exc()})
    finally:
     if state['tx'] and state['tx'].GetStatus()==DB.TransactionStatus.Started:state['tx'].RollBack()
     for own in [child,p,f]:
      if own and own.IsValidObject:own.Close(False)
     r['activeAfter']=b.snapshot(doc);r['activeProjectPreserved']=r['activeBefore']==r['activeAfter'];write()
    return r
