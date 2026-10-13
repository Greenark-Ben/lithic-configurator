# -*- coding: utf-8 -*-
"""Isolated native review views. Exports are evidence for visual review, not certification."""
from __future__ import division
import os
from System.Collections.Generic import List
from pyrevit import DB
from authoring import point

def create_review_views(project,instance,width,height,exterior):
    # Instance bounds include template annotations above the physical frame.
    # Transform frame coordinates to keep head crops on the physical model.
    tr=instance.GetTransform()
    corners=[tr.OfPoint(point(x,y,z)) for x in [-width/2,width/2] for y in [-100,100] for z in [0,height]]
    bounds=DB.BoundingBoxXYZ()
    bounds.Min=DB.XYZ(min(p.X for p in corners),min(p.Y for p in corners),min(p.Z for p in corners))
    bounds.Max=DB.XYZ(max(p.X for p in corners),max(p.Y for p in corners),max(p.Z for p in corners))
    mid=(bounds.Min.Z+bounds.Max.Z)/2
    ext=instance.GetTransform().OfVector(DB.XYZ(0,exterior,0)).Y
    level=project.GetElement(instance.LevelId)
    types={v.ViewFamily:v for v in DB.FilteredElementCollector(project).OfClass(DB.ViewFamilyType)}
    views=[]
    for detail,scale in [('coarse',50),('medium',50),('fine',10)]:
        v=DB.ViewPlan.Create(project,types[DB.ViewFamily.FloorPlan].Id,level.Id)
        v.Name='AFKC '+detail+' plan 1-'+str(scale);v.Scale=scale
        v.DetailLevel={'coarse':DB.ViewDetailLevel.Coarse,'medium':DB.ViewDetailLevel.Medium,'fine':DB.ViewDetailLevel.Fine}[detail]
        vr=v.GetViewRange();vr.SetOffset(DB.PlanViewPlane.TopClipPlane,bounds.Max.Z+100/304.8-level.Elevation);vr.SetOffset(DB.PlanViewPlane.CutPlane,mid-level.Elevation);vr.SetOffset(DB.PlanViewPlane.BottomClipPlane,0);vr.SetOffset(DB.PlanViewPlane.ViewDepthPlane,0);v.SetViewRange(vr)
        crop=DB.BoundingBoxXYZ();crop.Min=DB.XYZ(bounds.Min.X-150/304.8,-150/304.8,0);crop.Max=DB.XYZ(bounds.Max.X+150/304.8,150/304.8,5000/304.8);v.CropBox=crop;v.CropBoxActive=True;v.CropBoxVisible=False
        for cat,weight in [(DB.BuiltInCategory.OST_Windows,1),(DB.BuiltInCategory.OST_Walls,2)]:
            og=DB.OverrideGraphicSettings();og.SetProjectionLineWeight(weight);og.SetCutLineWeight(weight);v.SetCategoryOverrides(DB.ElementId(cat),og)
        v.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Levels),True);views.append(v)
    for end in ['bottom','top']:
        zbase=bounds.Min.Z if end=='bottom' else bounds.Max.Z;direction=1 if end=='bottom' else -1
        for sign in [-1,1]:
            v=DB.View3D.CreateIsometric(project,types[DB.ViewFamily.ThreeDimensional].Id)
            v.Name='AFKC '+('left' if sign<0 else 'right')+' '+end+' corner';v.Scale=2;v.DetailLevel=DB.ViewDetailLevel.Fine;v.DisplayStyle=DB.DisplayStyle.ShadingWithEdges
            target=DB.XYZ(sign*(width/2-40)/304.8,ext*50/304.8,zbase+direction*40/304.8)
            eye=target+DB.XYZ(sign*.9,ext*1.2,direction*.7);forward=(target-eye).Normalize();right=forward.CrossProduct(DB.XYZ.BasisZ).Normalize();up=right.CrossProduct(forward).Normalize();v.SetOrientation(DB.ViewOrientation3D(eye,up,forward))
            v.IsSectionBoxActive=True;box=DB.BoundingBoxXYZ();box.Min=DB.XYZ((width/2-120 if sign>0 else -width/2-40)/304.8,-90/304.8,zbase+(-10 if end=='bottom' else -150)/304.8);box.Max=DB.XYZ((width/2+40 if sign>0 else -width/2+120)/304.8,90/304.8,zbase+(150 if end=='bottom' else 10)/304.8);v.SetSectionBox(box)
            ids=List[DB.ElementId]()
            for wall in DB.FilteredElementCollector(project).OfClass(DB.Wall):
                if wall.CanBeHidden(v):ids.Add(wall.Id)
            if ids.Count:v.HideElements(ids)
            v.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Levels),True)
            og=DB.OverrideGraphicSettings();og.SetProjectionLineWeight(1);og.SetCutLineWeight(1);v.SetElementOverrides(instance.Id,og);views.append(v)
    for name,low,high in [('sill',bounds.Min.Z-5/304.8,bounds.Min.Z+95/304.8),('head',bounds.Max.Z-95/304.8,bounds.Max.Z+5/304.8)]:
        transform=DB.Transform.Identity;transform.BasisX=DB.XYZ.BasisY;transform.BasisY=DB.XYZ.BasisZ;transform.BasisZ=DB.XYZ.BasisX
        box=DB.BoundingBoxXYZ();box.Transform=transform;box.Min=DB.XYZ(-75/304.8,low,-20/304.8);box.Max=DB.XYZ(75/304.8,high,20/304.8)
        v=DB.ViewSection.CreateSection(project,types[DB.ViewFamily.Section].Id,box);v.Name='AFKC '+name+' section';v.Scale=2;v.DetailLevel=DB.ViewDetailLevel.Fine;v.DisplayStyle=DB.DisplayStyle.ShadingWithEdges
        ids=List[DB.ElementId]()
        for wall in DB.FilteredElementCollector(project).OfClass(DB.Wall):
            if wall.CanBeHidden(v):ids.Add(wall.Id)
        if ids.Count:v.HideElements(ids)
        v.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Levels),True)
        og=DB.OverrideGraphicSettings();og.SetProjectionLineWeight(1);og.SetCutLineWeight(1);v.SetElementOverrides(instance.Id,og);views.append(v)
    finish_review_views(views)
    return views

def finish_review_views(views):
    # The host review sections must not draw their markers across plan exports.
    for view in views:
        if isinstance(view,DB.ViewPlan):view.SetCategoryHidden(DB.ElementId(DB.BuiltInCategory.OST_Sections),True)


def export_review_views(project,views,folder,label):
    evidence=[]
    for v in views:
        prefix=label+'-'+v.Name
        opt=DB.ImageExportOptions();opt.ExportRange=DB.ExportRange.SetOfViews;ids=List[DB.ElementId]();ids.Add(v.Id);opt.SetViewsAndSheets(ids);opt.FilePath=os.path.join(folder,prefix);opt.HLRandWFViewsFileType=DB.ImageFileType.PNG;opt.ShadowViewsFileType=DB.ImageFileType.PNG;opt.ZoomType=DB.ZoomFitType.FitToPage;opt.PixelSize=1600;project.ExportImage(opt)
        files=[name for name in os.listdir(folder) if name.startswith(prefix) and name.endswith('.png')]
        if len(files)!=1:raise ValueError('Missing or ambiguous native image export for '+v.Name)
        evidence.append({'view':v.Name,'detailLevel':str(v.DetailLevel),'scale':v.Scale,'file':files[0],'visualAcceptance':'pending'})
    return evidence
