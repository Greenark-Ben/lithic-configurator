# -*- coding: utf-8 -*-
"""AFKC native forms and drawing conventions. No FreeForm or DirectShape fallback."""
from __future__ import division
from pyrevit import DB
from contract import expected_parts, native_specs, polygon_moments

MM=1/304.8

def point(x,y,z):return DB.XYZ(x*MM,y*MM,z*MM)

def curves(points,closed=True):
    result=DB.CurveArray()
    for i in range(len(points) if closed else len(points)-1):result.Append(DB.Line.CreateBound(points[i],points[(i+1)%len(points)]))
    return result

def category(document,name):
    result=next((c for c in document.OwnerFamily.FamilyCategory.SubCategories if c.Name==name),None)
    return result if result is not None else document.Settings.Categories.NewSubcategory(document.OwnerFamily.FamilyCategory,name)

def positive_solids(element):return [g for g in element.get_Geometry(DB.Options()) if isinstance(g,DB.Solid) and g.Volume>1e-10]

def create_forms(document,source,width,height,exterior,materials):
    manager=document.FamilyManager
    parameters={}
    for role,name in source['authoringRules']['materialParameters'].items():
        fp=manager.AddParameter(name,DB.GroupTypeId.Materials,DB.SpecTypeId.Reference.Material,False)
        manager.Set(fp,materials[role]);parameters[role]=fp
    def bind(element,name,role):
        element.Subcategory=category(document,'LITHIC '+name)
        ep=element.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM);ep.Set(materials[role]);manager.AssociateElementParameterToFamilyParameter(ep,parameters[role])
        return element
    def mapped(values):return point(values[0],values[2]*exterior,values[1])
    elements={}
    for part in expected_parts(source,width,height):
        if part['role'] in ['aluminium','seal']:continue
        loops=DB.CurveArrArray()
        if 'sweep' in part:
            s=part['sweep'];origin=s['originMm'];inward=s['inward']
            for polygon in [s['pointsMm']]+s.get('holesMm',[]):
                vertices=[mapped([origin[i]+inward[i]*u+(z if i==2 else 0) for i in range(3)]) for u,z in polygon]
                loops.Append(curves(vertices))
            normal=mapped(s['axis']).Normalize();length=s['lengthMm']
        else:
            x,h,z=part['position'];w,hh,d=part['size'];start=z-d/2
            vertices=[mapped(v) for v in [[x-w/2,h-hh/2,start],[x+w/2,h-hh/2,start],[x+w/2,h+hh/2,start],[x-w/2,h+hh/2,start]]]
            loops.Append(curves(vertices));normal=DB.XYZ(0,exterior,0);length=d
        plane=DB.SketchPlane.Create(document,DB.Plane.CreateByNormalAndOrigin(normal,vertices[0]))
        element=document.FamilyCreate.NewExtrusion(True,loops,plane,length*MM)
        elements[part['id']]=bind(element,part['id'].replace('-',' ').title(),part['role'])
    profiles=source['profiles'];half=width/2
    path=[point(-half,0,0),point(-half,0,height),point(half,0,height),point(half,0,0)]
    input_checks=[]
    def sweep(profile,path,name,role,expected_volume):
        loops=DB.CurveArrArray();loops.Append(curves([point(u,-d*exterior,0) for u,d in profile]))
        p=document.Application.Create.NewCurveLoopsProfile(loops)
        plane=DB.SketchPlane.Create(document,DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisY,path[0]))
        element=bind(document.FamilyCreate.NewSweep(True,curves(path,False),plane,p,0,DB.ProfilePlaneLocation.Start),name,role)
        document.Regenerate();solid=positive_solids(element)
        actual=sum(g.Volume for g in solid)*304.8**3
        input_checks.append({'name':name,'nativeType':element.GetType().Name,'volumeMm3':actual,'expectedVolumeMm3':expected_volume,'passed':len(solid)==1 and abs(actual-expected_volume)<=max(1,expected_volume*.001)})
        return element
    def profile_volume(name,length,trim):
        a,m=polygon_moments(profiles[name]['pointsMm']);return a*length-trim*m
    u=sweep(profiles['aluminiumHeadJamb']['pointsMm'],path,'Aluminium Head And Jambs','aluminium',profile_volume('aluminiumHeadJamb',width+2*height,4))
    ret=sweep(profiles['aluminiumCoverageReturn']['pointsMm'],path,'Aluminium Coverage Return','aluminium',profile_volume('aluminiumCoverageReturn',width+2*height,4))
    sill=sweep(profiles['aluminiumSill']['pointsMm'],[point(half,0,0),point(-half,0,0)],'Aluminium Sill','aluminium',profile_volume('aluminiumSill',width,0))
    for body,key in [(u,'aluminium-head-jamb-return'),(sill,'aluminium-sill')]:
        members=DB.CombinableElementArray();members.Append(body)
        if body.Id==u.Id:members.Append(ret)
        for sign in [-1,1]:
            coords=[(half-150,-50),(half+50,-50),(half-150,150)] if body.Id==u.Id else [(half-150,150),(half+50,-50),(half+50,150)]
            vertices=[point(sign*x,30*exterior,z) for x,z in coords];loops=DB.CurveArrArray();loops.Append(curves(vertices))
            plane=DB.SketchPlane.Create(document,DB.Plane.CreateByNormalAndOrigin(DB.XYZ(0,exterior,0),vertices[0]))
            void=document.FamilyCreate.NewExtrusion(False,loops,plane,50*MM)
            void.Subcategory=category(document,'LITHIC Cladding Mitre Cuts');members.Append(void)
        document.Regenerate();elements[key]=document.CombineElements(members)
    seal=sweep(profiles['glazingSeal']['pointsMm'],path+[path[0]],'Glazing Seal Perimeter','seal',profile_volume('glazingSeal',2*(width+height),8))
    elements['seal-perimeter']=seal
    for element in DB.FilteredElementCollector(document).OfClass(DB.GenericForm):
        vis=element.GetVisibility();vis.IsShownInTopBottom=False;vis.IsShownInPlanRCPCut=False;element.SetVisibility(vis)
    return elements,input_checks

