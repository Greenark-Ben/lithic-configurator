# -*- coding: utf-8 -*-
"""Isolated AFSC closed geometry study, not a production/export builder.

Run through the desktop bridge with explicit source/template/output paths.
Never modifies the active document. Source-specific profiles remain separate.
"""
from __future__ import division
import os,io,json,hashlib,traceback,imp
from pyrevit import DB
from System.Collections.Generic import List

MM=1/304.8

class FailClosed(DB.IFailuresPreprocessor):
    """Keep diagnostic messages; roll back instead of dismissing warnings."""
    def __init__(self,report):self.report=report
    def PreprocessFailures(self,accessor):
        messages=list(accessor.GetFailureMessages())
        if not messages:return DB.FailureProcessingResult.Continue
        rows=[]
        for message in messages:
            items=[]
            for eid in message.GetFailingElementIds():
                row={'id':eid.IntegerValue}
                try:
                    e=accessor.GetDocument().GetElement(eid);row['type']=e.GetType().Name
                    if isinstance(e,DB.CurveElement):row['endpointsMm']=[[getattr(e.GeometryCurve.GetEndPoint(i),axis)/MM for axis in ['X','Y','Z']] for i in [0,1]]
                    if isinstance(e,DB.GenericForm) and e.Subcategory:row['subcategory']=e.Subcategory.Name
                except Exception:pass
                items.append(row)
            rows.append({'description':message.GetDescriptionText(),'severity':str(message.GetSeverity()),'elements':items})
        self.report.setdefault('transactionFailures',[]).extend(rows)
        return DB.FailureProcessingResult.ProceedWithRollBack

def fail_closed(transaction,report):
    handler=FailClosed(report);options=transaction.GetFailureHandlingOptions();options.SetFailuresPreprocessor(handler);options.SetClearAfterRollback(True);transaction.SetFailureHandlingOptions(options)
    return handler
def point(x,y,z):return DB.XYZ(x*MM,y*MM,z*MM)
def curves(points):
    result=DB.CurveArray()
    for a,b in zip(points,points[1:]+points[:1]):result.Append(DB.Line.CreateBound(a,b))
    return result
def solids(element):
    result=[]
    def collect(geometry):
        for g in geometry:
            if isinstance(g,DB.Solid) and g.Volume>1e-10:result.append(g)
            elif isinstance(g,DB.GeometryInstance):collect(g.GetInstanceGeometry())
    collect(element.get_Geometry(DB.Options()));return result
def signature(element,inverse=None):
    inverse=inverse or DB.Transform.Identity
    result=[]
    for solid in solids(element):
        pts=[inverse.OfPoint(edge.AsCurve().GetEndPoint(i)) for edge in solid.Edges for i in [0,1]]
        result.append([round(v,3) for v in [solid.Volume/MM**3]+[f(getattr(p,axis)/MM for p in pts) for axis in ['X','Y','Z'] for f in [min,max]]])
    return sorted(result)
def snapshot(active):
    return {'title':active.Title,'path':active.PathName,'modified':active.IsModified,'elements':DB.FilteredElementCollector(active).GetElementCount()}

def area_moment(points):
    cross=[a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])]
    signed=sum(cross)/2;direction=1 if signed>0 else -1
    moment=direction*sum((a[0]+b[0])*c for a,b,c in zip(points,points[1:]+points[:1],cross))/6
    return abs(signed),moment

def positive_moment(points):
    clipped=[]
    for a,b in zip(points,points[1:]+points[:1]):
        if a[0]>=0:clipped.append(a)
        if (a[0]<0)!=(b[0]<0):
            t=-a[0]/(b[0]-a[0]);clipped.append([0,a[1]+t*(b[1]-a[1])])
    return area_moment(clipped)[1] if len(clipped)>2 else 0

