# AFKC authoring specification 0.2.2

This specification captures the user's accepted 1200 × 1500 prototype and the corrections made during its native Revit review on 13 October 2026. Its machine-readable counterpart is `authoringRules` in `public/native/afkc-source.json` and the browser's `AFKC_SOURCE`.

| Component | Native form | Material parameter | Geometry rule |
| --- | --- | --- | --- |
| Timber frame | Polygon extrusions | Timber Material | Preserve source slopes, rebates and main silhouette |
| Glazing beads | Separate polygon extrusions | Timber Material | Distinct beads; horizontal beads abut jamb beads |
| Head/jamb cladding | U-shaped sweep | Aluminium Material | Preserve the distinct source section and native upper joins |
| Sill cladding | Straight sweep with void cuts | Aluminium Material | Complementary lower mitre planes |
| Coverage return | Supplemental U-shaped sweep | Aluminium Material | Reviewed prototype addition; explicit source distinction |
| Glass | Three separate extrusions | Glazing Material | 4 / 18 / 4 / 18 / 4 mm assembly; cavities are empty |
| Spacer | Eight hollow extrusions | Glazing Spacer Material | Aluminium; 7 mm radial section, 3.75 mm inset, 1 mm skin |
| Visible seals | Closed perimeter sweep | Glazing Seal Material | Simplified visible finger; elastomer chemistry unresolved |

Use editable native forms. FreeFormElement and DirectShape are forbidden for this builder, with no automatic fallback. Keep element names meaningful, distinguish glass from spacer and seal materials, and retain material parameter associations after native joins and reopening.

Main source sections remain distinct. Revit's native join of the overlapping supplemental return slightly extends the folded profile at their junction. Validate source sweep inputs before joining and inspect the resulting assembly. Preserve the original source rounding differences and record prototype additions; do not describe this as manufacturer corner fabrication.

Coarse plan graphics show the frame and overall glazing limits. Medium graphics show the assembly. Fine graphics show source frame/bead profiles, individual panes, hollow spacers, seals and the actual native joined cladding outline. Hide model forms in plan/RCP so projected head/sill geometry does not clutter these symbols. Preserve model geometry in sections and 3D. Native images need visual inspection in addition to visibility/count checks.

Width/Height remain fixed formulas. A new browser size generates a new family. Introduce parameter flex only in a separate native-tested change that covers frame, panes, spacers, seals, symbolic graphics and the host opening.

Acceptance boundaries: user visual approval applies to the reviewed prototype. Material chemistry, manufactured size availability, drainage/fastening details and manufacturer approval remain unresolved. A desktop technical pass is unsigned local evidence tied to one request and builder version.

Host placement must preserve the authored cross-sections. In implementation patch 0.2.1, explicit locked offsets from the centre plane replace automatic sketch dimensions referencing host faces. A host opening follows wall thickness, while the fixed 105 mm frame stays fixed. Validate bounds and volumes for all 22 hosted components at 100, 200, 300 and 500 mm wall thicknesses, including saved/reopened placements. This does not establish native Width/Height flex. See Autodesk’s [automatic sketch dimension guidance](https://help.autodesk.com/cloudhelp/2023/ENU/Revit-Customize/files/GUID-3A47011F-8DD7-44DC-909A-0A2B71454BE1.htm).

Plan graphics also require independent coordinate datums: orthogonal symbolic edges are aligned to dimensioned reference planes, so their coordinates cannot follow the host. Every coarse/medium/fine line endpoint and style is compared with the source family at each wall thickness, then compared again after reopening. Counts alone cannot establish stable graphics.

Ten shared type parameters use permanent GUIDs from `authoringRules.sharedParameterSchema`. Material values remain editable; provenance is visible but user-read-only. Never change GUIDs per build or reuse them for another property. Require all ten schedule fields and values before and after reopening, in addition to the existing geometry and hosting checks. See [shared parameter specification](AFKC-SHARED-PARAMETERS.md).
