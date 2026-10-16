# -*- coding: utf-8 -*-
"""Source-pinned side-hung desktop export; owns only fresh isolated documents."""
import os,io,json,imp,hashlib,math,traceback
from pyrevit import DB

BUILDER='lithic-window-sidehung-desktop/0.1.0'
def file_hash(path):
    with open(path,'rb') as stream:return hashlib.sha256(stream.read()).hexdigest()

def verify_materials(f,b):
    fm=f.FamilyManager;parameters={p.Definition.Name:p for p in fm.Parameters}
    names=['Timber Material','Aluminium Material','Glazing Material','Glazing Spacer Material','Glazing Seal Material'];counts=[8,8,3,8,2]
    original={n:fm.CurrentType.AsElementId(parameters[n]) for n in names}
    child=next(e for e in DB.FilteredElementCollector(f).OfClass(DB.FamilyInstance));rows=[]
    for angle in [0,45,90]:
        tx=DB.Transaction(f,'Verify nested materials');tx.Start();holder={};handler=b.fail_closed(tx,holder)
        try:
            fm.Set(parameters['Opening Angle'],math.radians(angle));f.Regenerate();baseline=b.signature(child)
            sentinel=DB.Material.Create(f,'LITHIC isolated material verification '+str(angle))
            for name,count in zip(names,counts):
                fm.Set(parameters[name],sentinel);f.Regenerate();solids=b.solids(child)
                actual=sum(1 for solid in solids if all(face.MaterialElementId==sentinel for face in solid.Faces))
                affected=sum(1 for solid in solids if any(face.MaterialElementId==sentinel for face in solid.Faces))
                rows.append({'degrees':angle,'parameter':name,'expectedSolids':count,'actualSolids':actual,'affectedSolids':affected,'passed':actual==count and affected==count and b.signature(child)==baseline})
                fm.Set(parameters[name],original[name]);f.Regenerate()
        finally:tx.RollBack()
    return rows

