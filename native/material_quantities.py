# -*- coding: utf-8 -*-
"""Read material quantities in isolated copies of native proof projects.
No transactions, family loads or saves target the active document.
"""
from __future__ import division
import io,json,os,hashlib,traceback
from pyrevit import DB

MM3=304.8**3
MM2=304.8**2

def solids(element):
    found=[]
    def collect(items):
        for item in items:
            if isinstance(item,DB.Solid) and item.Volume>1e-10:found.append(item)
            elif isinstance(item,DB.GeometryInstance):collect(item.GetInstanceGeometry())
    collect(element.get_Geometry(DB.Options()))
    return found

def cells(view):
    data=view.GetTableData().GetSectionData(DB.SectionType.Body)
    return [[view.GetCellText(DB.SectionType.Body,r,c) for c in range(data.FirstColumnNumber,data.LastColumnNumber+1)] for r in range(data.FirstRowNumber,data.LastRowNumber+1)]

def number(text):
    return float(text.replace(' ','').replace(u'\u00a0','').replace(',','.'))

def inspect(project,view):
    items=[];expected={}
    windows=list(DB.FilteredElementCollector(project).OfCategory(DB.BuiltInCategory.OST_Windows).WhereElementIsNotElementType())
    for instance in windows:
        mark=instance.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).AsString();by={};counts={}
        shapes=solids(instance)
        if len(shapes)!=22:raise ValueError('Expected 22 native solids per window')
        for solid in shapes:
            mids=set(face.MaterialElementId.IntegerValue for face in solid.Faces)
            if len(mids)!=1 or -1 in mids:raise ValueError('Solid does not have one unambiguous material')
            mid=next(iter(mids));v,a=by.get(mid,(0,0));by[mid]=(v+solid.Volume*MM3,a+sum(f.Area for f in solid.Faces)*MM2);counts[mid]=counts.get(mid,0)+1
        material_ids=list(instance.GetMaterialIds(False))
        if len(material_ids)!=5:raise ValueError('Expected five material roles per window')
        if set(by)!=set(m.IntegerValue for m in material_ids):raise ValueError('Takeoff and solid material sets differ')
        for mid in material_ids:
            name=project.GetElement(mid).Name;solid_volume,face_area=by[mid.IntegerValue];api_volume=instance.GetMaterialVolume(mid)*MM3;api_area=instance.GetMaterialArea(mid,False)*MM2
            volume_pass=abs(api_volume-solid_volume)<=max(1,solid_volume*1e-6)
            items.append({'mark':mark,'material':name,'solidCount':counts[mid.IntegerValue],'solidVolumeMm3':solid_volume,'takeoffVolumeMm3':api_volume,'volumePassed':volume_pass,'solidSurfaceAreaMm2':face_area,'takeoffAreaMm2':api_area,'areaMatchesTotalSolidSurface':abs(api_area-face_area)<=max(1,face_area*1e-6)})
            expected[(mark,name)]=(api_volume,api_area)
    rows=cells(view);checks=[]
    for row in rows:
        key=(row[0],row[1]) if len(row)==4 else None
        if key not in expected:continue
        volume,area=expected[key];actual_volume=number(row[2])*1e9;actual_area=number(row[3])*1e6
        checks.append({'mark':key[0],'material':key[1],'scheduleVolumeMm3':actual_volume,'scheduleAreaMm2':actual_area,'volumePassed':abs(actual_volume-volume)<=1.1,'areaPassed':abs(actual_area-area)<=.01})
    keys=[(c['mark'],c['material']) for c in checks]
    passed=len(windows)==5 and len(items)==25 and len(checks)==25 and len(set(keys))==25 and all(i['volumePassed'] and i['areaMatchesTotalSolidSurface'] for i in items) and all(c['volumePassed'] and c['areaPassed'] for c in checks)
    return {'passed':passed,'instances':len(windows),'materialPairs':items,'scheduleChecks':checks,'scheduleCells':rows,'totalVolumeMm3':sum(i['takeoffVolumeMm3'] for i in items),'allAreasMatchTotalSolidSurface':all(i['areaMatchesTotalSolidSurface'] for i in items)}