def create_plan_symbols(document,source,width,height,exterior,cladding):
    """LOD symbols; fine cladding is a section through actual native joined geometry."""
    for e in list(DB.FilteredElementCollector(document).OfClass(DB.CurveElement)):
        if isinstance(e,DB.SymbolicCurve):document.Delete(e.Id)
    plane=DB.SketchPlane.Create(document,DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisZ,point(0,0,height/2)))
    counts={'coarse':0,'medium':0,'fine':0};seen=set()
    def line(a,b,detail,style):
        if sum((x-y)**2 for x,y in zip(a,b))<=.8**2:return
        key=(detail,tuple(sorted([tuple(round(v,5) for v in a),tuple(round(v,5) for v in b)])))
        if key in seen:return
        seen.add(key);cat=category(document,'LITHIC Plan '+style);cat.SetLineWeight(1,DB.GraphicsStyleType.Projection)
        e=document.FamilyCreate.NewSymbolicCurve(DB.Line.CreateBound(point(a[0],a[1],height/2),point(b[0],b[1],height/2)),plane)
        e.LineStyle=cat.GetGraphicsStyle(DB.GraphicsStyleType.Projection);v=e.GetVisibility();v.IsShownInCoarse=detail=='coarse';v.IsShownInMedium=detail=='medium';v.IsShownInFine=detail=='fine';v.IsShownOnlyWhenCut=True;e.SetVisibility(v);counts[detail]+=1
    def polygon(points,detail,style):
        for i,a in enumerate(points):line(a,points[(i+1)%len(points)],detail,style)
    for detail in ['coarse','medium','fine']:
        for sign in [-1,1]:
            def mapped(points):return [[sign*(width/2-u),-d*exterior] for u,d in points]
            if detail=='coarse':profile=[[0,-52.5],[53.5,-52.5],[53.5,52.5],[0,52.5]]
            elif detail=='medium':profile=[[0,-52.5],[34.5,-52.5],[34.5,13.5],[53.5,13.5],[53.5,52.5],[0,52.5]]
            else:profile=source['profiles']['timberJamb']['pointsMm']
            polygon(mapped(profile),detail,'Frame')
            if detail=='fine':
                bead=mapped(source['profiles']['beadHeadJamb']['pointsMm'])
                for i in [0,1]:line(bead[i],bead[i+1],detail,'Frame')
                polygon(mapped(source['profiles']['glazingSeal']['pointsMm']),detail,'Seal')
        depths=[-10.5,37.5] if detail!='fine' else [v for pair in source['glazing']['paneDepthRangesMm'] for v in pair]
        for depth in depths:line([-width/2+53.5,depth*exterior],[width/2-53.5,depth*exterior],detail,'Glazing')
    native=positive_solids(cladding)[0]
    cut=DB.BooleanOperationsUtils.CutWithHalfSpace(native,DB.Plane.CreateByNormalAndOrigin(DB.XYZ.BasisZ,point(0,0,height/2)))
    for face in cut.Faces:
        if isinstance(face,DB.PlanarFace) and face.FaceNormal.Z<-.9999 and abs(face.Origin.Z/MM-height/2)<.001:
            for edges in face.EdgeLoops:
                for edge in edges:
                    curve=edge.AsCurve();a,b=curve.GetEndPoint(0),curve.GetEndPoint(1)
                    line([a.X/MM,a.Y/MM],[b.X/MM,b.Y/MM],'fine','Cladding')
    spacer=source['glazing']['spacer'];start=40.5+spacer['edgeInsetMm'];radial=spacer['radialHeightMm'];skin=spacer['skinMm']
    for sign in [-1,1]:
        for a,b in source['glazing']['cavityDepthRangesMm']:
            for inset in [0,skin]:
                polygon([[sign*(width/2-u),d*exterior] for u,d in [(start+inset,a+inset),(start+radial-inset,a+inset),(start+radial-inset,b-inset),(start+inset,b-inset)]],'fine','Glazing')
    return counts