def build(application,active,source_path,template,output,helpers,assembly_only=False):
    if os.path.exists(output):raise ValueError('Use a new output directory, preserving previous proofs.')
    os.makedirs(output)
    with io.open(source_path,encoding='utf-8') as stream:source=json.load(stream)
    before=snapshot(active);f=None;p=None;tx=None
    report={'status':'running','activeBefore':before,'source':source,'nativeParameterFlex':False,'manufacturerApproved':False,'openingMovementVerified':False,'visualAcceptance':'pending'}
    def write():
        with io.open(os.path.join(output,'proof.json'),'w',encoding='utf-8') as stream:stream.write(json.dumps(report,indent=2))
    def checkpoint(stage):report['stage']=stage;write()
    write()
    try:
        checkpoint('create-empty-family');f=application.NewFamilyDocument(template)
        if not assembly_only and f.OwnerFamily.FamilyCategory.Id!=DB.ElementId(DB.BuiltInCategory.OST_Windows):raise ValueError('Window category required')
        hosts=list(DB.FilteredElementCollector(f).OfClass(DB.Wall))
        if len(hosts)!=(0 if assembly_only else 1) or DB.FilteredElementCollector(f).OfClass(DB.GenericForm).GetElementCount():raise ValueError('Empty template required')
        host=None if assembly_only else hosts[0];exterior=1 if assembly_only or host.Orientation.Y>0 else -1
        width,height=source['frameSizeMm'];half=width/2;manager=f.FamilyManager
        selected_group=source.get('openingStudyGeometryGroup')
        if selected_group and (not assembly_only or selected_group not in ['Fixed Frame','Moving Sash']):raise ValueError('Group selection is limited to isolated opening-study assemblies')
        tx=DB.Transaction(f,'LITHIC Side-Hung Outward closed geometry study');tx.Start();failure_handler=fail_closed(tx,report)
        if assembly_only:f.OwnerFamily.FamilyCategory=f.Settings.Categories.get_Item(DB.BuiltInCategory.OST_Windows)
        if manager.CurrentType is None:manager.NewType('LITHIC Side-Hung Outward 880x1180 component')
        sill_parameter=next((p for p in manager.Parameters if p.Definition.Name=='Default Sill Height'),None)
        if sill_parameter is None and not assembly_only:raise ValueError('Template lacks its Default Sill Height datum')
        sill_datum=0 if assembly_only else manager.CurrentType.AsDouble(sill_parameter)/MM
        report['nativeSillDatumMm']=sill_datum
        def family_point(x,depth,z):return point(x,-depth*exterior,z+sill_datum)
        shared=helpers.shared_parameters(f,source)
        if assembly_only:
            for fp in shared.values():manager.MakeInstance(fp)
        for name,value in [('Width',width),('Height',height)]:
            fp=manager.get_Parameter({'Width':DB.BuiltInParameter.FAMILY_WIDTH_PARAM,'Height':DB.BuiltInParameter.FAMILY_HEIGHT_PARAM}[name])
            if fp is None:fp=manager.AddParameter(name,DB.GroupTypeId.Geometry,DB.SpecTypeId.Length,False)
            manager.SetFormula(fp,str(value)+' mm')
        for name,value in [('LITHIC Builder','lithic-afsc-closed-study/0.1'),('LITHIC Source Drawing',source['drawing']),('LITHIC Geometry Mode','fixed-size-snapshot'),('LITHIC Evidence Status','UNAPPROVED_CLOSED_GEOMETRY_STUDY'),('LITHIC Request SHA256',hashlib.sha256(json.dumps(source,sort_keys=True).encode('utf-8')).hexdigest())]:manager.Set(shared[name],value)
        params={'timber':'Timber Material','aluminium':'Aluminium Material','glazing':'Glazing Material','spacer':'Glazing Spacer Material','seal':'Glazing Seal Material'}
        for role,color in [('timber',(206,170,126)),('aluminium',(61,66,64)),('glazing',(174,205,209)),('spacer',(70,73,69)),('seal',(28,30,28))]:
            label='LITHIC Side-Hung Outward '+('Warm Edge Spacer - composition unresolved' if role=='spacer' else role.title()+' Prototype')
            mid=DB.Material.Create(f,label);material=f.GetElement(mid);material.Color=DB.Color(*color)
            if role=='glazing':material.Transparency=75
            manager.Set(shared[params[role]],mid)
        elements={};all_forms=[];groups={};expected_volumes={};form_roles={}
        def bind(e,name,role,group):
            e.Subcategory=helpers.category(f,'LITHIC Side-Hung Outward '+name)
            manager.AssociateElementParameterToFamilyParameter(e.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM),shared[params[role]])
            vis=e.GetVisibility();vis.IsShownInTopBottom=bool(selected_group) and not source.get('openingPlanSymbols',False);vis.IsShownInPlanRCPCut=vis.IsShownInTopBottom;e.SetVisibility(vis)
            all_forms.append(e);form_roles[e.UniqueId]=role;groups[name]=group;return e
        def extrusion(name,points,normal,length,role,group,holes=None):
            loops=DB.CurveArrArray();loops.Append(curves(points))
            for hole in holes or []:loops.Append(curves(hole))
            plane=DB.SketchPlane.Create(f,DB.Plane.CreateByNormalAndOrigin(normal,points[0]))
            e=f.FamilyCreate.NewExtrusion(True,loops,plane,length*MM);elements[name]=bind(e,name,role,group);return e
        def section_points(profile,side,start):
            result=[]
            for u,d in profile:
                if side=='Left':x,y,z=exterior*(half-u),d,start
                elif side=='Right':x,y,z=-exterior*(half-u),d,start
                elif side=='Head':x,y,z=start,d,height-u
                else:x,y,z=start,d,u
                result.append(family_point(x,y,z))
            return result
        profiles=source.get('nativeProfiles',source['profiles'])
        frame_keys=source.get('frameCladdingProfileKeys',{'Left':'frameHeadClip','Right':'frameHeadClip','Head':'frameHeadClip','Sill':'frameSillCover'})
        corner_math=imp.load_source('afsc_corner_math',os.path.join(os.path.dirname(__file__),'corner_math.py')) if source.get('compoundSashMitres') else None
        for group,prefix in [('Fixed Frame','frame'),('Moving Sash','sash')]:
            if selected_group and selected_group!=group:continue
            checkpoint('timber-'+prefix)
            for side in ['Left','Right','Head','Sill']:
                key=prefix+side
                if side in ['Left','Right']:
                    start,end=(0,height) if prefix=='frame' else (42.5,height-44)
                    pts=section_points(profiles[key]['pointsMm'],side,start);normal=DB.XYZ.BasisZ;length=end-start
                else:
                    inset=52 if prefix=='frame' else 103.5
                    pts=section_points(profiles[key]['pointsMm'],side,-half+inset);normal=DB.XYZ.BasisX;length=width-2*inset
                name=group+' Timber '+side
                expected_volumes[name]=area_moment(profiles[key]['pointsMm'])[0]*length
                extrusion(name,pts,normal,length,'timber',group)
        # Straight native sweeps retain independently editable source sections.
        # Complementary native void cuts share each corner plane; visual review remains required.
        def swept_member(name,key,side,group):
            if selected_group and selected_group!=group:return
            checkpoint('sweep-'+name)
            pts=profiles[key]['pointsMm'];start=0 if side in ['Left','Right'] else -half
            # Keep the entire profile inward of its native sweep path. Revit's
            # cut can consume a thin sweep when its folded return crosses the
            # attachment path. Rebase both perimeter coordinates together.
            offset=max(0,-min(u for u,d in pts));length=(height if side in ['Left','Right'] else width)+2*offset
            local_pts=[[u+offset,d] for u,d in pts]
            expected_volumes[name]=area_moment(local_pts)[0]*length-2*positive_moment(local_pts)
            if corner_math and key.startswith('sashAluminium'):
                if side in ['Left','Right']:
                    specs=[corner_math.corner_spec(profiles,side,horizontal) for horizontal in ['Sill','Head']]
                    expected_volumes[name]=area_moment(pts)[0]*height-sum(corner_math.integral(pts,s) for s in specs)
                else:
                    specs=[corner_math.corner_spec(profiles,jamb,side) for jamb in ['Left','Right']]
                    expected_volumes[name]=area_moment(pts)[0]*width-sum(corner_math.integral(pts,s,True) for s in specs)
            if corner_math and source.get('matchedFrameSillCuts'):
                if key=='frameHeadClip' and side in ['Left','Right']:
                    expected_volumes[name]=area_moment(pts)[0]*height-positive_moment(pts)-corner_math.integral(pts,corner_math.frame_sill_spec())
                elif key=='frameSillCover':
                    expected_volumes[name]=area_moment(pts)[0]*width-2*corner_math.integral(pts,corner_math.frame_sill_spec(),True)
            if corner_math and source.get('sourceSpecificFrameCladding') and key in frame_keys.values():
                if side in ['Left','Right']:
                    expected_volumes[name]=area_moment(pts)[0]*height-sum(corner_math.integral(pts,corner_math.frame_corner_spec(profiles,frame_keys,side,h)) for h in ['Head','Sill'])
                else:
                    expected_volumes[name]=area_moment(pts)[0]*width-sum(corner_math.integral(pts,corner_math.frame_corner_spec(profiles,frame_keys,j,side),True) for j in ['Left','Right'])
            # CurveLoopsProfile uses local XY at the path attachment.
            # +Z path local X is +X; +X path local X is -Z.
            inward=-exterior if side=='Left' else exterior if side=='Right' else 1 if side=='Head' else -1
            vertices=[point(inward*u,-d*exterior,0) for u,d in local_pts]
            normal=DB.XYZ.BasisZ if side in ['Left','Right'] else DB.XYZ.BasisX
            origin=point(exterior*(half+offset) if side=='Left' else -exterior*(half+offset) if side=='Right' else -half-offset,0,sill_datum+(-offset if side!='Head' else height+offset))
            if source.get('sourceSpecificFrameCladding') and side=='Head' and key=='frameHeadClip':
                # Cut through an extended native sweep, away from its end caps.
                # 10 mm stays inside the local cutter's -20 mm outer boundary.
                origin=origin-normal*10*MM;length+=20
            end=origin+normal*length*MM
            loops=DB.CurveArrArray();loops.Append(curves(vertices));profile=application.Create.NewCurveLoopsProfile(loops)
            path=DB.CurveArray();path.Append(DB.Line.CreateBound(origin,end))
            sk=DB.SketchPlane.Create(f,DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisY,origin))
            e=bind(f.FamilyCreate.NewSweep(True,path,sk,profile,0,DB.ProfilePlaneLocation.Start),name,'aluminium',group)
            f.Regenerate()
            report.setdefault('sweepInputChecks',[]).append({'name':name,'signature':signature(e)})
            members=DB.CombinableElementArray();members.Append(e)
            for top in [False,True] if side in ['Left','Right'] else [side=='Head']:
                for sign in [-1,1] if side in ['Head','Sill'] else [exterior if side=='Left' else -exterior]:
                    # u is distance from the outside frame side; v from sill/head.
                    region=[(-100,-100),(200,-100),(200,200)] if side in ['Left','Right'] else [(-100,-100),(-100,200),(200,200)]
                    if corner_math and key.startswith('sashAluminium'):
                        jamb=side if side in ['Left','Right'] else 'Left' if sign==exterior else 'Right'
                        horizontal=('Head' if top else 'Sill') if side in ['Left','Right'] else side
                        spec=corner_math.corner_spec(profiles,jamb,horizontal)
                        region=corner_math.cut_region(spec,side in ['Left','Right'])
                        report.setdefault('compoundMitreCuts',[]).append({'member':name,'corner':jamb+' '+horizontal,'spec':spec})
                    if corner_math and source.get('matchedFrameSillCuts') and ((key=='frameHeadClip' and side in ['Left','Right'] and not top) or key=='frameSillCover'):
                        spec=corner_math.frame_sill_spec();region=corner_math.cut_region(spec,side in ['Left','Right'])
                        report.setdefault('fixedFrameSillCuts',[]).append({'member':name,'spec':spec})
                    if corner_math and source.get('sourceSpecificFrameCladding') and key in frame_keys.values():
                        jamb=side if side in ['Left','Right'] else 'Left' if sign==exterior else 'Right'
                        horizontal=('Head' if top else 'Sill') if side in ['Left','Right'] else side
                        spec=corner_math.frame_corner_spec(profiles,frame_keys,jamb,horizontal);region=corner_math.frame_cut_region(spec,side in ['Left','Right'])
                        report.setdefault('sourceSpecificFrameCuts',[]).append({'member':name,'corner':jamb+' '+horizontal,'spec':spec})
                    # Jamb keeps v >= u; horizontal member keeps v <= u.
                    cut_start=-160;cut_length=330
                    if source.get('sourceSpecificFrameCladding') and key in frame_keys.values():
                        depths=[-d for u,d in pts];cut_start=min(depths)-2;cut_length=max(depths)-min(depths)+4
                    coords=[point(sign*(half+offset-u),cut_start*exterior,sill_datum+(height+offset-v if top else v-offset)) for u,v in region]
                    loops2=DB.CurveArrArray();loops2.Append(curves(coords))
                    plane=DB.SketchPlane.Create(f,DB.Plane.CreateByNormalAndOrigin(DB.XYZ(0,exterior,0),coords[0]))
                    void=f.FamilyCreate.NewExtrusion(False,loops2,plane,cut_length*MM);members.Append(void)
            f.Regenerate();elements[name]=f.CombineElements(members);f.Regenerate()
            report.setdefault('sweepCutChecks',[]).append({'name':name,'signature':signature(elements[name])})
            write()
            if not signature(elements[name]):raise ValueError('Sweep disappeared at native cut: '+name)
        for side in ['Left','Right','Head','Sill']:
            swept_member('Moving Sash Aluminium '+side,'sashAluminium'+side,side,'Moving Sash')
        for side in ['Left','Right','Head']:
            if source.get('includePlasterTrim',True):swept_member('Fixed Frame Outer Trim '+side,'frameOuterTrim',side,'Fixed Frame')
            swept_member('Fixed Frame Rail '+side,frame_keys[side],side,'Fixed Frame')
        swept_member('Fixed Frame Sill Cover',frame_keys['Sill'],'Sill','Fixed Frame')
        checkpoint('glazing-spacers-and-seals')
        edge=source['glazingEdgeInsetsMm'];x0=-half+edge['left'];x1=half-edge['right'];z0=edge['sill'];z1=height-edge['head']
        def rect(name,x0,x1,z0,z1,d0,d1,role,holes=None):
            pts=[family_point(x,d0,z) for x,z in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]]
            hs=[[family_point(x,d0,z) for x,z in h] for h in holes] if holes else None
            return extrusion(name,pts,DB.XYZ(0,-exterior,0),d1-d0,role,'Moving Sash',hs)
        if selected_group!='Fixed Frame':
            for i,(a,b) in enumerate(source['glazingDepthRangesMm']):rect('Moving Sash Glass Pane '+str(i+1),x0,x1,z0,z1,a,b,'glazing')
            for i,(a,b) in enumerate([(21,39),(43,61)]):
                # A hollow perimeter ring, kept clear of the centre of both gas cavities.
                inset=4;radial=7;skin=1
                for side in ['Left','Right','Head','Sill']:
                    lo,hi=(z0+inset,z1-inset) if side in ['Left','Right'] else (x0+inset+radial,x1-inset-radial)
                    u0,u1=(x0+inset,x0+inset+radial) if side=='Left' else (x1-inset-radial,x1-inset) if side=='Right' else (z1-inset-radial,z1-inset) if side=='Head' else (z0+inset,z0+inset+radial)
                    pts=[family_point(u0,a,lo),family_point(u1,a,lo),family_point(u1,b,lo),family_point(u0,b,lo)] if side in ['Left','Right'] else [family_point(lo,a,u0),family_point(lo,b,u0),family_point(lo,b,u1),family_point(lo,a,u1)]
                    hs=[family_point(u0+skin,a+skin,lo),family_point(u1-skin,a+skin,lo),family_point(u1-skin,b-skin,lo),family_point(u0+skin,b-skin,lo)] if side in ['Left','Right'] else [family_point(lo,a+skin,u0+skin),family_point(lo,b-skin,u0+skin),family_point(lo,b-skin,u1-skin),family_point(lo,a+skin,u1-skin)]
                    extrusion('Moving Sash Warm Edge '+str(i+1)+' '+side,pts,DB.XYZ.BasisZ if side in ['Left','Right'] else DB.XYZ.BasisX,hi-lo,'spacer','Moving Sash',[hs])
            # Closed glazing seals at the two pane faces, geometry deliberately simplified.
            for a,b in [(15,17),(65,67)]:
                hole=[(x0+9,z0+9),(x0+9,z1-9),(x1-9,z1-9),(x1-9,z0+9)]
                rect('Moving Sash Glazing Seal '+str(a),x0-1,x1+1,z0-1,z1+1,a,b,'seal',[hole])
        if not assembly_only:
            for opening in list(DB.FilteredElementCollector(f).OfClass(DB.Opening)):f.Delete(opening.Id)
            f.FamilyCreate.NewOpening(host,curves([family_point(-half,0,0),family_point(half,0,0),family_point(half,0,height),family_point(-half,0,height)]))
        f.Regenerate()
        # Fine plan curves use source jamb profiles and individual pane boundaries.
        plane=DB.SketchPlane.Create(f,DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisZ,family_point(0,0,height/2)))
        symbolic=[];symbolic_keys=set();plan_segments=[]
        def create_plan_line(a,b,coarse=False):
            if selected_group and not source.get('openingPlanSymbols',False):return
            if a.DistanceTo(b)<.9*MM:return
            key=(coarse,tuple(sorted(tuple(round(getattr(p,axis)/MM,4) for axis in ['X','Y','Z']) for p in [a,b])))
            if key in symbolic_keys:return
            symbolic_keys.add(key)
            c=f.FamilyCreate.NewSymbolicCurve(DB.Line.CreateBound(a,b),plane)
            c.LineStyle=helpers.category(f,'LITHIC Side-Hung Outward Plan').GetGraphicsStyle(DB.GraphicsStyleType.Projection)
            v=c.GetVisibility();v.IsShownOnlyWhenCut=True;v.IsShownInCoarse=coarse;v.IsShownInMedium=not coarse;v.IsShownInFine=not coarse;c.SetVisibility(v);symbolic.append(c)
        def plan_line(a,b):plan_segments.append((a,b))
        for side in ['Left','Right']:
            keys=['frame'+side,'sash'+side,'sashAluminium'+side]
            if source.get('completePlan',False):keys+=[frame_keys[side]]+(['frameOuterTrim'] if source.get('includePlasterTrim',True) else [])
            if selected_group=='Moving Sash':keys=['sash'+side,'sashAluminium'+side]
            elif selected_group=='Fixed Frame':keys=['frame'+side,frame_keys[side]]
            for key in keys:
                pts=section_points(profiles[key]['pointsMm'],side,height/2)
                for a,b in zip(pts,pts[1:]+pts[:1]):plan_line(a,b)
        def plan_polygon(points):
            pts=[family_point(x,d,height/2) for x,d in points]
            for a,b in zip(pts,pts[1:]+pts[:1]):plan_line(a,b)
        if selected_group=='Fixed Frame':pass
        elif source.get('completePlan',False):
            for a,b in source['glazingDepthRangesMm']:plan_polygon([(x0,a),(x1,a),(x1,b),(x0,b)])
            for a,b in [(21,39),(43,61)]:
                for lo,hi in [(x0+4,x0+11),(x1-11,x1-4)]:
                    plan_polygon([(lo,a),(hi,a),(hi,b),(lo,b)])
                    plan_polygon([(lo+1,a+1),(hi-1,a+1),(hi-1,b-1),(lo+1,b-1)])
            for a,b in [(15,17),(65,67)]:
                for lo,hi in [(x0-1,x0+9),(x1-9,x1+1)]:plan_polygon([(lo,a),(hi,a),(hi,b),(lo,b)])
        else:
            for a,b in source['glazingDepthRangesMm']:
                for depth in [a,b]:plan_line(family_point(-half+103.5,depth,height/2),family_point(half-103.5,depth,height/2))
        # Adjacent material boundaries can be coincident (pane/seal/spacer).
        # Merge collinear intervals before creating Revit curves; do not suppress
        # native overlapping-line warnings or remove entire component outlines.
        axial={}
        for a,b in plan_segments:
            axis='X' if abs(a.Y-b.Y)<1e-9 else 'Y' if abs(a.X-b.X)<1e-9 else None
            if axis:
                fixed=a.Y if axis=='X' else a.X;key=(axis,round(fixed/MM,5))
                lo,hi=sorted([getattr(a,axis),getattr(b,axis)])
                axial.setdefault(key,[]).append((lo,hi,a.Z))
            else:create_plan_line(a,b)
        for (axis,fixed_mm),intervals in axial.items():
            merged=[]
            for lo,hi,z in sorted(intervals):
                if merged and lo<=merged[-1][1]+1e-8:merged[-1][1]=max(hi,merged[-1][1])
                else:merged.append([lo,hi,z])
            fixed=fixed_mm*MM
            for lo,hi,z in merged:
                create_plan_line(DB.XYZ(lo,fixed,z) if axis=='X' else DB.XYZ(fixed,lo,z),DB.XYZ(hi,fixed,z) if axis=='X' else DB.XYZ(fixed,hi,z))
        if selected_group and source.get('openingPlanSymbols',False):
            # Coarse views retain a readable moving sash and fixed frame.
            for side in ['Left','Right']:
                key=('frame' if selected_group=='Fixed Frame' else 'sash')+side
                points=profiles[key]['pointsMm'];umin=min(u for u,d in points);umax=max(u for u,d in points);dmin=min(d for u,d in points);dmax=max(d for u,d in points)
                outline=section_points([[umin,dmin],[umax,dmin],[umax,dmax],[umin,dmax]],side,height/2)
                for a,b in zip(outline,outline[1:]+outline[:1]):create_plan_line(a,b,True)
            if selected_group=='Moving Sash':
                for depth in [17,65]:create_plan_line(family_point(x0,depth,height/2),family_point(x1,depth,height/2),True)
        checkpoint('validate-before-constraints')
        report['beforeConstraintSignatures']={name:signature(e) for name,e in elements.items()}
        if any(not s for s in report['beforeConstraintSignatures'].values()):raise ValueError('Solid disappeared before depth constraints')
        checkpoint('lock-host-depth-and-plan-datums')
        report['hostDepthConstraints']={'method':'Rigid unhosted nested assembly; placement controlled in hosted wrapper'} if assembly_only else helpers.lock_host_depth(f,host)
        f.Regenerate();report['familySignatures']={name:signature(e) for name,e in elements.items()}
        report['groups']=groups;report['symbolicCurveCount']=len(symbolic)
        report['analyticVolumeChecks']=[{'name':name,'expectedMm3':expected,'actualMm3':sum(s.Volume/MM**3 for s in solids(elements[name])),'passed':abs(sum(s.Volume/MM**3 for s in solids(elements[name]))-expected)<max(1,expected*.001)} for name,expected in expected_volumes.items()]
        report['materialBindings']=[]
        # Constraint helper subtransactions may roll back. Reacquire API wrappers
        # after those operations instead of retaining earlier FamilyManager state.
        manager=f.FamilyManager
        shared={p.Definition.Name:p for p in manager.Parameters if p.Definition.Name in shared}
        for e in all_forms:
            e=f.GetElement(e.UniqueId)
            ep=e.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM);wanted=shared[params[form_roles[e.UniqueId]]]
            associated=manager.GetAssociatedFamilyParameter(ep)
            # Native combinations may clear the member's material association.
            # Restore the explicit role after all cuts/constraints, then verify it.
            if associated is None or associated.Id!=wanted.Id:manager.AssociateElementParameterToFamilyParameter(ep,wanted)
            associated=manager.GetAssociatedFamilyParameter(ep)
            report['materialBindings'].append({'element':e.Subcategory.Name,'parameter':associated.Definition.Name if associated else None,'passed':associated is not None and associated.Id==wanted.Id})
        if not all(row['passed'] for row in report['materialBindings']):raise ValueError('A material role could not be rebound after native joins')
        checkpoint('commit-family-with-fail-closed-warning-handling')
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Family transaction rolled back; see transactionFailures')
        tx=None
        report['familyWarnings']=[w.GetDescriptionText() for w in f.GetWarnings()]
        forms=list(DB.FilteredElementCollector(f).OfClass(DB.GenericForm))
        report['nativeForms']={'sweeps':sum(isinstance(e,DB.Sweep) for e in forms),'solidExtrusions':sum(isinstance(e,DB.Extrusion) and e.IsSolid for e in forms),'voidExtrusions':sum(isinstance(e,DB.Extrusion) and not e.IsSolid for e in forms),'freeForms':DB.FilteredElementCollector(f).OfClass(DB.FreeFormElement).GetElementCount(),'directShapes':DB.FilteredElementCollector(f).OfClass(DB.DirectShape).GetElementCount()}
        if any(not s for s in report['familySignatures'].values()):raise ValueError('Missing solid after native cuts')
        ids={name:e.UniqueId for name,e in elements.items()};report['partUniqueIds']=ids;report['formRoles']=form_roles
        checkpoint('save-and-reopen-family')
        family_path=os.path.join(output,'LITHIC-Window-SideHung-Outward-880x1180-COMPONENT.rfa');f.SaveAs(family_path,DB.SaveAsOptions());f.Close(False);f=None
        f=application.OpenDocumentFile(family_path)
        report['reopenedFamilySignatures']={name:signature(f.GetElement(uid)) for name,uid in ids.items()}
        report['familyPersistencePassed']=report['familySignatures']==report['reopenedFamilySignatures']
        report['reopenedMaterialBindings']=[]
        for uid,role in form_roles.items():
            e=f.GetElement(uid);associated=f.FamilyManager.GetAssociatedFamilyParameter(e.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM))
            report['reopenedMaterialBindings'].append({'name':e.Subcategory.Name,'expected':params[role],'parameter':associated.Definition.Name if associated else None,'passed':associated is not None and associated.Definition.Name==params[role]})
        if assembly_only:
            report['files']={'family':family_path}
            report['status']='assembly-created-review-required' if report['familyPersistencePassed'] and all(c['passed'] for c in report['analyticVolumeChecks']) and all(c['passed'] for c in report['reopenedMaterialBindings']) and not report['familyWarnings'] else 'technical-checks-failed'
            return report
        checkpoint('isolated-wall-placement')
        p=application.NewProjectDocument(DB.UnitSystem.Metric);loaded=f.LoadFamily(p);symbol=p.GetElement(list(loaded.GetFamilySymbolIds())[0])
        tx=DB.Transaction(p,'LITHIC isolated closed AFSC placement');tx.Start();placement_failure_handler=fail_closed(tx,report);symbol.Activate();level=DB.Level.Create(p,0)
        wt=next(t for t in DB.FilteredElementCollector(p).OfClass(DB.WallType) if t.Kind==DB.WallKind.Basic and t.Width>0)
        wall=DB.Wall.Create(p,DB.Line.CreateBound(point(-2200,0,0),point(2200,0,0)),wt.Id,level.Id,3000*MM,0,False,False);p.Regenerate();uncut=sum(s.Volume for s in solids(wall))
        inst=p.Create.NewFamilyInstance(point(0,0,900),symbol,wall,level,DB.Structure.StructuralType.NonStructural);p.Regenerate()
        if inst.FacingOrientation.DotProduct(wall.Orientation)<0:inst.flipFacing();p.Regenerate()
        tr=inst.GetTransform();base=tr.OfPoint(point(0,0,sill_datum)).Z/MM
        reported_sill=inst.get_Parameter(DB.BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM).AsDouble()/MM+level.Elevation/MM
        report['placementDatums']={'physicalTimberSillMm':base,'reportedSillMm':reported_sill,'passed':abs(base-reported_sill)<.1}
        report['exteriorPassed']=tr.OfVector(DB.XYZ(0,exterior,0)).DotProduct(wall.Orientation)>.999
        report['outsideLeftConventionPassed']=tr.OfVector(DB.XYZ(exterior,0,0)).DotProduct(wall.Orientation.CrossProduct(DB.XYZ.BasisZ))>.999
        report['hostPassed']=inst.Host.Id==wall.Id
        removed=(uncut-sum(s.Volume for s in solids(wall)))/MM**3;expected=width*height*wt.Width/MM
        report['opening']={'actualMm3':removed,'expectedMm3':expected,'passed':abs(removed-expected)<max(1,expected*.001)}
        expected_sigs=sorted(s for parts in report['familySignatures'].values() for s in parts)
        actual_sigs=signature(inst,inst.GetTransform().Inverse)
        report['hostGeometry']={'expected':expected_sigs,'actual':actual_sigs,'passed':len(actual_sigs)==len(expected_sigs) and all(abs(a-b)<=max(.1,abs(b)*1e-6) for row1,row2 in zip(actual_sigs,expected_sigs) for a,b in zip(row1,row2))}
        typ=next(t for t in DB.FilteredElementCollector(p).OfClass(DB.ViewFamilyType) if t.ViewFamily==DB.ViewFamily.ThreeDimensional)
        v=DB.View3D.CreateIsometric(p,typ.Id);v.Name='AFSC closed source-profile study';v.DetailLevel=DB.ViewDetailLevel.Fine;v.DisplayStyle=DB.DisplayStyle.ShadingWithEdges
        target=tr.OfPoint(point(0,0,sill_datum+height/2));eye=target+DB.XYZ(-2,wall.Orientation.Y*3,1.7);forward=(target-eye).Normalize();right=forward.CrossProduct(DB.XYZ.BasisZ).Normalize();up=right.CrossProduct(forward).Normalize();v.SetOrientation(DB.ViewOrientation3D(eye,up,forward))
        hidden=List[DB.ElementId]();hidden.Add(wall.Id);v.HideElements(hidden);v.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Levels),True)
        bounds=DB.BoundingBoxXYZ();bounds.Min=point(-half-50,-150,base-50);bounds.Max=point(half+50,150,base+height+50);v.SetSectionBox(bounds);v.IsSectionBoxActive=True
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Placement rolled back; see transactionFailures')
        tx=None
        checkpoint('export-native-review-image')
        export=DB.ImageExportOptions();export.ExportRange=DB.ExportRange.SetOfViews;views=List[DB.ElementId]();views.Add(v.Id);export.SetViewsAndSheets(views);export.FilePath=os.path.join(output,'closed-study');export.HLRandWFViewsFileType=DB.ImageFileType.PNG;export.ShadowViewsFileType=DB.ImageFileType.PNG;export.PixelSize=1800;export.ZoomType=DB.ZoomFitType.FitToPage;p.ExportImage(export)
        project_path=os.path.join(output,'LITHIC-AFSC-closed-review.rvt');p.SaveAs(project_path,DB.SaveAsOptions())
        report['projectWarnings']=[w.GetDescriptionText() for w in p.GetWarnings()]
        report['files']={'family':family_path,'project':project_path}
        passed=all(c['passed'] for c in report['analyticVolumeChecks']) and all(c['passed'] for c in report['reopenedMaterialBindings']) and report['familyPersistencePassed'] and report['hostPassed'] and report['opening']['passed'] and report['hostGeometry']['passed'] and report['placementDatums']['passed'] and report['exteriorPassed'] and report['outsideLeftConventionPassed'] and not report['familyWarnings'] and not report['projectWarnings'] and report['nativeForms']['freeForms']==0 and report['nativeForms']['directShapes']==0
        report['status']='closed-study-created-review-required' if passed else 'technical-checks-failed'
    except Exception as error:
        report['status']='failed';report['error']=str(error);report['traceback']=traceback.format_exc()
    finally:
        if tx and tx.GetStatus()==DB.TransactionStatus.Started:tx.RollBack()
        for owned in [p,f]:
            if owned is not None and owned.IsValidObject:owned.Close(False)
        report['activeAfter']=snapshot(active);report['activeProjectPreserved']=before==report['activeAfter'];write()
    return report
