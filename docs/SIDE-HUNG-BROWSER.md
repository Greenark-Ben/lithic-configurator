# LITHIC Side-Hung Outward Window — first browser preview

The Create screen now offers **Review LITHIC Side-Hung Outward Window** beside
the fixed window. Review the evidence, approve the session definition, and use
the opening slider or Closed / 30° / 45° / 90° presets in Configure.

This milestone keeps the existing Three.js viewer and live LITHIC branding.
The side-hung desktop handoff uses a separate native builder. Side-hung APS
generation is still disabled; the fixed-window cloud builder is unchanged.

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
native assembly associated with `sidehung-browser-native-refresh-01/assembly/proof.json`.
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

The native head-cladding volume check now passes: its sweep extends 10 mm
beyond each end before the same native void cuts trim it. The local cutter
bounds fully cover those extensions. No profile simplification or tolerance
relaxation was used to claim the pass. Five top-level material controls were
verified on their actual solids at 0°, 45° and 90°. Plan symbols rotate with
the sash, with separate coarse and medium/fine representations. Manufacturer
approval, hardware and maximum travel remain unverified.

## Generation boundary

Choose **Prepare Revit handoff** in Configure. Extract the ZIP, install the
separate **Side-Hung Window Handoff** pyRevit command, and select request.json,
an empty wall-hosted Window template, Metric Generic Model.rft and a results
folder. Revit 2024 is required for this verified prototype.

The native builder checks all source member volumes, 48 hosted cases,
save/reopen persistence and 15 material-control cases. The final family retains
your selected finishes and starting angle. Native Opening Angle and Window
Setback are instance controls; width and height stay fixed. The review project
includes 0°, 45° and 90° instances and coarse/medium/fine plans.

Import native-report.json into the matching approved browser configuration.
Angle and finish edits invalidate that match. Reports remain unsigned local
evidence; a technical pass is not visual or manufacturer approval.

The APS endpoint independently rejects side-hung requests. Next is a separately
validated side-hung cloud adapter and one actual cloud generation proof.
