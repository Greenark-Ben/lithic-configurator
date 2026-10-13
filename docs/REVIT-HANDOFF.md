# AFKC desktop handoff 0.2.1

The AFKC preview and desktop builder share a versioned reviewed construction definition. Prepare Revit handoff exports the exact browser request, SHA-256 manifest, source bundle, native authoring/drawing modules, pyRevit command and installer. The live Build Revit family action remains disabled; no remote worker is connected.

## Reviewed construction

The 1200 × 1500 mm visual baseline was accepted by the user on 13 October 2026. This is prototype visual acceptance, not manufacturer approval. The definition records the source drawing 61-37-F221 rev A and its original PDF/DWG digests, while distinguishing reviewed coverage additions from source profiles.

- Native U-shaped head/jamb cladding sweep, separate sill sweep and supplemental coverage-return sweep, with four native void extrusions for the lower mitres.
- Native closed seal sweep; no FreeFormElement or DirectShape fallback.
- Source-derived timber extrusions and separate beads.
- Three 4 mm glass panes, two empty 18 mm cavities, and eight hollow aluminium spacer extrusions.
- Five family material parameters, preserving finish choices for timber and cladding.
- Coarse/medium/fine plan symbols; fine cladding outlines come from the actual joined native section. Three plan, two section and four corner views are exported per size.

[AFKC authoring specification](AFKC-AUTHORING.md) records the modelling rules, naming and simplification boundaries. `afkc-source.json` embeds the same versioned rules used by the browser definition. A rule change must version the source, engine and builder together and receive fresh native evidence.

## Fixed-size scope

Each run builds the selected size and the 900 × 1200, 1200 × 1500 and 1500 × 1800 proof sizes, deduplicated. Width/Height formulas deliberately remain fixed. Resizing occurs in LITHIC followed by a new handoff. These are separate snapshots; no native parameter flex is claimed. The 300–3000 mm browser range is illustrative, not manufacturer availability.

## Evidence and failure behaviour

The independent Python contract rejects unsupported products, old builder/profile versions, changed source sections or source data, invalid finishes, altered browser geometry and changed request bytes. Browser and Python parts must match exactly.

Native checks compare 22 rendered components/assemblies. Sweep inputs are checked before joining. Most volumes use exact polygon formulae; the joined overlapping head/jamb coverage return uses a documented range from ideal boolean union to the sum of its mitred inputs, because Revit's native join extends the adjoining folded return. This is explicit native join behaviour, not a widened tolerance applied to every component.

The builder also checks four sweep/19 solid extrusion/four void extrusion counts, absence of FreeForm/DirectShape, material associations, plan visibility, empty cavity probes, zero cladding overlap and matching lower outer mitre endpoints. It verifies schedule dimensions, request/source metadata, hosting, exterior orientation, wall opening removal, warnings and saved/reopened family/project persistence. All work occurs in fresh documents; the active project is not edited or saved. Any missing check, exception or warning prevents a technical pass.

Native PNG exports support visual review. Exporting an image or having zero warnings does not establish drawing quality or manufacturer verification. Native parameter flex, manufacturer corner/drainage details and seal chemistry remain unresolved.

Report import requires builder/report 0.2, the exact current request digest, all required cases, authoring counts, drawing records, zero warnings and family digests. Configuration changes clear the displayed report. Imported reports remain **unsigned local evidence**; importing a report does not import its RFA or attest execution cryptographically. Version 0.1 reports cannot establish acceptance of the revised construction.

## Run

1. Review AFKC, select size/finishes and choose Prepare Revit handoff.
2. Extract the ZIP and run Install.ps1; reload pyRevit.
3. In LITHIC > Native > AFKC Handoff, choose request.json, an empty wall-hosted Window RFT and a results folder.
4. Inspect the native plan, section and corner exports, then import native-report.json into the unchanged configuration. Retain the native files and evidence together.

Integration validation and native run results are recorded with the change; they must not be relabelled as native flex or manufacturer acceptance.

[Revit 2024 proof run](AFKC-NATIVE-PROOF.md) records the three tested snapshots and drawing refinement provenance.

## Host-depth correction

Builder 0.2.1 replaces wall-face automatic sketch dimensions with locked offsets from the family centre plane. Version 0.2 was checked in a 200 mm host only; a user placement in a 300 mm wall revealed that Revit reshaped the timber sketches. Every snapshot now requires all 22 component bounds/volumes and the wall opening to pass in 100, 200, 300 and 500 mm hosts, both initially and after project reopening. Reports from earlier builders cannot establish this pass. Unsupported automatic dimension references are recorded; they cannot bypass the complete hosted geometry checks.
