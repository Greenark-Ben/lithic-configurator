LITHIC Side-Hung Outward Window — desktop prototype 0.1.0

Revit 2024 and pyRevit are required. Width and height are fixed at 880 x 1180 mm.
Left viewed from outside; outward opening 0–90 degrees is diagnostic travel.
The manufacturer hinge mechanism, hardware and maximum opening are unverified.

1. Extract this ZIP into its own folder and run Install.ps1.
2. Reload pyRevit. Choose LITHIC > Native > Side-Hung Window Handoff.
3. Choose this package's request.json.
4. Choose an empty wall-hosted Window .rft, then Metric Generic Model.rft.
   These are installed with Revit, typically under:
   C:\ProgramData\Autodesk\RVT 2024\Family Templates\English
5. Choose a results folder. Keep Revit idle while the isolated checks run.
6. Review LITHIC-Window-SideHung-Outward-880x1180.rfa and the hosted review .rvt.
   Import native-report.json into the matching browser configuration.

The active project is not edited, saved or closed. The builder owns only fresh
family and test project documents. It checks source member volumes, native
sweeps and cuts, hosted wall openings across 48 cases, save/reopen persistence
and five material controls at three angles. The final .rfa uses your browser
finishes and starting angle. Opening Angle and Window Setback remain native
instance controls; width and height are fixed-size snapshots.

The review project includes separate instances at 0, 45 and 90 degrees.
The report is unsigned local evidence, not manufacturer approval. Retain the
entire results folder alongside request.json and manifest.json.
