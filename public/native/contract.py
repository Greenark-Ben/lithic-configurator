# -*- coding: utf-8 -*-
"""Pure, deterministic AFKC boundary. No Revit imports and no request code execution."""
from __future__ import division
import hashlib
import json
import math

BUILDER = 'lithic-afkc-desktop/0.2.2'
CASES = [(900, 1200), (1200, 1500), (1500, 1800)]

def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and not math.isnan(value) and not math.isinf(value)

def expected_parts(source, width, height):
    parts = []
    f = 53.5
    profiles = source['profiles']
    def add(pid, role, points, origin, inward, axis, length, mitred=False, holes=None):
        sweep = {'pointsMm':points, 'originMm':origin, 'inward':inward, 'axis':axis, 'lengthMm':length}
        if mitred: sweep['mitred'] = True
        if holes is not None: sweep['holesMm'] = holes
        bounds = []
        for i in range(3):
            values = [origin[i]+inward[i]*u+axis[i]*t+(z if i==2 else 0) for u,z in points for t in ([u,length-u] if mitred else [0,length])]
            bounds.append([min(values),max(values)])
        parts.append({'id':pid,'role':role,'position':[(a+b)/2 for a,b in bounds],'size':[b-a for a,b in bounds],'sweep':sweep})
    members = [('left',[-width/2,0,0],[1,0,0],[0,1,0],height),('right',[width/2,0,0],[-1,0,0],[0,1,0],height),('head',[-width/2,height,0],[0,-1,0],[1,0,0],width),('sill',[-width/2,0,0],[0,1,0],[1,0,0],width)]
    mapped = lambda name:[[u,-z] for u,z in profiles[name]['pointsMm']]
    for name,origin,inward,axis,length in members:
        horizontal = name in ['head','sill']
        timber = 'timberSill' if name=='sill' else 'timberHead' if name=='head' else 'timberJamb'
        add('timber-'+name,'timber',mapped(timber),[origin[0]+(f if horizontal else 0),origin[1],0],inward,axis,length-(2*f if horizontal else 0))
        add('bead-'+name,'timber',mapped('beadSill' if name=='sill' else 'beadHeadJamb'),[origin[0]+(40 if horizontal else 0),origin[1],0],inward,axis,length-(80 if horizontal else 0))
        add('aluminium-'+name,'aluminium',mapped('aluminiumSill' if name=='sill' else 'aluminiumHeadJamb'),origin,inward,axis,length,True)
        if name!='sill':add('return-'+name,'aluminium',mapped('aluminiumCoverageReturn'),origin,inward,axis,length,True)
        add('seal-'+name,'seal',mapped('glazingSeal'),origin,inward,axis,length,True)
    inset=f-source['fixedSectionDimensions']['glazingSeatOverlapMm']['value']
    for i,(a,b) in enumerate(source['glazing']['paneDepthRangesMm']):
        parts.append({'id':'glass-pane-'+str(i+1),'role':'glazing','position':[0,height/2,(a+b)/2],'size':[width-2*inset,height-2*inset,b-a]})
    spacer=source['glazing']['spacer'];edge=spacer['edgeInsetMm'];radial=spacer['radialHeightMm'];skin=spacer['skinMm']
    for i,(a,b) in enumerate(source['glazing']['cavityDepthRangesMm']):
        points=[[0,a],[radial,a],[radial,b],[0,b]];holes=[[[skin,a+skin],[skin,b-skin],[radial-skin,b-skin],[radial-skin,a+skin]]]
        for side in ['left','right','sill','head']:
            vertical=side in ['left','right']
            origin=[(-width/2+inset+edge if side=='left' else width/2-inset-edge-radial),inset+edge,0] if vertical else [-width/2+inset+edge+radial,(inset+edge if side=='sill' else height-inset-edge-radial),0]
            add('spacer-'+str(i+1)+'-'+side,'spacer',points,origin,[1,0,0] if vertical else [0,1,0],[0,1,0] if vertical else [1,0,0],height-2*(inset+edge) if vertical else width-2*(inset+edge+radial),False,holes)
    return parts

