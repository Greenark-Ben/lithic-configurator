# AFSC opening mechanism study

Research branch only. The accepted closed AFSC package remains unchanged.
This is an 880 x 1180 mm fixed-size snapshot with a native, instance-based
`Opening Angle` control. It is not a production handoff/export builder.

## Native control proved in Revit 2024

The complete 21-part sash is a non-shared, workplane-based nested family.
Its timber, aluminium sweeps and native void cuts, three panes, eight hollow
spacer members and two glazing seals rotate together. The eight fixed frame
parts remain stationary. No FreeFormElement or DirectShape is authored.

A reference line starts at the source-observed hinge-axis candidate. Its
endpoint is driven by native length dimensions with sine/cosine formulas;
the moving family attaches to its vertical workplane. The API-created angular
dimension experiment did not flex reliably and was rejected, with its native
errors retained in local evidence. The retained endpoint rig passes closed
and 90-degree positions without an angular-dimension singularity.

Family flex was checked at 0, 15, 30, 45 and 90 degrees and returned to zero.
After save/reopen, 0, 15, 45 and 90 degrees and return to zero passed again.
Separate project instances at 0, 45 and 90 degrees retained all 29 solids
after project save/reopen. The tested family/project documents had no warnings.
The user's active project was preserved and restored after image export.

## Source correction and motion screening

The earlier closed prototype reused the wider head cladding rail at the jambs.
Native motion screening exposed clashes. The opening study instead uses thin
metal region 93 at the left jamb and region 91 at the right. Adjacent regions
74/75 are air, not metal. The source-specific head and sill profiles remain
distinct. Small front-face endpoint reconciliations are recorded in the input.

Read-only Revit solid transforms/Boolean intersections screened 12 positions
per hand: 0, 0.25, 0.5, 1, 2, 5, 10, 15, 30, 45, 60 and 90 degrees.
All 24 fixed-frame cases and 72 wall cases reported no overlaps above the
1 mm3 reporting threshold, with no Boolean errors. Wall assumptions: 300 mm
thickness, nominal 880 x 1180 opening, setbacks 0/50/100 mm, no installation
allowance. This is sampled analysis, not continuous clearance certification.
The right-hand analysis reflects native solids; a right-hand authored control
has NOT yet been verified.

## Unresolved before another finished prototype

- The fixed head cladding's native corner cut fails the independent analytic
  volume check. The review rig uses the initial corrected-frame variant:
  actual 75,513.025 mm3 versus expected 76,862.214 mm3. Local cutter experiments
  reduce the difference but do not pass; the tolerance has not been relaxed.
  Source-profile simplification and sequential cuts did not resolve it.
- The hinge axis is a DWG observation, not a manufacturer-approved mechanism.
  Hardware heights, hinge travel, seal compression and maximum opening are
  unverified. Use 0..90 degrees only as the tested diagnostic range.
- Wall-hosted opening control, `Window Setback` combined with opening,
  material-control propagation through the additional nesting, and authored
  right-hand/mirror behavior still require proof. Existing closed proofs
  do not automatically establish these behaviors for this opening study.
- Plan graphics currently use native geometry for the mechanism study;
  the accepted closed symbolic plan must not be reused as an open-sash plan.
- Width/Height flex, hardware, drainage, fixings and web/APS integration
  are not part of this milestone.

## Reproduction

1. Use `native/afsc/build_closed.py` with `assembly_only=True` to build two fresh
   component families from `source-study.json`, setting
   `openingStudyGeometryGroup` to `Moving Sash` or `Fixed Frame` respectively.
2. Preserve both component `proof.json` files in `sash/` and `frame/` folders.
3. Call `build_native.build(application, active_document, component_base,
   hinge_reference_path, empty_generic_template_path, fresh_output, builder)`.
4. Run `screen_motion.run` separately on a full assembly proof. Its result
   cannot approve the native control or override a failed source volume check.

Requires a locally licensed Revit 2024 template and the existing desktop
authoring helpers. Templates and manufacturer source files are not distributed.
All tools use isolated documents and fresh output directories.
