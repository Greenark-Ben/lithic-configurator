import * as THREE from 'three';
import type { Part } from './engine';
// Sweeps and boxes share the same millimetre build request. Only this adapter converts to metres.
export function partGeometry(part:Part):THREE.BufferGeometry{
 if(!part.sweep)return new THREE.BoxGeometry(...part.size.map(n=>n/1000) as [number,number,number]);
 const s=part.sweep,contour=s.pointsMm.map(([u,z])=>new THREE.Vector2(u,z));
 if(THREE.ShapeUtils.isClockWise(contour))contour.reverse();
 const vertices:number[]=[],n=contour.length;
 const point=(index:number)=>{const p=contour[index%n],t=index<n?0:s.lengthMm;return s.originMm.map((o,i)=>(o+s.inward[i]*p.x+s.axis[i]*t+(i===2?p.y:0)-part.position[i])/1000)};
 const determinant=new THREE.Vector3(...s.inward).cross(new THREE.Vector3(0,0,1)).dot(new THREE.Vector3(...s.axis));
 const face=(a:number,b:number,c:number)=>{for(const i of determinant<0?[a,c,b]:[a,b,c])vertices.push(...point(i))};
 for(const [a,b,c] of THREE.ShapeUtils.triangulateShape(contour,[])){face(c,b,a);face(a+n,b+n,c+n)}
 for(let i=0;i<n;i++){const j=(i+1)%n;face(i,j,j+n);face(i,j+n,i+n)}
 const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(vertices,3));geometry.computeVertexNormals();
 // A planar grain map; texture follows timber without changing section coordinates.
 const uv=[];for(let i=0;i<vertices.length;i+=3)uv.push(vertices[i]*4,vertices[i+1]*4);geometry.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));
 return geometry;
}
