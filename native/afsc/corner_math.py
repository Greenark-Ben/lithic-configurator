"""Profile-aware compound mitres; all dimensions are source millimetres."""
from __future__ import division

OFFSETS={'Left':0,'Right':0,'Head':3.5,'Sill':2.0}
KNEE=76.533

def corner_spec(profiles,jamb,horizontal):
    def outer(side):
        return min(u for u,d in profiles['sashAluminium'+side]['pointsMm'] if abs(d+6.939)<.001)
    uj=KNEE+OFFSETS[jamb];vh=KNEE+OFFSETS[horizontal]
    m=(vh-outer(horizontal))/(uj-outer(jamb));b=vh-m*uj
    return {'kneeU':uj,'kneeV':vh,'slope':m,'intercept':b,'delta':OFFSETS[horizontal]-OFFSETS[jamb]}

def frame_sill_spec():
    # Different fixed-frame jamb and sill face widths require an oblique cut,
    # shared by both members, rather than assuming equal-width 45-degree mitres.
    m=(28.279-9.72)/(40.2-3.081);b=9.72-m*3.081
    return {'kneeU':300,'kneeV':m*300+b,'slope':m,'intercept':b,'delta':0}

def frame_corner_spec(profiles,keys,jamb,horizontal):
    def front(side):
        values=[u for u,d in profiles[keys[side]]['pointsMm'] if abs(d+10)<.001]
        if len(values)<2:raise ValueError('Frame exterior face needs two source points: '+side)
        return min(values),max(values)
    a,b=front(jamb);c,d=front(horizontal)
    m=(d-c)/(b-a);offset=c-m*a
    return {'kneeU':300,'kneeV':m*300+offset,'slope':m,'intercept':offset,'delta':0}

def boundary(spec,u):
    return spec['slope']*u+spec['intercept'] if u<spec['kneeU'] else u+spec['delta']

def inverse(spec,v):
    return (v-spec['intercept'])/spec['slope'] if v<spec['kneeV'] else v-spec['delta']

def cut_region(spec,jamb):
    # Complementary outlines share exactly the same compound boundary.
    edge=[[-150,boundary(spec,-150)]]
    if -150<spec['kneeU']<250:edge.append([spec['kneeU'],spec['kneeV']])
    edge.append([250,boundary(spec,250)])
    low=min(-200,min(p[1] for p in edge)-100);high=max(350,max(p[1] for p in edge)+100)
    return [[-150,low],[250,low]]+list(reversed(edge)) if jamb else edge+[[250,high],[-150,high]]

def frame_cut_region(spec,jamb):
    # Keep the corner cutter local to the frame section to avoid distant
    # near-coplanar intersections in Revit's thin-sheet solid kernel.
    edge=[[-20,boundary(spec,-20)],[80,boundary(spec,80)]]
    low=min(-30,min(v for u,v in edge)-20);high=max(100,max(v for u,v in edge)+20)
    return [[-20,low],[80,low]]+list(reversed(edge)) if jamb else edge+[[80,high],[-20,high]]

def integral(points,spec,horizontal=False):
    def clip(points,limit,lower):
        out=[]
        for a,b in zip(points,points[1:]+points[:1]):
            inside_a=a[0]<=limit if lower else a[0]>=limit
            inside_b=b[0]<=limit if lower else b[0]>=limit
            if inside_a:out.append(a)
            if inside_a!=inside_b:
                t=(limit-a[0])/(b[0]-a[0]);out.append([limit,a[1]+t*(b[1]-a[1])])
        return out
    def moments(points):
        if len(points)<3:return 0,0
        cross=[a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])]
        signed=sum(cross)/2;sign=1 if signed>=0 else -1
        return abs(signed),sign*sum((a[0]+b[0])*c for a,b,c in zip(points,points[1:]+points[:1],cross))/6
    knee=spec['kneeV'] if horizontal else spec['kneeU']
    a,m=moments(clip(points,knee,True));aa,mm=moments(clip(points,knee,False))
    if horizontal:return (m-spec['intercept']*a)/spec['slope']+mm-spec['delta']*aa
    return spec['slope']*m+spec['intercept']*a+mm+spec['delta']*aa
