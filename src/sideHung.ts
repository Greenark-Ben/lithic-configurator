import mesh from './sidehung-mesh.json';
import { SIDE_HUNG_OUTWARD_WINDOW as product } from './productCatalogue';
import type { Configuration,Definition,Part } from './engine';

export const SIDE_HUNG_INITIAL:Configuration={width:880,height:1180,interior:'timber',exterior:'graphite'};
export const SIDE_HUNG_DEFINITION:Definition={
 schemaVersion:'0.1',id:product.constructionId,productId:product.id,revision:1,product:product.name,
 operation:'side-hung-outward',frameFace:53.5,frameDepth:105,glazingThickness:48,
 provenance:{frameFace:'Source-specific frame sections; sightlines vary by member. Drawing 61-37-S221 rev A.',frameDepth:'105 mm timber depth from drawing 61-37-S221 rev A.',glazing:'Three 4 mm panes with two 18 mm cavities; source-derived prototype.'},
 sideHung:{id:'lithic-side-hung-preview/0.1',sizeMm:[880,1180],handing:'left viewed from outside',source:product.source,sourceFamilySha256:mesh.sourceFamilySha256,manufacturerApproved:false}
};
export const SIDE_HUNG_PIVOT=mesh.pivotMm as [number,number,number];
// Render-only triangulation of reviewed native sweeps/extrusions/cuts.
// Native authoring is unchanged. This asset is never a Revit build request.
export const SIDE_HUNG_PARTS:Part[]=mesh.parts.map(p=>({
 id:p.id,role:p.role as Part['role'],position:[0,0,0],size:[0,0,0],
 mesh:{verticesMm:p.verticesMm,moving:p.moving}
}));
export function openingAngleIssues(angle:number){return Number.isFinite(angle)&&angle>=0&&angle<=90?[]:['Opening angle must be between 0 and 90 degrees for this diagnostic preview.'];}
export function rotateSashPoint(point:[number,number,number],angle:number):[number,number,number]{
 if(openingAngleIssues(angle).length)throw new Error(openingAngleIssues(angle)[0]);
 const a=-angle*Math.PI/180,[px,,pz]=SIDE_HUNG_PIVOT,x=point[0]-px,z=point[2]-pz;
 return [px+x*Math.cos(a)+z*Math.sin(a),point[1],pz-x*Math.sin(a)+z*Math.cos(a)];
}
