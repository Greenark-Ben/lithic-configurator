LITHIC AFSC closed source-profile and placement study 0.2

This is an isolated development study, not a browser-exportable product.
The accepted AFKC builder and public download contract are unchanged.

Configuration: module 9 x 12; 880 x 1180 mm frame; closed outward side-hung
window; intended left hinging when viewed from outside. The closed geometry
does not establish opening movement or native handedness behaviour.

Sources:
- User-supplied drawing 61-37-S221 revision A, PDF and DWG.
- User-supplied standard sizing matrix and fixing drawing 61-39-E13 A.
- Manufacturer product sheet dated 2026-06-17, linked in source.json:
  1 module = 100 mm, total frame allowance 20 mm per dimension;
  standard glazing 4/18/4/18/4 mm, with warm-edge spacers.

source.json stores explicitly selected section polygons and the original DWG
hash. Each simplification records its maximum outline deviation. Small
fillets and sketch edges under 0.9 mm are removed for native sketch creation.
Do not treat the resulting coordinates as manufacturing profiles.

build_closed.py creates fresh family and project documents, native timber
extrusions, individual aluminium sweeps with complementary native void cuts,
three glass panes, eight hollow simplified warm-edge spacer members and two
simplified glazing seals. Shared material/provenance identities reuse the
existing LITHIC schema. Width and Height are fixed formulas.

The source-specific head, sill and left/right sash profiles stay distinct.
Timber corners use simplified butt joints. Frame rail material classification,
the rounded glazing edge bite, profile interfaces and cladding corners require
review. Hardware, fixing holes, drainage and opening animation are omitted.
No FreeFormElement or DirectShape fallback is permitted.

Refinement: nativeProfiles retains the distinct outer folds, reconciles common
glazing returns by at most 0.898 mm relative to the earlier simplified sections,
and joins sill-cover DWG regions 130/138 across a 0.704 mm drawing gap. Profile
changes are recorded separately from the original simplified profiles. Native
compound sash cuts and a separate fixed-frame sill cut follow different face
widths. These are prototype joint treatments, not verified fabrication details.
The source's optional plaster-facade trim is excluded from the standard study.

Coordinates: source depth increases towards the interior. The native adapter
maps exterior depth against the template host's exterior normal; outside-left
is determined from that normal. Geometry includes the template's Default Sill
Height datum so physical placement can be checked against project sill height.
Transactions roll back on native warnings or errors, retaining diagnostics.
Material associations must survive native cuts and reopening the saved family.

The refined fine/medium symbolic plan includes standard frame and sash cladding,
three pane sections, hollow spacers and simplified glazing seals. Shared
collinear boundaries are merged. Coarse detail remains incomplete.
The diagnostic wall opening follows nominal frame width/height; installation
clearance, host wrapping and production wall junctions remain future checks.

PLACEMENT WRAPPER
For adjustable placement, run build(..., assembly_only=True) with an empty
unhosted Generic Model template; the native assembly receives the Windows
category. wrap_setback.build then nests that rigid, non-shared assembly in an
empty hosted Window family. Users edit Window Setback in INSTANCE properties:
0 mm places the front of the timber frame at the host's exterior face;
positive values recess it into the wall. Aluminium projection is excluded
from this dimension. The default review value is 50 mm. Frame Width/Height
remain fixed. Only placement flexibility is claimed, subject to proof reports.

The wrapper exposes five material type parameters associated to the nested
assembly. Immutable shared provenance is copied to the wrapper. Do not edit
or place the unhosted development assembly directly in a project. Load the
SETBACK-STUDY.rfa wrapper supplied in the review package.

Run build(application, active_document, source_path, empty_window_template,
          NEW_output_directory, existing_authoring_helpers) inside pyRevit.
It refuses an existing output directory. The supplied template must be an
empty wall-hosted Window template. The helper module is public/native/authoring.py;
its contract import must resolve to the same public/native directory.

proof.json records source data, native form types, materials, saved/reopened
family geometry, isolated wall placement/opening, host geometry comparison,
warnings and active-document state. Native images require visual inspection.
A created study is not an accepted family or a passing production release.

Next gates: review closed frame/sash geometry and 2D detail; resolve junctions;
model/verify hinge axis and assembly motion; test host thickness, handedness,
saved/reopened project behaviour and schedules; then add browser/export support.
