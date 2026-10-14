# AFKC browser generation

The existing LITHIC renderer and configuration UI remain the preview. A server-only APS adapter generates a fixed-size Revit 2024 family from the exact approved AFKC request. No browser viewer migration is required.

The first APS proof, work item `6d628e3ec81049c3a12a4676091dfd39`, produced a 1200 × 1500 family. Its 22 measured component bounds and volumes matched the accepted desktop baseline exactly. Native forms, material associations, four hosted-wall thickness cases and saved/reopened plan graphics passed. Nine review views were subsequently exported from the downloaded RVT in desktop Revit and inspected. This establishes the first configuration, not every permitted size or manufacturer approval.

## Boundaries

- `/api/revit/status` reports configuration availability, not an authenticated build result.
- POST `/api/revit/jobs` validates the full request against the canonical reviewed AFKC definition, locks submissions, persists the record, uploads private inputs and submits one work item.
- GET `/api/revit/jobs/:id` polls the existing work item and checks the returned report, native authoring counts, all four hosted-wall cases, plan signatures, warnings and model file hashes.
- Family, report and complete model-evidence downloads are enabled only after those checks pass. Presigned APS URLs, upload keys, access tokens and credentials remain server-side.
- Conditional storage writes prevent duplicate submissions and stale polling responses from overwriting checked results. An uncertain submission is retained for support rather than automatically retried.
- Records and files are scoped to the trusted Sites visitor identity. Service-access QA uses a separate namespace. This deployment remains owner-private behind Sites dispatch; public access needs its own reviewed authorization and usage policy.
- Cloud technical acceptance remains distinct from visual review. Every returned report keeps `visualReviewPassed=false`, `manufacturerApproved=false` and `nativeParameterFlex=false`.

## Deployment

Runtime secrets: `APS_CLIENT_ID`, `APS_CLIENT_SECRET`, configured through native Sites environment tools. Existing OpenAI runtime settings are preserved. Generated code and the hosting manifest contain no credentials. The `BUCKET` storage binding owns persistent build records and downloaded results; temporary APS inputs/results use an app-owned transient OSS bucket.

Build the adapter with `dotnet build cloud/Lithic.Afkc.Cloud.csproj -c Release`, then `python cloud/package.py --template <licensed empty English Metric Window.rft>`. RevitAPI.dll is a local build reference, not distributed in the bundle. The private generated payload and licensed template are ignored by Git and embedded only into the server build, never served through public asset routes. `cloud/artifacts-manifest.json` pins their hashes.

The adapter retains the desktop geometry and checking functions, replaces pyRevit DB imports, omits desktop dialogs and does not export PNGs headlessly. It creates native review views in the returned verification RVT. Geometry changes require new native evidence; a successful image-free job is not visual certification.

The server uses Fetch, Web Crypto and a small object-store interface. It does not depend on Lovable or Core's database and can be moved during the planned backend cutover.

## Browser build evidence

On 14 October 2026, the published browser workflow generated and downloaded the 900 × 1200, 1200 × 1500 and 1500 × 1800 timber/graphite presets. All three reports passed their 22 component and four hosted-wall cases, including reopening and plan signatures. Downloaded RFA hashes matched the reports. Measured component volumes matched the accepted desktop baselines exactly. This confirms these tested presets; the wider illustrative range and manufacturer approval remain separate.

CI builds without licensed private payloads retain the desktop workflow and report cloud generation unavailable. Set `LITHIC_REQUIRE_CLOUD_PAYLOAD=1` for deployments that must fail rather than omit private generation inputs. Browser QA uses one worker because SwiftShader contexts competing in parallel caused local timeouts; six sequential browser tests passed.

## Build history, recovery and usage

The browser lists persistent, user-scoped build records from R2, including builds created before this update. Select a history entry to inspect its size, finishes and status or download a previously checked RFA. Every result retains its build reference and report; choosing history does not change the current configuration or imply visual approval.

The private deployment permits ten APS work-item submission attempts per UTC day across all visitor/service namespaces. A conditional storage counter reserves allowance immediately before submission. Cached results, polling and downloads consume no allowance. Uncertain submissions consume allowance conservatively. Attempts made before this counter was deployed are not retrospectively counted. This cap limits submissions, not a monetary budget or Autodesk processing charges.

“Check existing build” polls the confirmed APS work item and can retrieve and re-check its result after a temporary transfer failure. It never posts another work item. Native failures and unverified results remain blocked from download. A checking lease can be recovered after two minutes. A submission with no returned APS identifier stays held for support; automatically clearing its lock could duplicate a paid job. Temporary Autodesk objects can expire, so recovery is not guaranteed after their retention period. Verified copies already stored in R2 remain downloadable.

The CI native contract now compares the five authoring/source files against the accepted desktop 0.2.1 package hashes, allowing LF/CRLF checkout conversion. Native source changes require a new evidence baseline. Software/browser tests verify delivery behavior; they do not replace execution in Revit or visual review.
