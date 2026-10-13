# AFKC desktop 0.2 proof run

On 13 October 2026, the actual browser-exported handoff was executed through the local pyRevit bridge in Revit 2024. The selected 1200 × 1500 mm configuration and the 900 × 1200 and 1500 × 1800 mm proof snapshots passed native geometry, material, hosting, opening and saved/reopened checks. The active project remained unchanged against each operation's baseline.

Each family has four native sweeps, 19 solid extrusions and four native void extrusions, zero FreeFormElement/DirectShape objects, 23 checked material associations and zero native warnings. The report checks 22 rendered components/assemblies, zero cladding overlap, lower outer mitre endpoints, empty glazing cavities and coarse/medium/fine plan symbols.

All 27 final native exports were inspected by the assistant: three plans, two sections and four corners per size. An export framing issue was found: template annotations extended the instance bounding box above the window. The production drawing helper now uses transformed physical frame dimensions. The isolated proof projects received that helper, all nine views were regenerated per size, saved/reopened and re-exported. Original build package hashes and the separate drawing refinement hash are retained in the [evidence record](evidence/afkc-desktop-0.2.json).

The actual report was replayed through the application's importer against its original request and accepted for all three sizes. This establishes local integration behaviour; the report remains unsigned. A fresh browser approval produces a new request identity and requires its own run.

These are fixed-size snapshots. No native parameter flex, manufacturer approval or manufactured corner/drainage certification is claimed. The user's earlier visual approval applies to the reviewed 1200 × 1500 prototype; the assistant's multi-size export inspection does not expand that approval.

Software validation: 36 unit/API/interop tests and four Python contract tests passed; client and Worker builds passed. All five browser tests passed with one worker and a 60-second timeout; the parallel Windows run hit rendering/download timeouts. Native binaries and PNGs are delivered separately from Git.
