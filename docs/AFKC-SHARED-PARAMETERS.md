# AFKC shared parameter schema 1

Builder 0.2.2 uses ten shared type parameters: five editable materials and five provenance fields. Their names, GUIDs, data types and editability are recorded in `authoringRules.sharedParameterSchema`, shared by browser and native builder. GUIDs are permanent identities; never reuse them for another meaning or change them per configuration.

Materials remain associated with all 23 native form parameters. Provenance is visible and user-read-only: request SHA-256, source drawing, builder, evidence status and geometry mode. These values describe a fixed-size, unapproved manufacturer-source prototype. They do not certify manufacturer acceptance.

A fresh build creates a Window schedule containing all ten shared fields by GUID. Five placements must show the expected values, initially and after saving/reopening. Family shared identities, type binding and editability are also checked. The temporary shared definition file is isolated, and the application's original SharedParametersFilename is restored in a finally block.

Existing 0.2.1 files are retained as historical downloads. Rebuild a configuration with 0.2.2 to obtain shared parameters; this release does not edit previously downloaded RFAs or existing project instances. Geometry and Width/Height remain fixed snapshots.

On 14 October 2026, fresh 900 × 1200, 1200 × 1500 and 1500 × 1800 snapshots passed in Revit 2024. All ten shared fields and their values were checked across five placements per size before and after reopening. Native geometry, material bindings and four host-thickness cases passed with zero warnings. All 27 exported plan, section and corner images were inspected. The active project baseline and application shared-parameter file setting were preserved. See [native evidence](evidence/afkc-shared-parameters-0.2.2.json). Cloud verification is recorded separately.
