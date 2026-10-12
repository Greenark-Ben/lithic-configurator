LITHIC AFKC Revit handoff — desktop builder 0.1

This package contains your reviewed configuration and a fixed builder. It does
not contain a generated .rfa yet. Revit 2024 or later and pyRevit are required.
The builder runs only in fresh family and test documents, preserving your active
project. It does not connect to the internet or execute text from the request.

1. Extract this ZIP into a folder.
2. With pyRevit installed, run Install.ps1 (right-click > Run with PowerShell).
   Alternatively copy script.py, contract.py, afkc-source.json and bundle.yaml to:
   %APPDATA%\pyRevit\Extensions\LITHICNativeHandoff.extension\LITHIC.tab\Native.panel\AFKC Handoff.pushbutton
3. Reload pyRevit or restart Revit. Open a blank project so the ribbon is available.
4. Click LITHIC > Native > AFKC Handoff. Choose request.json from this extracted
   package, an empty wall-hosted Window .rft template and an output folder.
5. The tool builds your selected size and the 900x1200, 1200x1500 and 1500x1800
   checks (without duplicates), saving a separate .rfa and test .rvt for each.
6. Import native-report.json from the results folder into LITHIC using Import
   Revit report. Keep the .rfa/.rvt files with that report. Review the selected
   family in Revit before using it in a project.

Current boundary:
- Fixed-size snapshots. Width/Height have fixed formulas so editing metadata
  cannot silently misrepresent unchanged geometry. Resize in LITHIC and rebuild.
- Eight native polygon extrusions represent the straight frame sweeps; glazing
  is one solid. No imported mesh. Materials follow your selected finishes.
- Native checks compare dimensions, solid volumes, material assignments, wall
  hosting, exterior orientation, opening volume, warnings and saved/reopened files.
- A passed desktop report is local, unsigned evidence, not an independent or
  manufacturer certification. Failed cases remain failed; warnings are not hidden.
- No native parameter flex, 2D detailing, seals, drainage or manufacturer size
  certification is claimed. These source profiles retain their prototype status.

If the tool stops, retain the error/report and share it with Ben's LITHIC thread.
Do not treat an output .rfa from a failed report as verified.
