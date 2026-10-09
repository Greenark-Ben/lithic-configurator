import { Suspense,useEffect,useMemo,useRef,useState,Component,type ReactNode,type RefObject } from 'react';
import { Canvas,useThree,useFrame } from '@react-three/fiber';
import { OrbitControls,ContactShadows,Line } from '@react-three/drei';
import * as THREE from 'three';
import { calculateParts,type Definition,type Configuration } from './engine';
class SceneBoundary extends Component<{children:ReactNode},{failed:boolean}> {state={failed:false};static getDerivedStateFromError(){return {failed:true}};render(){return this.state.failed?<div className="scene-fallback">3D preview unavailable on this device. Your definition and configuration remain available.</div>:this.props.children}}
function woodTexture(){const canvas=document.createElement('canvas');canvas.width=256;canvas.height=512;const ctx=canvas.getContext('2d')!;ctx.fillStyle='#b99670';ctx.fillRect(0,0,256,512);for(let i=0;i<190;i++){const x=(i*37)%256;ctx.strokeStyle=`rgba(77,47,23,${0.025+(i%7)*0.014})`;ctx.lineWidth=0.5+(i%3);ctx.beginPath();ctx.moveTo(x,0);for(let y=0;y<=512;y+=16)ctx.lineTo(x+Math.sin(y/85+i)*2,y);ctx.stroke()}const tex=new THREE.CanvasTexture(canvas);tex.colorSpace=THREE.SRGBColorSpace;return tex}
function Window({definition,config,section,dimensions}:{definition:Definition;config:Configuration;section:boolean;dimensions:boolean}) {
 const parts=useMemo(()=>calculateParts(definition,config),[definition,config]);const wood=useMemo(woodTexture,[]);const w=config.width/1000,h=config.height/1000;
 return <group position={[0,-h/2,0]}>{parts.filter(p=>!section||!p.id.endsWith('right')).map(p=><mesh key={p.id} position={p.position.map(n=>n/1000) as [number,number,number]} castShadow receiveShadow><boxGeometry args={p.size.map(n=>n/1000) as [number,number,number]}/>{p.role==='glazing'?<meshPhysicalMaterial color="#b5c5c2" transparent opacity={0.28} roughness={0.06} metalness={0.1} side={THREE.DoubleSide}/>:<meshStandardMaterial map={p.role==='timber'&&config.interior==='timber'?wood:null} color={p.role==='timber'?(config.interior==='white'?'#e7e5de':'#dbc3a4'):(config.exterior==='white'?'#d9dcd6':'#3c4240')} roughness={p.role==='timber'?0.72:0.34} metalness={p.role==='aluminium'?0.65:0}/>}</mesh>)}
 {dimensions&&<><Line points={[[-w/2,-0.1,0.13],[w/2,-0.1,0.13]]} color="#757d77" lineWidth={1}/><Line points={[[-w/2,-0.13,0.13],[-w/2,-0.06,0.13]]} color="#757d77"/><Line points={[[w/2,-0.13,0.13],[w/2,-0.06,0.13]]} color="#757d77"/><Line points={[[-w/2-0.13,0,0.13],[-w/2-0.13,h,0.13]]} color="#757d77"/></>}
 <ContactShadows position={[0,-0.005,0]} opacity={0.35} scale={6} blur={2.8} far={2}/></group>
}
function DimensionLabels({config,widthLabel,heightLabel}:{config:Configuration;widthLabel:RefObject<HTMLDivElement|null>;heightLabel:RefObject<HTMLDivElement|null>}) {
 const point=useMemo(()=>new THREE.Vector3(),[]);
 useFrame(({camera,size})=>{
  const place=(element:HTMLDivElement|null,x:number,y:number)=>{
   if(!element)return;
   point.set(x,y,0.13).project(camera);
   const halfWidth=element.offsetWidth/2+8,halfHeight=element.offsetHeight/2+8;
   element.style.left=`${Math.max(halfWidth,Math.min(size.width-halfWidth,(point.x+1)*size.width/2))}px`;
   element.style.top=`${Math.max(halfHeight,Math.min(size.height-halfHeight,(1-point.y)*size.height/2))}px`;
  };
  place(widthLabel.current,0,-config.height/2000-0.18);
  place(heightLabel.current,-config.width/2000-0.21,0);
 });
 return null;
}
function DimensionFraming({config}:{config:Configuration}) {
 const {camera,size}=useThree();
 useEffect(()=>{
  if(!(camera instanceof THREE.PerspectiveCamera))return;
  // Reserve space for dimension lines and labels as the approved window flexes.
  const halfFov=THREE.MathUtils.degToRad(camera.fov/2);
  const distance=1.12*Math.max((config.height/1000+0.55)/(2*Math.tan(halfFov)),(config.width/1000+0.7)/(2*Math.tan(halfFov)*Math.max(size.width/size.height,0.1)))+0.2;
  camera.position.copy(camera.position.clone().normalize().multiplyScalar(distance));
  camera.updateProjectionMatrix();
 },[camera,size.width,size.height,config.width,config.height]);
 return null;
}
export default function WindowScene(props:{definition:Definition;config:Configuration;section:boolean;dimensions:boolean}) {
 const widthLabel=useRef<HTMLDivElement>(null),heightLabel=useRef<HTMLDivElement>(null);
 const [lost,setLost]=useState(false);return <SceneBoundary><div className="scene-preview">{lost?<div className="scene-fallback">Graphics context lost. Reload to restore the preview.</div>:<Canvas shadows dpr={[1,2]} camera={{position:[1.5,0.6,3.4],fov:34}} onCreated={({gl})=>gl.domElement.addEventListener('webglcontextlost',()=>setLost(true))}><color attach="background" args={['#eeede7']}/><ambientLight intensity={1.5}/><directionalLight position={[3,5,4]} intensity={3} castShadow/><directionalLight position={[-3,2,-2]} intensity={1}/><DimensionFraming config={props.config}/>{props.dimensions&&<DimensionLabels config={props.config} widthLabel={widthLabel} heightLabel={heightLabel}/>}<Suspense fallback={null}><Window {...props}/></Suspense><OrbitControls makeDefault minDistance={2} maxDistance={20} target={[0,0,0]} enablePan={false}/></Canvas>}{!lost&&props.dimensions&&<div className="dimension-overlay" aria-label="Window dimensions"><div className="dimension-anchor" ref={widthLabel}><span className="dimension-label">{props.config.width} mm</span></div><div className="dimension-anchor height-anchor" ref={heightLabel}><span className="dimension-label vertical">{props.config.height} mm</span></div></div>}</div></SceneBoundary>
}
