# LITHIC Side-Hung Outward Window — first browser preview

The Create screen now offers **Review LITHIC Side-Hung Outward Window** beside
the fixed window. Review the evidence, approve the session definition, and use
the opening slider or Closed / 30° / 45° / 90° presets in Configure.

This milestone keeps the existing Three.js viewer and live LITHIC branding.
It does not connect the side-hung product to the fixed-window Revit builder.

## Supported preview

- Product identity: `lithic.window.side-hung-outward`.
- Construction identity: `lithic.side-hung-outward.timber-aluminium/1`.
- Overall frame: **880 × 1180 mm**, module 9 × 12 with 20 mm overall allowance.
- Outward opening, left viewed from outside. Angle 0–90° is diagnostic travel.
- Natural timber / white interior and graphite / white aluminium preview finishes.
- Three separate 4 mm panes, two 18 mm cavities, eight spacers and two seals.

Width and height are locked. The snapshot must not be stretched to advertise
other sizes. Manufacturer sizing rules, right-hand control, hardware mechanism
and maximum opening have not been approved by this browser milestone.

## Geometry provenance

`src/sidehung-mesh.json` is render-only triangulation read from the closed
native assembly associated with `afsc-opening-study-20261015-05/assembly/proof.json`.
The read-only extractor is `native/afsc-opening/export_browser_mesh.py`; it accepts
the application, active document, assembly report, output path and closed-builder
helpers. Extraction opened that saved family in the background, closed it
without saving, and confirmed the active project snapshot was unchanged.

It contains 29 parts: 21 moving sash parts and eight fixed frame parts. The
source Revit solids remain native sweeps and extrusions with native cuts.
Web meshes are not used to author FreeFormElement or DirectShape in Revit.

Native millimetres `(X,Y,Z)` map to browser millimetres `(-X,Z,Y)`. This is a
proper rotation, preserving triangle winding. The browser's outside-left pivot
is `(-411.6464609802715, 0, 15.7772291928652)` mm. A negative rotation about
browser Y opens the complete sash towards exterior +Z. The fixed frame stays put.
Only the renderer converts millimetres to metres.

Supplier references remain provenance: Elitfönster Original Alu 100, source model
AFSC, drawing **61-37-S221 rev A**. The source family SHA256 is embedded in the
asset and approved preview definition. The supplier model is not the product ID.

The native head-cladding analytic volume check remains unresolved. This preview
preserves that evidence status and does not establish manufacturer approval.
Open-sash plan symbols and parent material propagation remain separate native work.

## Generation boundary

Side-hung cloud generation and desktop handoff are unavailable in this release.
`createBuildRequest` rejects side-hung definitions, the desktop handoff requires
the fixed profile, and the backend independently compares requests against its
fixed-window contract before any APS submission. Existing fixed-window builds,
downloads and history remain on their existing contract.

Next: resolve outstanding native checks and material propagation, then connect a
separate side-hung generation contract and prove its browser-to-Revit output.
