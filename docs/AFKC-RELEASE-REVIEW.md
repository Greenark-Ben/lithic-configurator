# AFKC release review — 14 October 2026

PR #5 establishes the accepted desktop authoring baseline; PR #6 layers private APS browser delivery on that branch. Both remain open for human review. The native source files still match the accepted 0.2.1 package hashes. This update adds a CI check of those hashes rather than changing geometry.

Reviewed boundaries: native sweeps/extrusions and mitre cuts, separate panes and cavities, material associations, host depth constraints, fresh document creation/closing, checked model downloads and private visitor storage. Existing evidence covers the recorded desktop cases and three browser cloud presets. Ben has additionally confirmed the 1200 × 1300 browser result visually in Revit; this is user acceptance, not a new independently measured cloud report.

The browser delivery review identified three gaps: only the latest local build was reachable, result retrieval failures had no safe recovery action, and submissions had no daily allowance. The implementation adds persistent history, recovery of confirmed APS jobs without resubmission and a shared ten-attempt UTC daily cap. No active Revit project or native authoring source is modified.

Remaining boundaries: fixed-size snapshots, manufacturer/source prototype status, manual visual approval, owner-private audience. Uncertain submissions without an APS identifier require support; native failures cannot be bypassed. The cap is not a monetary guarantee. Wider product/size validation, public authorization, operator tools and Core integration remain later work.

PR review here is a focused implementation/evidence assessment, not a formal independent approval. Neither PR is merged by this task.
