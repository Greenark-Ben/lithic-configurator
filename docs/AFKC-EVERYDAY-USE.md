# AFKC everyday Revit use audit

PR #5 and PR #6 were merged into main on 14 October 2026. Both main CI runs passed. This audit tests the downloaded 1200 × 1500 timber/graphite cloud result in isolated Revit 2024.3 documents; it does not change the released authoring source or browser.

## Native evidence

Five variants passed before and after saving/reopening: baseline, facing flip, reassignment of all five material parameters, left/right mirrored wall/window assemblies and front/back mirrored wall/window assemblies. Each variant contains five instances, including 100, 200, 300 and 500 mm hosts. This yields 50 instance checks and 1,100 component checks against the accepted 22-part geometry, plus exact coarse/medium/fine plan signatures, opening volumes, host relationships, material assignments and fixed Width/Height values. No warnings remained in the accepted cases.

Actual window schedules contain Family and Type, Mark, Width, Height and Sill Height, with five identifiable rows per model. Values and table contents persisted after reopening. Native review exports cover plans at 1:10, 1:20 and 1:50, elevations at 1:20 and 1:50, and head/sill sections at 1:10. Elevation markers added by the audit are hidden in clean plan exports. PNG exports fit the view to the image; physical printed scale has not been verified.

The evidence summary is in `docs/evidence/afkc-everyday-use-20261014.json`. Full JSON, five isolated RVTs, schedules and native PNGs are retained in the task's final output package. The accepted input RFA/RVT hashes were rechecked after the audit and remain unchanged.

## Observed boundaries

- Window-only API mirror attempts failed with Revit's error: “Can't mirror an instance without its host.” A failure preprocessor captured that error and rolled back, retaining all five source windows. Successful mirror evidence includes both walls and their windows; it does not establish standalone window-only mirroring. This is an observed Revit 2024 API boundary, not a general claim about every Revit UI mirror operation. See Autodesk's [MirrorElements reference](https://help.autodesk.com/cloudhelp/2026/ENU/Revit-API-MainReference/files/html/bb533c52-171a-85f9-8896-c7bb661e129f.htm).
- `CanFlipFacing` is true; `CanFlipHand` is false in the released fixed-window family. An experimental horizontal control enabled hand flipping but did not remove the host requirement. That experimental family is not released.
- The five material parameters are editable and bound, but absent from Revit's available window-schedule fields. Making material and provenance fields schedulable through stable shared parameters is the next functional improvement. It requires a versioned parameter schema and new native/cloud evidence, not a silent change to the accepted baseline.
- Fixed-size snapshots, manufacturer prototype status and manual visual acceptance remain unchanged. Material reassignment is not native dimension flex.

## Active document state

Every accepted audit run preserved its own active-document before/after snapshot. Across the longer session, however, the original project's modified flag changed from false to true; its element count remained 4,893. The cause of this between-run change is not established. No audit transaction, family reload or save was directed at the active project, and its current unsaved state was retained. Do not interpret per-run snapshots as proof that no user or application state changed anywhere in the session.

## Reuse

`native/everyday_check.py` is a desktop-only pyRevit helper. Call `run(application, active_document, input_folder, fresh_output_folder, native_root)` with a hash-verified cloud report/RFA/RVT for the specific 1200 × 1500 case. Optional scenario names restrict reruns. It loads the accepted builder's function definitions without running its interactive main, includes host walls in mirror selections, captures and rolls back native errors, closes its own documents without saving them over the inputs, and records persistence separately from visual review. Use a new results folder; failed or intermediate runs are diagnostic evidence, not accepted models.
