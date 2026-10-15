LITHIC AFKC Revit handoff — desktop builder 0.2.2

This package builds fixed-size snapshots of the reviewed AFKC prototype in
Revit 2024 or later. Revit and pyRevit are required. It creates fresh family
and test project documents; the active project is never edited or saved.

1. Extract the ZIP into its own folder.
2. Run Install.ps1, or copy script.py, contract.py, authoring.py, drawings.py,
   afkc-source.json and bundle.yaml into the AFKC Handoff pushbutton folder.
3. Reload pyRevit. Choose LITHIC > Native > AFKC Handoff.
4. Select this package's request.json, an empty wall-hosted Window .rft
   template and a results folder.
5. The builder creates the selected size plus 900x1200, 1200x1500 and
   1500x1800 mm, deduplicated. Each case has a separate .rfa and review .rvt.
6. Review the native plan, section and corner PNGs. Import native-report.json
   into the unchanged approved LITHIC configuration. Retain the report,
   request, family/project files and native images together.

Reviewed construction:
- Three native cladding sweeps and four native void mitre cuts retain distinct
  source head/jamb and sill sections. Thin coverage returns are prototype
  additions. No FreeFormElement or DirectShape fallback is allowed.
- Timber and separate glazing beads use native polygon extrusions.
- Three 4 mm glass panes, two empty 18 mm cavities and eight hollow aluminium
  spacer members replace the former single 48 mm glass block.
- Visible seals use one native closed sweep. Seal chemistry is unresolved.
- Timber, cladding, glass, spacer and seal materials have family parameters.
- Coarse/medium/fine plan symbols accompany 3D and section geometry. Fine
  cladding symbols derive from the actual native joined section.

Checks include sweep inputs before joining, assembled bounds/materials,
analytic volumes (bounded native join volume for the overlapping return),
cladding overlap, lower corner endpoints, empty cavity probes, material
bindings, native form counts, plan visibility, wall hosting/opening volume,
source/request metadata, warnings, and saved/reopened persistence. Nine
native drawing exports per size support visual review. A technical pass does
not replace visual acceptance. Failed outputs are not verified deliverables.

Boundary:
Width/Height have fixed formulas. Resize in LITHIC and prepare a new handoff.
Native parameter flex, manufacturer corner/drainage construction, seal
chemistry and available manufactured sizes are not verified. The accepted
visual baseline is the 1200x1500 prototype, not manufacturer approval.
Imported desktop reports are unsigned local evidence. Builder/report 0.1
packages are intentionally incompatible with this revised construction.

Host-depth correction 0.2.1:
Explicit locked centre-plane offsets prevent automatic sketch dimensions from
reshaping timber in different host walls. Every snapshot is checked in 100,
200, 300 and 500 mm walls, including all 22 hosted solids and saved/reopened
geometry and openings. Earlier 0.2 reports did not cover varying host depth.

Plan coordinates are fixed with native reference planes and alignments.
Every coarse/medium/fine line endpoint/style is checked before and after
project reopening in all four host thicknesses.

Shared parameters 0.2.2:
Five editable material fields and five user-read-only provenance fields have
permanent shared GUIDs. All ten are available in Window schedules and checked
across five placements before/after reopening. Existing downloads are not
modified; rebuild with this package for shared fields.
