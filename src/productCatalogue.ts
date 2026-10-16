// Product identity is independent of a supplier's construction reference.
export const FIXED_WINDOW = {
 id:'lithic.window.fixed',name:'LITHIC Fixed Window',
 constructionId:'lithic.fixed.timber-aluminium/1',
 operation:'fixed',source:{manufacturer:'Elitfönster',model:'AFKC',drawing:'61-37-F221 rev A'}
} as const;
// Browser snapshot and native study share this identity; browser generation is not enabled.
export const SIDE_HUNG_OUTWARD_WINDOW = {
 id:'lithic.window.side-hung-outward',name:'LITHIC Side-Hung Outward Window',
 constructionId:'lithic.side-hung-outward.timber-aluminium/1',
 operation:'side-hung-outward',source:{manufacturer:'Elitfönster',model:'AFSC',drawing:'61-37-S221 rev A'}
} as const;
