# -*- coding: utf-8 -*-
import os,io,json,imp,sys,datetime,traceback
from pyrevit import revit,forms
HERE=os.path.dirname(__file__);sys.path.insert(0,HERE)
contract=imp.load_source('lithic_sidehung_contract',os.path.join(HERE,'desktop_contract.py'))
helpers=imp.load_source('lithic_sidehung_authoring',os.path.join(HERE,'authoring.py'))
builder=imp.load_source('lithic_sidehung_export',os.path.join(HERE,'export_builder.py'))
def main():
    path=forms.pick_file(file_ext='json',title='Choose request.json from your LITHIC side-hung handoff')
    if not path:return
    with open(path,'rb') as stream:raw=stream.read()
    with io.open(os.path.join(os.path.dirname(path),'manifest.json'),encoding='utf-8') as stream:manifest=json.load(stream)
    with io.open(os.path.join(HERE,'definition.json'),encoding='utf-8') as stream:definition=json.load(stream)
    request,digest=contract.validate(raw,manifest,definition)
    wall=forms.pick_file(file_ext='rft',title='Choose an empty wall-hosted Window template')
    if not wall:return
    generic=forms.pick_file(file_ext='rft',title='Choose Metric Generic Model.rft (unhosted)')
    if not generic:return
    folder=forms.pick_folder(title='Choose where to save LITHIC side-hung results')
    if not folder:return
    output=os.path.join(folder,'LITHIC-SideHung-'+datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')+'-'+digest[:8])
    result=builder.build(revit.doc.Application,revit.doc,request,digest,os.path.join(HERE,'source.json'),wall,generic,output,helpers)
    forms.alert('Native checks: '+result['status']+'\n\nResults: '+output+'\n\nReview the .rfa and hosted review .rvt. Import native-report.json into the matching browser configuration. Fixed size; opening travel is diagnostic.',title='LITHIC Side-Hung Outward Window')
try:main()
except Exception as error:forms.alert(str(error)+'\n\nNo verified output is claimed.\n'+traceback.format_exc(),title='LITHIC side-hung handoff stopped')
