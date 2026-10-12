# AFKC desktop handoff 0.1

This slice prepares an executable desktop handoff; it has not been executed in Revit in this session. There is no connected native worker. The disabled live Build Revit family action remains disabled.

For an approved AFKC configuration, Prepare Revit handoff downloads one ZIP containing the exact request, a SHA-256 manifest, source profile bundle, pyRevit command, installer and instructions. It runs in Revit 2024+ on the user's desktop using an empty wall-hosted Window template. It uses fresh family and project documents; the active project is never modified.

## Current native scope

The builder creates separate **fixed-size snapshots** for the selected configuration and the three proof sizes, deduplicated. Width/Height formulas are fixed deliberately: editable metadata must not imply geometry flex. Resizing occurs in LITHIC followed by a new handoff. Native parameter-driven flex and 2D detailing are not implemented or verified.

Eight native polygon extrusions reproduce straight source-profile sweeps exactly, plus one glazing extrusion. The template must be Windows category, OneLevelBasedHosted, have one axis-aligned host wall, built-in Width/Height type parameters and no existing forms. The selected finishes become native materials; evidence status, source drawing, builder and request hash become type metadata. An actual family opening is created in the template's host wall.

## Evidence and failure behavior

The pure Python contract rejects unsupported products, changed profiles, fixed section changes, invalid finishes, mismatched geometry and mismatched request bytes. Tests compare this implementation against actual browser build requests at six sizes and against the prior AFKC proof's recorded timber/aluminium volumes. These are software checks, not a live Revit acceptance result.

For each case the native command compares all nine forms' bounds, solid counts, volumes and material assignments. It checks schedule dimensions, provenance, wall placement, exterior orientation and wall volume removed by the opening. It saves/reopens both family and isolated project, checks persistence and collects warnings without suppression. Any exception, missing evidence or warning prevents a pass. Failed output files are not verified deliverables.

Import Revit report accepts only the exact current request digest and the complete required size set. A claimed pass must include individual native check results, zero warnings and the saved family's SHA-256. The UI labels this **unsigned desktop evidence**, not trusted remote-worker certification. A report import does not import .rfa bytes, cryptographically attest execution, or establish manufacturer approval. Changes to approval, width, height or finishes clear the report.

## Run

1. Review and approve AFKC, select size/finishes, then Prepare Revit handoff.
2. Extract it, install the pyRevit command with the included installer and reload pyRevit.
3. In Revit, LITHIC > Native > AFKC Handoff asks for request.json, the Window .rft and an output folder.
4. Import the output native-report.json in LITHIC. Retain the report and .rfa/.rvt outputs together. Inspect the selected family in Revit before project use.

First live acceptance is pending. The next native slice must establish geometry-driving parameters, host-opening flex and persistence inside one family, using a live Revit run. Do not relabel the current snapshot checks as family flex.