def validate(raw, manifest, source):
    digest = hashlib.sha256(raw).hexdigest()
    if manifest.get('builder') != BUILDER or manifest.get('requestSha256') != digest:
        raise ValueError('The request does not match this handoff package. Download a fresh package from LITHIC.')
    request = json.loads(raw.decode('utf-8'))
    if request.get('kind') != 'lithic-build-request' or request.get('schemaVersion') != '0.1' or request.get('units') != 'mm':
        raise ValueError('Unsupported build request format.')
    if request.get('geometryEngine') != 'fixed-window-profile-sweeps/0.2.2' or not request.get('approvedAt'):
        raise ValueError('Only reviewed AFKC profile requests are supported by this builder.')
    definition = request['definition']
    if definition.get('id') != 'elitfonster-afkc-profile-proof' or definition.get('operation') != 'fixed':
        raise ValueError('This builder only accepts the AFKC fixed-window proof.')
    profile = definition.get('profile', {})
    if profile.get('id') != 'afkc-polygon/0.2.2' or profile.get('manufacturerApproved') is not False or profile.get('source') != source:
        raise ValueError('The source profile bundle was changed or is unsupported.')
    if [definition.get(k) for k in ['frameFace', 'frameDepth', 'glazingThickness']] != [53.5, 105, 48]:
        raise ValueError('Fixed source section dimensions were changed.')
    config = request['configuration']
    width, height = config['width'], config['height']
    if not all(finite(n) and 300 <= n <= 3000 for n in [width, height]):
        raise ValueError('Overall dimensions must be 300-3000 mm.')
    if config.get('interior') not in ['timber', 'white'] or config.get('exterior') not in ['graphite', 'white']:
        raise ValueError('Unsupported finish selection.')
    if request.get('parts') != expected_parts(source, width, height):
        raise ValueError('Exported geometry does not match the deterministic AFKC engine.')
    return request, digest

def verification_sizes(request):
    selected = (request['configuration']['width'], request['configuration']['height'])
    return [selected] + [case for case in CASES if case != selected]

def polygon_moments(points):
    cross = [points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in range(len(points))]
    area = sum(cross)/2
    moment = sum((points[i][0]+points[(i+1)%len(points)][0])*cross[i] for i in range(len(points)))/6
    return (area,moment) if area>=0 else (-area,-moment)

def polygon_area(points):
    return polygon_moments(points)[0]

def volume_mm3(part):
    if 'sweep' not in part: return part['size'][0]*part['size'][1]*part['size'][2]
    s=part['sweep'];area,moment=polygon_moments(s['pointsMm'])
    for hole in s.get('holesMm',[]):
        a,m=polygon_moments(hole);area-=a;moment-=m
    return area*s['lengthMm']-(2*moment if s.get('mitred') else 0)

def _cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def _triangles(points):
    p=[list(v) for v in points]
    if sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))<0:p.reverse()
    triangles=[]
    while len(p)>3:
        for i,b in enumerate(p):
            a,c=p[i-1],p[(i+1)%len(p)]
            if _cross(a,b,c)<=1e-10:continue
            if any(all(_cross(x,y,q)>=-1e-10 for x,y in [(a,b),(b,c),(c,a)]) for j,q in enumerate(p) if j not in [(i-1)%len(p),i,(i+1)%len(p)]):continue
            triangles.append([a,b,c]);p.pop(i);break
        else:raise ValueError('Non-simple source profile.')
    triangles.append(p);return triangles

def intersection_moments(first,second):
    area=moment=0
    for a in _triangles(first):
        for b in _triangles(second):
            clip=a[:]
            for i,q in enumerate(b):
                r=b[(i+1)%3];result=[]
                if not clip:break
                for j,end in enumerate(clip):
                    start=clip[j-1];ds=_cross(q,r,start);de=_cross(q,r,end)
                    if (ds>=0)!=(de>=0):
                        ratio=ds/(ds-de);result.append([start[k]+ratio*(end[k]-start[k]) for k in [0,1]])
                    if de>=0:result.append(end)
                clip=result
            if len(clip)>=3:
                value,m=polygon_moments(clip);area+=value;moment+=m
    return area,moment

def native_specs(source,width,height):
    parts=expected_parts(source,width,height)
    checks=[dict(p,expectedVolumeMm3=volume_mm3(p),nativeType='Extrusion') for p in parts if p['role'] not in ['aluminium','seal']]
    profiles=source['profiles'];head=profiles['aluminiumHeadJamb']['pointsMm'];ret=profiles['aluminiumCoverageReturn']['pointsMm'];sill=profiles['aluminiumSill']['pointsMm'];seal=profiles['glazingSeal']['pointsMm']
    a,m=polygon_moments(head);b,n=polygon_moments(ret);overlap,om=intersection_moments(head,ret)
    checks.append({'id':'aluminium-head-jamb-return','role':'aluminium','nativeType':'GeomCombination','position':[0,height/2,51.5],'size':[width,height,22],'expectedVolumeMm3':(a+b-overlap)*(width+2*height)-6*(m+n-om),'maximumJoinedVolumeMm3':(a+b)*(width+2*height)-6*(m+n)})
    a,m=polygon_moments(sill);maxu=max(p[0] for p in sill)
    checks.append({'id':'aluminium-sill','role':'aluminium','nativeType':'GeomCombination','position':[0,maxu/2,51.5],'size':[width,maxu,22],'expectedVolumeMm3':a*width-2*m})
    a,m=polygon_moments(seal)
    checks.append({'id':'seal-perimeter','role':'seal','nativeType':'Sweep','position':[0,height/2,39],'size':[width-94,height-94,3],'expectedVolumeMm3':a*2*(width+height)-8*m})
    return checks
