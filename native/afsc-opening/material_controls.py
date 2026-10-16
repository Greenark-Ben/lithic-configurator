# -*- coding: utf-8 -*-
"""Propagate the five shared material controls through native nested families."""
import os,tempfile
from System import Guid
from pyrevit import DB

NAMES=['Timber Material','Aluminium Material','Glazing Material','Glazing Spacer Material','Glazing Seal Material']

def promote(document,instances,source,instance_controls):
    app=document.Application;fm=document.FamilyManager;previous=app.SharedParametersFilename
    handle,path=tempfile.mkstemp(prefix='lithic-sidehung-materials-',suffix='.txt');os.close(handle)
    result=[]
    try:
        app.SharedParametersFilename=path;group=app.OpenSharedParameterFile().Groups.Create('LITHIC')
        schema={p['name']:p for p in source['authoringRules']['sharedParameterSchema']['parameters']}
        for name in NAMES:
            entry=schema[name];opts=DB.ExternalDefinitionCreationOptions(name,DB.SpecTypeId.Reference.Material)
            opts.GUID=Guid(entry['guid']);opts.Visible=True;opts.UserModifiable=True
            parameter=fm.AddParameter(group.Definitions.Create(opts),DB.GroupTypeId.Materials,instance_controls)
            children=[]
            for child in instances:
                ep=child.LookupParameter(name)
                if ep is None:raise ValueError('Nested family lacks '+name)
                if not children:fm.Set(parameter,ep.AsElementId())
                fm.AssociateElementParameterToFamilyParameter(ep,parameter)
                linked=fm.GetAssociatedFamilyParameter(ep)
                children.append(linked is not None and linked.Id==parameter.Id)
            result.append({'name':name,'guid':str(parameter.GUID),'instance':parameter.IsInstance,'associations':children,'passed':all(children) and str(parameter.GUID).lower()==entry['guid']})
        document.Regenerate()
    finally:
        app.SharedParametersFilename=previous;os.remove(path)
    if not all(row['passed'] for row in result):raise ValueError('Nested material association failed')
    return result