def authoring_checks(document,source,width,height,exterior,elements,input_checks):
    forms=list(DB.FilteredElementCollector(document).OfClass(DB.GenericForm))
    sweeps=[e for e in forms if isinstance(e,DB.Sweep)]
    extrusions=[e for e in forms if isinstance(e,DB.Extrusion)]
    bindings=[]
    wanted=source['authoringRules']['materialParameters']
    for e in forms:
        if not e.IsSolid:continue
        p=document.FamilyManager.GetAssociatedFamilyParameter(e.get_Parameter(DB.BuiltInParameter.MATERIAL_ID_PARAM))
        name=e.Subcategory.Name if e.Subcategory else ''
        role='timber' if 'Timber' in name or 'Bead' in name else 'glazing' if 'Glass Pane' in name else 'spacer' if 'Spacer' in name else 'seal' if 'Seal' in name else 'aluminium'
        bindings.append({'id':e.UniqueId,'materialParameter':p.Definition.Name if p else None,'expectedParameter':wanted[role],'passed':p is not None and p.Definition.Name==wanted[role]})
    metal=[positive_solids(elements[k])[0] for k in ['aluminium-head-jamb-return','aluminium-sill']]
    overlap=DB.BooleanOperationsUtils.ExecuteBooleanOperation(metal[0],metal[1],DB.BooleanOperationsType.Intersect).Volume*304.8**3
    corners=[]
    for sign in [-1,1]:
        target=point(sign*width/2,62.5*exterior,0)
        distances=[min(edge.AsCurve().GetEndPoint(i).DistanceTo(target)/MM for edge in solid.Edges for i in [0,1]) for solid in metal]
        corners.append({'side':'left' if sign<0 else 'right','outerEndpointDistancesMm':distances,'passed':max(distances)<.001})
    # Centre probes show that neither air cavity has been modelled as a solid.
    empty=[]
    for a,b in source['glazing']['cavityDepthRangesMm']:
        probe=DB.Line.CreateBound(point(0,(a+.1)*exterior,height/2),point(0,(b-.1)*exterior,height/2))
        segments=sum(s.IntersectWithCurve(probe,DB.SolidCurveIntersectionOptions()).SegmentCount for element in elements.values() for s in positive_solids(element))
        empty.append({'rangeMm':[a,b],'solidSegments':segments,'passed':segments==0})
    no_free=DB.FilteredElementCollector(document).OfClass(DB.FreeFormElement).GetElementCount()==0
    no_direct=DB.FilteredElementCollector(document).OfClass(DB.DirectShape).GetElementCount()==0
    mode_ok=len(sweeps)==4 and sum(e.IsSolid for e in extrusions)==19 and sum(not e.IsSolid for e in extrusions)==4
    return {'nativeAuthoringPassed':mode_ok and no_free and no_direct and all(c['passed'] for c in input_checks),'nativeFormCounts':{'sweeps':len(sweeps),'solidExtrusions':sum(e.IsSolid for e in extrusions),'voidExtrusions':sum(not e.IsSolid for e in extrusions),'freeForms':0 if no_free else 1,'directShapes':0 if no_direct else 1},'sweepInputChecks':input_checks,'materialsBoundPassed':all(b['passed'] for b in bindings),'materialBindings':bindings,'cornerChecksPassed':overlap<.01 and all(c['passed'] for c in corners),'claddingOverlapMm3':overlap,'lowerCorners':corners,'cavitiesEmptyPassed':all(e['passed'] for e in empty),'cavityProbes':empty,'planVisibilityPassed':all(not e.GetVisibility().IsShownInTopBottom and not e.GetVisibility().IsShownInPlanRCPCut for e in forms)}
