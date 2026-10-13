# AFKC host-depth correction 0.2.1

A 1200 × 1300 family looked correct in the Family Editor but lost its intended timber jamb shape in a project using a 300 mm wall. The solids remained present: automatic sketch dimensions referenced the host faces and reshaped timber as wall thickness changed. A four-wall diagnostic reproduced changes at 100, 300 and 500 mm; the earlier 200 mm proof host matched the template and concealed this issue.

The builder now replaces supported wall-depth automatic dimensions with explicit locked offsets from the family centre plane. Unsupported references are recorded and cannot bypass the full placed geometry checks. Revit native sweeps/extrusions and material associations are retained. All 22 component bounds and volumes, plus the wall opening, must remain valid in 100, 200, 300 and 500 mm hosts, both on placement and after reopening the project.

Revit 2024 checks passed for 1200 × 1300, 900 × 1200, 1200 × 1500 and 1500 × 1800 snapshots: 16 host cases, zero warnings and an unchanged active-project baseline. Each family has 37 explicit depth constraints, four sweeps, 19 solid extrusions and four void extrusions. The actual report passed the current application's importer against its original request. The [evidence record](evidence/afkc-host-depth-0.2.1.json) retains source and native file hashes.

The original user's request was preserved and combined with the corrected production modules/manifest for this native run; a separate current browser handoff capture passed. This is not an assertion that an unmodified older ZIP contains the fix. Interior/exterior views of the corrected 1200 × 1300 family in a 300 mm wall were inspected. Existing user project and open family documents were not modified.

Validation: 36 unit/API/interop tests, four Python contract tests, client/Worker builds and the built-Worker handoff smoke check passed. A real browser 0.2.1 ZIP capture passed. Full browser checks run in CI. Width/Height remain fixed; host-depth independence does not establish native size flex or manufacturer approval. Earlier builder reports cannot establish this host-depth check.
