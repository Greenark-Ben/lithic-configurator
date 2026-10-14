# AFKC material quantity audit

On 14 October 2026, Revit 2024 material takeoffs were checked in isolated copies of three desktop snapshots (900 × 1200, 1200 × 1500, 1500 × 1800), the downloaded 1200 × 1500 cloud model, and the separate shared-material edit model. Each contains five placements, including the four 100/200/300/500 mm host-thickness cases. Four baseline input hashes match their generation reports; the edited-material case is explicitly a diagnostic project.

All five audit cases passed. Across 25 windows, 125 element/material pairs were checked initially and again after saving/reopening. Each window had 22 native solids and five material roles. Material volume matched the sum of native solid volumes, and material area matched the sum of all solid face areas. Every takeoff row matched the corresponding native API quantities. Initial/reopened values matched exactly, with zero warnings and the active project baseline preserved. No production builder, family geometry, browser UI or cloud runtime was changed, and no new APS job was submitted.

The audit uses real Window material takeoffs with Mark, Material: Name, Material: Volume and Material: Area. Volumes and areas are displayed in m³ and m² with 0.000000001 precision for the proof, so small seal and sheet-metal quantities do not round to zero. API/solid comparisons use relative tolerance 0.000001, with a minimum 1 mm³ or 1 mm²; displayed rows use 1.1 mm³ and 0.01 mm² allowances. Source geometry was independently checked in the preceding native generation evidence; this audit checks how Revit reports its material quantities.

For a single 1200 × 1500 timber/graphite snapshot:

| Material role | Modelled volume (litres) | Total solid surface (m²) |
| --- | ---: | ---: |
| Timber | 23.672725 | 2.314581 |
| Cladding aluminium | 0.631858 | 0.908962 |
| Glass panes | 19.054332 | 9.588078 |
| Spacer aluminium | 0.461656 | 0.924048 |
| Glazing seal | 0.028513 | 0.065132 |

These are quantities of the simplified model. Material: Area includes the surfaces and edges of all three glass panes; 9.588078 m² is not the clear glazed opening area or the overall 1.8 m² window size. Likewise, total aluminium surface is not a procurement sheet area. Manufacturing waste, purchased stock lengths, coating quantities, gasket production details, seal chemistry, manufacturer approval and native parameter flex are outside this proof.

To review, open one delivered `*-material-quantities.rvt` in its own Revit session/tab and inspect `LITHIC material quantity proof`. TSV exports preserve full names and numerical values. Audit marks Q1–Q5 exist only in the separate proof models; they were never applied to the user's project. The audit helper is desktop-only and does not add these takeoffs automatically to newly generated families.

[Compact native evidence](evidence/afkc-material-quantities-20261014.json) records exact input/output digests and per-window values. The full result, saved proof models and schedules are delivered separately. Autodesk documents the [material quantity APIs](https://help.autodesk.com/cloudhelp/2014/CHS/Revit/files/GUID-101E6FBF-D776-4CFA-A40D-D2DB7C0BDE9A.htm) and notes that quantities can be approximate in some situations; acceptance here is bounded to the tested native snapshots.
