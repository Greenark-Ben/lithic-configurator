# AFKC shared parameter schema 1

Builder 0.2.2 uses ten shared type parameters: five editable materials and five provenance fields. Their names, GUIDs, data types and editability are recorded in `authoringRules.sharedParameterSchema`, shared by browser and native builder. GUIDs are permanent identities; never reuse them for another meaning or change them per configuration.

Materials remain associated with all 23 native form parameters. Provenance is visible and user-read-only: request SHA-256, source drawing, builder, evidence status and geometry mode. These values describe a fixed-size, unapproved manufacturer-source prototype. They do not certify manufacturer acceptance.

A fresh build creates a Window schedule containing all ten shared fields by GUID. Five placements must show the expected values, initially and after saving/reopening. Family shared identities, type binding and editability are also checked. The temporary shared definition file is isolated, and the application's original SharedParametersFilename is restored in a finally block.

Existing 0.2.1 files are retained as historical downloads. Rebuild a configuration with 0.2.2 to obtain shared parameters; this release does not edit previously downloaded RFAs or existing project instances. Geometry and Width/Height remain fixed snapshots.

On 14 October 2026, fresh 900 × 1200, 1200 × 1500 and 1500 × 1800 snapshots passed in Revit 2024. All ten shared fields and their values were checked across five placements per size before and after reopening. Native geometry, material bindings and four host-thickness cases passed with zero warnings. All 27 exported plan, section and corner images were inspected. The active project baseline and application shared-parameter file setting were preserved. See [native evidence](evidence/afkc-shared-parameters-0.2.2.json). Cloud verification is recorded separately.

A fresh browser request at 1200 × 1500 also passed APS Revit 2024 generation, file-hash validation and all ten initial/reopened schedule values. One paid job was submitted; recovery checks submitted none. The cloud report keeps visual approval false. [Cloud evidence](evidence/afkc-shared-parameters-cloud-0.2.2.json) records this build. A separate project test changed all five shared materials and confirmed rendered material IDs and schedule values before and after reopening, with zero warnings and the active project baseline preserved.

A delayed initial history response could overwrite the currently selected new build in the browser. A selection revision now discards that stale restoration; a dedicated browser regression verifies that a newly submitted build stays selected.

After the full desktop/cloud builds, an encoding regression in the rejected-dimension error message was corrected to ASCII. A Revit 2024 contract-only check accepted the valid request and rejected 299 mm with the corrected message. `buildPackageHashes` retain the exact full desktop-run files; `packageHashes` pin the release files, with the separate native correction evidence. Geometry/contract logic are unchanged. The cloud evidence records the exact pre-message-correction payload that executed; no second paid job was submitted for this text correction.