def build(application,active,request,digest,source_path,wall_template,generic_template,output,helpers,modules=None):
    if os.path.exists(output):raise ValueError('Use a fresh output directory')
    if application.VersionNumber!='2024':raise ValueError('This prototype export is verified for Revit 2024 only')
    os.makedirs(output);here=modules or os.path.dirname(__file__)
    b=imp.load_source('lithic_sidehung_geometry',os.path.join(here,'build_closed.py'))
    rb=imp.load_source('lithic_sidehung_rig',os.path.join(here,'build_native.py'))
    hb=imp.load_source('lithic_sidehung_host',os.path.join(here,'wrap_hosted.py'))
    with io.open(source_path,encoding='utf-8') as stream:source=json.load(stream)
    source['openingPlanSymbols']=True
    report={'kind':'lithic-sidehung-native-report','schemaVersion':'0.1','builder':BUILDER,'requestSha256':digest,'configuration':request['configuration'],'revitVersion':application.VersionNumber,'geometryMode':'fixed-size-snapshot','nativeParameterFlex':False,'openingAngleControlVerified':False,'manufacturerApproved':False,'manufacturerMechanismVerified':False,'maximumOpeningVerified':False,'status':'running','activeBefore':b.snapshot(active)}
    f=None;p=None;tx=None
    def write(stage):
        report['stage']=stage
        with io.open(os.path.join(output,'native-report.json'),'w',encoding='utf-8') as stream:stream.write(json.dumps(report,indent=2))
    try:
        write('source-components');components=os.path.join(output,'components');os.makedirs(components)
        for key,group in [('sash','Moving Sash'),('frame','Fixed Frame')]:
            selected=dict(source);selected['openingStudyGeometryGroup']=group;path=os.path.join(components,key+'-source.json')
            with io.open(path,'w',encoding='utf-8') as stream:stream.write(json.dumps(selected))
            result=b.build(application,active,path,generic_template,os.path.join(components,key),helpers,True)
            if result['status']!='assembly-created-review-required':raise ValueError(key+' native geometry failed: '+str(result.get('error')))
        write('opening-rig');rig=rb.build(application,active,components,os.path.join(here,'hinge-reference.json'),generic_template,os.path.join(output,'rig'),b)
        if rig.get('error') or rig.get('headCornerCheckResolved') is not True:raise ValueError('Opening rig or head geometry failed')
        write('hosted-matrix');host=hb.build(application,active,rig,source,wall_template,os.path.join(output,'hosted'),b)
        if host['status']!='hosted-opening-cut-verified-review-required':raise ValueError('Hosted native matrix failed: '+str(host.get('error')))
        report.update({'headCornerCheckResolved':True,'openingAngleControlVerified':True,'hostedCases':host['placementChecks'],'familyPersistencePassed':host['familyPersistencePassed'],'projectPersistenceChecks':host['projectPersistenceChecks'],'wallCutPersisted':host['reopenedWallCutPassed'],'planViewsPersisted':host['planViewsPersisted']})
        write('top-level-material-checks');f=application.OpenDocumentFile(host['files']['family']);report['materialCases']=verify_materials(f,b)
        if not all(row['passed'] for row in report['materialCases']):raise ValueError('Top-level material propagation failed')
        fm=f.FamilyManager;params={q.Definition.Name:q for q in fm.Parameters};c=request['configuration']
        tx=DB.Transaction(f,'Apply reviewed browser configuration');tx.Start();handler=b.fail_closed(tx,report)
        fm.Set(params['Opening Angle'],math.radians(c['openingAngleDegrees']))
        for name,white,color in [('Timber Material',c['interior']=='white',(231,229,222)),('Aluminium Material',c['exterior']=='white',(217,220,214))]:
            if white:
                mid=DB.Material.Create(f,'LITHIC '+name+' White');material=f.GetElement(mid);material.Color=DB.Color(*color);fm.Set(params[name],mid)
        for name,value in [('LITHIC Builder',BUILDER),('LITHIC Request SHA256',digest),('LITHIC Geometry Mode','fixed-size-snapshot'),('LITHIC Evidence Status','UNAPPROVED_SOURCE_PROTOTYPE')]:
            fp=fm.AddParameter(name,DB.GroupTypeId.IdentityData,DB.SpecTypeId.String.Text,False);fm.SetFormula(fp,'"'+value+'"')
        f.Regenerate()
        if tx.Commit()!=DB.TransactionStatus.Committed:raise ValueError('Browser configuration transaction rolled back')
        tx=None;family=os.path.join(output,'LITHIC-Window-SideHung-Outward-880x1180.rfa');f.SaveAs(family,DB.SaveAsOptions());f.Close(False);f=None
        write('reopen-final-family');f=application.OpenDocumentFile(family);fm=f.FamilyManager;params={q.Definition.Name:q for q in fm.Parameters}
        report['requestedAnglePersisted']=abs(math.degrees(fm.CurrentType.AsDouble(params['Opening Angle']))-c['openingAngleDegrees'])<1e-6
        report['requestIdentityPersisted']=fm.CurrentType.AsString(params['LITHIC Request SHA256'])==digest
        report['materialValues']={name:f.GetElement(fm.CurrentType.AsElementId(params[name])).Name for name in ['Timber Material','Aluminium Material','Glazing Material','Glazing Spacer Material','Glazing Seal Material']}
        report['familyWarnings']=[w.GetDescriptionText() for w in f.GetWarnings()]
        report['familyFile']=os.path.basename(family);report['familySha256']=file_hash(family);report['reviewProject']=os.path.relpath(host['files']['project'],output)
        report['status']='passed' if report['requestedAnglePersisted'] and report['requestIdentityPersisted'] and not report['familyWarnings'] else 'failed'
    except Exception as error:report.update({'status':'failed','error':str(error),'traceback':traceback.format_exc()})
    finally:
        if tx and tx.GetStatus()==DB.TransactionStatus.Started:tx.RollBack()
        for owned in [p,f]:
            if owned is not None and owned.IsValidObject:owned.Close(False)
        report['activeProjectPreserved']=report['activeBefore']==b.snapshot(active)
        if not report['activeProjectPreserved']:report['status']='failed'
        write(report.get('stage','stopped'))
    return report
