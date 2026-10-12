# -*- coding: utf-8 -*-
"""Pure, deterministic AFKC boundary. No Revit imports and no request code execution."""
from __future__ import division
import hashlib
import json
import math

BUILDER = 'lithic-afkc-desktop/0.1'
CASES = [(900, 1200), (1200, 1500), (1500, 1800)]

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isnan(value) and not math.isinf(value)

def expected_parts(source, width, height):
    f = 53.5
    profiles = source['profiles']
    members = [
        ('left', [-width/2, 0, 0], [1, 0, 0], [0, 1, 0], height, 'timberJamb', 'aluminiumHeadJamb'),
        ('right', [width/2, 0, 0], [-1, 0, 0], [0, 1, 0], height, 'timberJamb', 'aluminiumHeadJamb'),
        ('head', [-width/2+f, height, 0], [0, -1, 0], [1, 0, 0], width-2*f, 'timberHead', 'aluminiumHeadJamb'),
        ('sill', [-width/2+f, 0, 0], [0, 1, 0], [1, 0, 0], width-2*f, 'timberSill', 'aluminiumSill')]
    parts = []
    for name, origin, inward, axis, length, timber, aluminium in members:
        for role, profile in [('timber', timber), ('aluminium', aluminium)]:
            points = [[u, -z] for u, z in profiles[profile]['pointsMm']]
            bounds = []
            for i in range(3):
                values = [origin[i]+inward[i]*u+axis[i]*t+(z if i == 2 else 0) for u, z in points for t in [0, length]]
                bounds.append([min(values), max(values)])
            parts.append({'id': role+'-'+name, 'role': role, 'position': [(a+b)/2 for a, b in bounds], 'size': [b-a for a, b in bounds],
                          'sweep': {'pointsMm': points, 'originMm': origin, 'inward': inward, 'axis': axis, 'lengthMm': length}})
    parts.append({'id': 'glazing', 'role': 'glazing', 'position': [0, height/2, 13.5], 'size': [width-81, height-81, 48]})
    return parts

def validate(raw, manifest, source):
    digest = hashlib.sha256(raw).hexdigest()
    if manifest.get('builder') != BUILDER or manifest.get('requestSha256') != digest:
        raise ValueError('The request does not match this handoff package. Download a fresh package from LITHIC.')
    request = json.loads(raw.decode('utf-8'))
    if request.get('kind') != 'lithic-build-request' or request.get('schemaVersion') != '0.1' or request.get('units') != 'mm':
        raise ValueError('Unsupported build request format.')
    if request.get('geometryEngine') != 'fixed-window-profile-sweeps/0.1' or not request.get('approvedAt'):
        raise ValueError('Only reviewed AFKC profile requests are supported by this builder.')
    definition = request['definition']
    if definition.get('id') != 'elitfonster-afkc-profile-proof' or definition.get('operation') != 'fixed':
        raise ValueError('This builder only accepts the AFKC fixed-window proof.')
    profile = definition.get('profile', {})
    if profile.get('id') != 'afkc-polygon/0.1' or profile.get('manufacturerApproved') is not False or profile.get('source') != source:
        raise ValueError('The source profile bundle was changed or is unsupported.')
    if [definition.get(k) for k in ['frameFace', 'frameDepth', 'glazingThickness']] != [53.5, 105, 48]:
        raise ValueError('Fixed source section dimensions were changed.')
    config = request['configuration']
    width, height = config['width'], config['height']
    if not all(finite(n) and 300 <= n <= 3000 for n in [width, height]):
        raise ValueError('Overall dimensions must be 300–3000 mm.')
    if config.get('interior') not in ['timber', 'white'] or config.get('exterior') not in ['graphite', 'white']:
        raise ValueError('Unsupported finish selection.')
    if request.get('parts') != expected_parts(source, width, height):
        raise ValueError('Exported geometry does not match the deterministic AFKC engine.')
    return request, digest

def verification_sizes(request):
    selected = (request['configuration']['width'], request['configuration']['height'])
    return [selected] + [case for case in CASES if case != selected]

def polygon_area(points):
    return abs(sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points)))/2)

def volume_mm3(part):
    if 'sweep' in part:
        return polygon_area(part['sweep']['pointsMm'])*part['sweep']['lengthMm']
    return part['size'][0]*part['size'][1]*part['size'][2]
