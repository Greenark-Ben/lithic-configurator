# AFKC reviewed source profile prototype 0.2

AFKC remains a separate review path for Elitfönster Original Alu 100 fixed frame, drawing 61-37-F221 revision A. It is not attached automatically to an unrelated interpreted product proposal.

`src/afkc-source.ts` and `public/native/afkc-source.json` contain the same definition: original source digests, section polygons, coordinate mapping, reviewed glazing build-up and versioned authoring rules. The 1200 × 1500 visual baseline was accepted by the user on 13 October 2026. Manufacturer content remains unapproved.

Exterior depth is negative source depth in both adapters. Timber depth 105 mm, sightline 53.5 mm and glazing assembly depth 48 mm stay fixed. Timber rebates, the sloped sill and separate beads retain reviewed source-derived sections. Distinct head/jamb and sill aluminium profiles have native swept corners and lower mitre cuts; the thin coverage return and extended sill return are explicitly prototype additions.

The glazing comprises three 4 mm panes and two empty 18 mm cavities. Pane dimensions remain overall width/height minus 81 mm. Eight hollow aluminium spacer members have a simplified 7 mm radial section, 3.75 mm inset and 1 mm skin. Visible seals have their own material parameter and native closed sweep; chemistry, smaller gasket bulbs, drainage and manufacturer corner fabrication remain unresolved.

The preview exports 30 deterministic components. The native builder uses four sweeps, 19 solid extrusions and four void extrusions, validating 22 rendered components/assemblies after joining. No FreeFormElement or DirectShape fallback is permitted. Exact source polygons, transformations and limitations accompany the request. Browser/Python parity checks protect this boundary.

Session review is not manufacturer certification. The 300–3000 mm bounds are illustrative; each desktop result is a fixed-size snapshot. A new size requires a new handoff. See [authoring rules](AFKC-AUTHORING.md) and [desktop validation](REVIT-HANDOFF.md).