def run(application,active,inputs,output):
    if not os.path.isdir(output):os.makedirs(output)
    def state():return {'modified':active.IsModified,'elements':DB.FilteredElementCollector(active).GetElementCount()}
    report={'status':'running','revitVersion':application.VersionNumber,'activeBefore':state(),'cases':[],'nativeParameterFlex':False,'manufacturerApproved':False}
    for label,path in inputs:
        project=None;tx=None;case={'name':label,'status':'failed'}
        try:
            if os.path.normcase(path)==os.path.normcase(active.PathName):raise ValueError('Input is the active project')
            with open(path,'rb') as f:case['inputSha256']=hashlib.sha256(f.read()).hexdigest()
            project=application.OpenDocumentFile(path)
            tx=DB.Transaction(project,'LITHIC isolated material quantity audit');tx.Start()
            windows=sorted(DB.FilteredElementCollector(project).OfCategory(DB.BuiltInCategory.OST_Windows).WhereElementIsNotElementType(),key=lambda e:e.Id.IntegerValue)
            for i,e in enumerate(windows):e.get_Parameter(DB.BuiltInParameter.ALL_MODEL_MARK).Set('Q'+str(i+1))
            view=DB.ViewSchedule.CreateMaterialTakeoff(project,DB.ElementId(DB.BuiltInCategory.OST_Windows));view.Name='LITHIC material quantity proof';view.Definition.IsItemized=True
            available={f.GetName(project):f for f in view.Definition.GetSchedulableFields()}
            case['availableFields']=sorted(available.keys())
            for name,unit,accuracy in [('Mark',None,None),('Material: Name',None,None),('Material: Volume',DB.UnitTypeId.CubicMeters,1e-9),('Material: Area',DB.UnitTypeId.SquareMeters,1e-9)]:
                field=view.Definition.AddField(available[name]);field.ColumnHeading=name
                if unit is not None:
                    fmt=DB.FormatOptions(unit);fmt.UseDefault=False;fmt.Accuracy=accuracy;fmt.SetSymbolTypeId(DB.ForgeTypeId());field.SetFormatOptions(fmt)
            project.Regenerate();view_id=view.UniqueId
            if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Schedule transaction failed')
            case['initial']=inspect(project,view);case['initialWarnings']=[w.GetDescriptionText() for w in project.GetWarnings()]
            options=DB.SaveAsOptions();options.OverwriteExistingFile=False
            saved=os.path.join(output,label+'-material-quantities.rvt');project.SaveAs(saved,options);project.Close(False);project=application.OpenDocumentFile(saved)
            case['reopened']=inspect(project,project.GetElement(view_id));case['reopenedWarnings']=[w.GetDescriptionText() for w in project.GetWarnings()]
            case['persistencePassed']=case['initial']==case['reopened'];case['status']='passed' if case['initial']['passed'] and case['persistencePassed'] and not case['initialWarnings'] and not case['reopenedWarnings'] else 'failed'
            case['projectFile']=os.path.basename(saved)
            with open(saved,'rb') as f:case['projectSha256']=hashlib.sha256(f.read()).hexdigest()
            with io.open(os.path.join(output,label+'-schedule.tsv'),'w',encoding='utf-8') as f:f.write(u'\n'.join(u'\t'.join(row) for row in case['reopened']['scheduleCells']))
        except Exception:case['error']=traceback.format_exc()
        finally:
            if tx and tx.GetStatus()==DB.TransactionStatus.Started:tx.RollBack()
            if project and project.IsValidObject:project.Close(False)
        report['cases'].append(case)
        with io.open(os.path.join(output,'quantity-proof.json'),'w',encoding='utf-8') as f:f.write(json.dumps(report,indent=2))
        if case['status']!='passed':break
    report['activeAfter']=state();report['activeProjectPreserved']=report['activeBefore']==report['activeAfter'];report['status']='passed' if len(report['cases'])==len(inputs) and all(c['status']=='passed' for c in report['cases']) and report['activeProjectPreserved'] else 'failed'
    with io.open(os.path.join(output,'quantity-proof.json'),'w',encoding='utf-8') as f:f.write(json.dumps(report,indent=2))
    return report
