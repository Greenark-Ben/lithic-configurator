# -*- coding: utf-8 -*-
"""Read-only native-solid motion screening, not an opening Revit family."""
from __future__ import division
import os,io,json,math,hashlib,traceback
from pyrevit import DB
from System.Collections.Generic import List

def run(active,accepted_report_path,hinge_path,output,builder):
    if os.path.exists(output):raise ValueError('A fresh proof directory is required')
    os.makedirs(output);f=None
    with io.open(accepted_report_path,encoding='utf-8') as stream:accepted=json.load(stream)
    with io.open(hinge_path,encoding='utf-8') as stream:hinge=json.load(stream)
    report={'status':'running','activeBefore':builder.snapshot(active),'acceptedClosedCommit':'433fc0b','hingeReference':hinge,'manufacturerMechanismVerified':False,'maximumOpeningVerified':False,'nativeOpeningParameterVerified':False,'continuousTravelVerified':False,'intersectionReportingThresholdMm3':1,'analysisOnly':True,'cases':[]}
    report['inputGeometryVariant']=accepted['source'].get('geometryVariant','Accepted closed-study geometry')
    MM=builder.MM;point=builder.point
    def write(stage):
        report['stage']=stage
        with io.open(os.path.join(output,'motion-screen.json'),'w',encoding='utf-8') as stream:stream.write(json.dumps(report,indent=2))
    def bounds(solid):
        box=solid.GetBoundingBox();points=[box.Transform.OfPoint(DB.XYZ(x,y,z)) for x in [box.Min.X,box.Max.X] for y in [box.Min.Y,box.Max.Y] for z in [box.Min.Z,box.Max.Z]]
        return [(min(getattr(p,a) for p in points),max(getattr(p,a) for p in points)) for a in ['X','Y','Z']]
    def disjoint(a,b):return any(x[1]<y[0]-1e-8 or y[1]<x[0]-1e-8 for x,y in zip(a,b))
    def intersections(moving,fixed):
        hits=[];errors=[];checks=0
        for mn,ms in moving:
            mb=bounds(ms)
            for fn,fs in fixed:
                if disjoint(mb,bounds(fs)):continue
                checks+=1
                try:
                    overlap=DB.BooleanOperationsUtils.ExecuteBooleanOperation(ms,fs,DB.BooleanOperationsType.Intersect)
                    volume=overlap.Volume/MM**3
                    if volume>1:hits.append({'moving':mn,'fixed':fn,'overlapMm3':round(volume,3)})
                except Exception as error:errors.append({'moving':mn,'fixed':fn,'error':str(error)})
        return {'hits':hits,'errors':errors,'testedPairs':checks,'status':'inconclusive' if errors else 'intersections-found' if hits else 'no-intersection-at-sampled-position'}
    def wall(thickness,width,height):
        loops=List[DB.CurveLoop]()
        for coords in [[(-2200,-900),(2200,-900),(2200,height+900),(-2200,height+900)],[(-width/2,0),(-width/2,height),(width/2,height),(width/2,0)]]:
            loop=DB.CurveLoop()
            pts=[point(x,0,z) for x,z in coords]
            for a,b in zip(pts,pts[1:]+pts[:1]):loop.Append(DB.Line.CreateBound(a,b))
            loops.Add(loop)
        return DB.GeometryCreationUtilities.CreateExtrusionGeometry(loops,-DB.XYZ.BasisY,thickness*MM)
    write('open-accepted-native-assembly')
    try:
        family=accepted['files']['family']
        if os.path.normcase(active.PathName)==os.path.normcase(family):raise ValueError('Do not use an active assembly document')
        with open(family,'rb') as stream:report['acceptedFamilySha256']=hashlib.sha256(stream.read()).hexdigest()
        f=active.Application.OpenDocumentFile(family)
        source=[]
        for name,uid in accepted['partUniqueIds'].items():
            element=f.GetElement(uid)
            for solid in builder.solids(element):source.append((name,accepted['groups'][name],solid))
        report['componentCount']=len(source)
        report['movingComponentCount']=sum(group=='Moving Sash' for name,group,solid in source)
        report['fixedComponentCount']=sum(group=='Fixed Frame' for name,group,solid in source)
        width,height=accepted['source']['frameSizeMm']
        u,depth=hinge['candidateAxisRelativeToFrameLeftFrontMm'];axis=point(width/2-u,-depth,0)
        report['leftAxisMm']=[axis.X/MM,axis.Y/MM,0]
        reflection=DB.Transform.CreateReflection(DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisX,DB.XYZ.Zero))
        report['sampledAnglesDegrees']=[0,.25,.5,1,2,5,10,15,30,45,60,90]
        report['wallAssumptions']={'thicknessMm':300,'setbacksMm':[0,50,100],'openingMm':[width,height],'facadeYmm':0,'installationAllowanceMm':0,'hardwareAndSealsBetweenFrameAndSashOmitted':True}
        wall_solid=wall(300,width,height)
        for hand in ['outside-left','outside-right-mirrored-prototype']:
            write('prepare-'+hand)
            try:
                parts=[(name,group,DB.SolidUtils.CreateTransformed(solid,reflection) if hand!='outside-left' else solid) for name,group,solid in source]
            except Exception as error:
                report.setdefault('handPreparationErrors',[]).append({'hand':hand,'error':str(error)});continue
            pivot=axis if hand=='outside-left' else reflection.OfPoint(axis)
            fixed=[(name,solid) for name,group,solid in parts if group=='Fixed Frame']
            sash=[(name,solid) for name,group,solid in parts if group=='Moving Sash']
            for angle in report['sampledAnglesDegrees']:
                rotation=DB.Transform.CreateRotationAtPoint(DB.XYZ.BasisZ,(-1 if hand=='outside-left' else 1)*math.radians(angle),pivot)
                moved=[(name,DB.SolidUtils.CreateTransformed(solid,rotation)) for name,solid in sash]
                rigid=all(abs(a.Volume-b.Volume)<=max(1e-10,abs(a.Volume)*1e-8) for (an,a),(bn,b) in zip(sash,moved))
                row={'hand':hand,'angleDegrees':angle,'rigidVolumePassed':rigid,'frame':intersections(moved,fixed),'walls':[]}
                for setback in report['wallAssumptions']['setbacksMm']:
                    shift=DB.Transform.CreateTranslation(point(0,-setback,0))
                    positioned=[(name,DB.SolidUtils.CreateTransformed(solid,shift)) for name,solid in moved]
                    result=intersections(positioned,[('300 mm host with nominal frame opening',wall_solid)])
                    result['setbackMm']=setback;row['walls'].append(result)
                report['cases'].append(row);write(hand+'-'+str(angle)+'-degrees')
        report['status']='sampled-motion-screen-complete-review-required'
        report['warnings']=[w.GetDescriptionText() for w in f.GetWarnings()]
    except:report['status']='failed';report['traceback']=traceback.format_exc()
    finally:
        if f is not None and f.IsValidObject:f.Close(False)
        report['activeAfter']=builder.snapshot(active);report['activeProjectPreserved']=report['activeBefore']==report['activeAfter'];write('complete')
    return report
