# -*- coding: utf-8 -*-
"""Bounded, source-pinned request validation; usable without Revit."""
from __future__ import division
import json,hashlib,math,re
BUILDER='lithic-window-sidehung-desktop/0.1.0'
def validate(raw,manifest,definition):
    digest=hashlib.sha256(raw).hexdigest();request=json.loads(raw.decode('utf-8'))
    if manifest.get('builder')!=BUILDER or manifest.get('requestSha256')!=digest:raise ValueError('Side-hung handoff identity does not match')
    if request.get('definition')!=definition or definition.get('productId')!='lithic.window.side-hung-outward':raise ValueError('Use the reviewed LITHIC side-hung definition')
    c=request.get('configuration',{})
    if set(c)!=set(['width','height','interior','exterior','openingAngleDegrees']):raise ValueError('Unsupported configuration fields')
    if c.get('width')!=880 or c.get('height')!=1180:raise ValueError('Only the 880 x 1180 mm snapshot is supported')
    if c.get('interior') not in ['timber','white'] or c.get('exterior') not in ['graphite','white']:raise ValueError('Unsupported finish')
    angle=c.get('openingAngleDegrees')
    if isinstance(angle,bool) or not isinstance(angle,(int,float)) or math.isnan(angle) or math.isinf(angle) or angle<0 or angle>90:raise ValueError('Diagnostic opening angle must be 0 to 90 degrees')
    if not isinstance(request.get('approvedAt'),str) and not isinstance(request.get('approvedAt'),type(u'')):raise ValueError('Approve the definition first')
    if not re.match(r'^\d{4}-\d{2}-\d{2}T',request['approvedAt']):raise ValueError('Missing approval timestamp')
    if request.get('kind')!='lithic-build-request' or request.get('schemaVersion')!='0.1' or request.get('geometryEngine')!='side-hung-native-snapshot/0.1' or request.get('units')!='mm' or request.get('parts')!=[] or request.get('nativeStatus')!='not-built':raise ValueError('Unsupported side-hung build contract')
    if manifest.get('nativeParameterFlex') is not False or manifest.get('geometryMode')!='fixed-size-snapshot':raise ValueError('Snapshot manifest required')
    return request,digest
