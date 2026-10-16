# LITHIC product naming

Agreed direction, 16 October 2026: manufacturer model codes are source
references, not permanent LITHIC product names. This convention applies to
the forthcoming multi-product configurator, Revit family/type names, downloads
and cloud build labels. It is a naming decision, not a production release.

| LITHIC product ID | Customer-facing name | Operation | Current source model |
| --- | --- | --- | --- |
| `lithic.window.fixed` | LITHIC Fixed Window | Fixed | Elitfönster AFKC |
| `lithic.window.side-hung-outward` | LITHIC Side-Hung Outward Window | Side-hung, outward opening | Elitfönster AFSC |

These IDs identify operation classes. An exact construction definition and
revision must also be selected: different manufacturers' sections are not
interchangeable merely because they share an operation. The reviewed supplier
geometry, applicable sizing matrix and evidence remain attached to that
construction definition. Additional manufacturers must receive their own
source records and validation.

## Separate product, configuration and provenance

- Product: neutral LITHIC name, stable operation-class ID and operation.
- Construction definition: immutable versioned geometry/material rules,
  source references and evidence status.
- Configuration: width/height, finishes, handing, opening angle and placement
  setback where supported. These values do not form new product names.
- Provenance: source manufacturer, original model code, drawing/revision,
  source-file digests, construction revision and request digest.

The user interface presents the LITHIC name. A source/evidence panel may
explicitly identify Elitfönster, AFKC/AFSC and the drawing references. Renaming
does not remove attribution, establish manufacturer approval or change which
source geometry is implemented. A LITHIC name does not imply an independent
manufacturer product or a validated universal construction system.

## New Revit names

Examples for the next coordinated export revision:

```text
LITHIC-Window-Fixed-1200x1500.rfa
LITHIC-Window-SideHung-Outward-880x1180.rfa
```

Keep study/prototype status explicit in the package or evidence fields.
Side-hung research files retain a `STUDY` suffix; fixed snapshots carry the
prototype status in `LITHIC Evidence Status` and the browser review.
Use a neutral type label such as `LITHIC Side-Hung Outward 880 x 1180`.
Keep left/right handing as a parameter or verified variant where supported;
keep prototype opening-angle and setback controls separate from product
identity. If independently generated constructions could collide, add a
neutral construction revision or request-digest suffix rather than a supplier
model code. Source manufacturer/model belong in provenance fields.

## Migration and compatibility

The current browser and AFKC native/cloud/report contract contain supplier
codes in definition IDs, builder versions, family filenames and validation
rules. Those are currently coupled to request digests and proof evidence.
They are legacy compatibility identifiers, not the naming convention for new
LITHIC products.

Migrate the browser, native builder, cloud activity/report validator and output
filenames together under a new versioned contract. Verify that source metadata
and evidence still identify the exact construction. Display-name changes
alone must not silently reinterpret old requests or accept a report for a
different definition. Explicitly map legacy identifiers to their neutral
operation class plus the original immutable construction definition.

Preserve historical packages, hashes, reports and accepted Revit files under
their original names. Do not bulk-replace AFKC/AFSC in source files or earlier
evidence: those names remain valid descriptions of the source manufacturer
models. The new convention supersedes their use as customer-facing LITHIC
product identities. Historical deliverables retain their original identities. The implementation
status below records the subsequent coordinated migration.

## Implemented migration: 0.3.0

New fixed requests use catalogue product `lithic.window.fixed` and immutable
construction definition `lithic.fixed.timber-aluminium/1`. The reviewed source
manufacturer/model remains Elitfonster / AFKC. Browser labels, family filenames,
Revit type names and construction dimensions use neutral LITHIC names. Separate
immutable family text fields retain product ID, construction ID, source
manufacturer and source model. The existing shared material/provenance GUIDs
are preserved.

The native builder is `lithic-window-fixed-desktop/0.3.0`; the cloud adapter is
`lithic-window-fixed-aps-browser/0.3.0`. New cloud jobs explicitly store their
builder version. Jobs already stored before migration retain the legacy 0.2.2
validator, family filenames and source evidence. Old desktop reports are not
accepted for newly approved requests; download a fresh handoff. The historical
cloud fixture is unchanged; transformed test data is explicitly synthetic.

Fresh Revit 2024 runs at 900 x 1200, 1200 x 1500 and 1500 x 1800 passed native
geometry, host, opening, material, plan, saved/reopened and naming checks. The
actual report also passed the browser importer for its original request.
`docs/evidence/lithic-fixed-naming-0.3.0.json` pins the tested package hashes.
The new cloud payload compiles and is packaged from these same authoring files;
this migration does not claim a fresh paid APS execution of that revision.

The side-hung hosted study uses neutral outer family/type names and separate
AFSC source attribution. Its earlier head-cladding discrepancy, right-hand
controls and parent material propagation remain independent follow-up work.
