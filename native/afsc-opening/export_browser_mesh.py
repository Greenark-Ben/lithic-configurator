# -*- coding: utf-8 -*-
"""Read-only renderer snapshot; does not author or save a Revit document."""
import io,json,traceback,hashlib

def export(application,active,report_path,output,builder):
    b=builder
    with io.open(report_path,encoding='utf-8') as stream:r=json.load(stream)
    before=b.snapshot(active);f=None;result={'status':'running','parts':[]}
    try:
     f=application.OpenDocumentFile(r['files']['family'])
     result.update({'schemaVersion':'1','units':'mm','sizeMm':[880,1180],'coordinateTransform':'native (X,Y,Z) to browser (-X,Z,Y); proper rotation; mm', 'sourceFamilySha256':hashlib.sha256(open(r['files']['family'],'rb').read()).hexdigest(),'sourceDrawing':'61-37-S221 rev A','manufacturerApproved':False,'headAnalyticVolumeCheckPassed':False,'pivotMm':[-411.6464609802715,0,15.7772291928652]})
     head_checks=[row for row in r.get('analyticVolumeChecks',[]) if row['name']=='Fixed Frame Rail Head']
     result['headAnalyticVolumeCheckPassed']=len(head_checks)==1 and head_checks[0]['passed'] is True
     for name in sorted(r['partUniqueIds']):
      element=f.GetElement(r['partUniqueIds'][name]);vertices=[];volume=0;solid_count=0
      for solid in b.solids(element):
       volume+=solid.Volume/b.MM**3;solid_count+=1
       for face in solid.Faces:
        mesh=face.Triangulate()
        for i in range(mesh.NumTriangles):
         triangle=mesh.get_Triangle(i)
         for j in range(3):
          p=triangle.get_Vertex(j)
          vertices.extend([round(-p.X/b.MM,6),round(p.Z/b.MM,6),round(p.Y/b.MM,6)])
      role='timber' if 'Timber' in name else 'glazing' if 'Glass Pane' in name else 'spacer' if 'Warm Edge' in name else 'seal' if 'Seal' in name else 'aluminium'
      assert vertices and solid_count==1
      result['parts'].append({'id':name.lower().replace(' ','-'),'role':role,'moving':r['groups'][name]=='Moving Sash','sourceUniqueId':element.UniqueId,'sourceNativeType':element.GetType().Name,'sourceVolumeMm3':volume,'verticesMm':vertices})
     result['activeProjectPreserved']=before==b.snapshot(active)
     assert len(result['parts'])==29 and sum(1 for p in result['parts'] if p['moving'])==21 and result['activeProjectPreserved']
     result['status']='extracted'
    except Exception as error:result.update({'status':'failed','error':str(error),'traceback':traceback.format_exc()})
    finally:
     if f and f.IsValidObject:f.Close(False)
     with io.open(output,'w',encoding='utf-8') as stream:stream.write(json.dumps(result,separators=(',',':')))
    return result
