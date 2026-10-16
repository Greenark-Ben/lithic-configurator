# -*- coding: utf-8 -*-
"""Experimental APS proof. No desktop report acceptance or visual pass is claimed."""
from __future__ import division
import datetime
import hashlib
import io
import json
import os
from cloud_builder import build_case, file_hash
from contract import validate

with open(os.path.join(input_root, 'request.json'), 'rb') as stream:
    raw = stream.read()
with io.open(os.path.join(input_root, 'manifest.json'), encoding='utf-8') as stream:
    manifest = json.load(stream)
with io.open(os.path.join(os.path.dirname(__file__), 'afkc-source.json'), encoding='utf-8') as stream:
    source = json.load(stream)
request, digest = validate(raw, manifest, source)
template = os.path.join(input_root, 'window.rft')
result = build_case(application, template, output_root, request, source, request['configuration']['width'], request['configuration']['height'], digest)
cloud_geometry_passed = result['status'] == 'passed'
result['visualReviewStatus'] = 'not-exported-headless-awaiting-Revit-review'
report = {
    'kind': 'lithic-cloud-proof-report', 'schemaVersion': '0.1',
    'adapter': 'lithic-window-fixed-aps-browser/0.3.0',
    'sourceBuilder': manifest['builder'], 'requestSha256': digest,
    'createdAt': datetime.datetime.utcnow().isoformat()+'Z',
    'revitVersion': application.VersionNumber,
    'geometryMode': 'fixed-size-snapshot', 'nativeParameterFlex': False,
    'manufacturerApproved': False, 'visualReviewPassed': False,
    'geometryChecksPassed': cloud_geometry_passed,
    'status': 'geometry-passed-awaiting-visual-review' if cloud_geometry_passed else 'failed',
    'templateSha256': file_hash(template), 'cases': [result]
}
with io.open(os.path.join(output_root, 'cloud-proof-report.json'), 'w', encoding='utf-8') as stream:
    stream.write(json.dumps(report, indent=2, ensure_ascii=False))
print('LITHIC cloud proof: '+report['status'])
