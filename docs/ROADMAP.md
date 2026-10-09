# First complete product proof

## Delivered in prototype 0.1

React/TypeScript/Vite interface; React Three Fiber preview; pure deterministic geometry functions; evidence-required sample approval; three bounded configurations; JSON handoff; meaningful engine tests. Uploaded references are session-only. No backend, credentials, live AI or Revit worker.

## Source-grounded creation integration

Implemented: image/PDF/description API, structured proposal schema, runtime evidence checks, explicit unknowns, five-dimension review, revisioned session approval, approved-size-only geometry and server-only credentials. Automated tests use a mocked provider. Live connection and source acceptance testing are pending. See [details](INTERPRETATION.md).

## Remaining product proof

1. Retrieve and inspect the earlier AFKC definition, profiles, source drawings and saved-family results. Establish an evidence-backed baseline before carrying manufacturer geometry forward.
2. Define a versioned product schema for profile polygons, component placement, relationships, units, hosting, supported choices, sources and explicit unknowns. Publish a JSON Schema and validate independently in browser/server/native adapters.
3. Add server-side OpenAI interpretation, using image inputs and Structured Outputs. Proposals remain unapproved. Check units, geometry and constraints independently; schema compliance alone does not establish correctness.
4. Implement revisions and immutable approval snapshots. Altering source evidence, profiles, relationships or supported rules invalidates approval; choosing an already permitted configuration does not.
5. Add authenticated persistence and company isolation. Do not place service credentials in the frontend. Uploads must be permission-scoped and retain original evidence.
6. Implement durable build jobs with pinned definition/configuration/engine/builder versions, content identity, retries, explicit failures and receipt records. Avoid running native jobs in browser HTTP requests.
7. Connect the existing local Revit/MCP workflow using validated supported operations. Keep manufacturer profile authoring separate from this illustrative box geometry. Save, reopen and place outputs; verify dimensions, materials, opening/hosting, parameters and 2D representation.
8. Replace/port native operations to a C# Revit API worker and evaluate APS Automation after local acceptance. Do not assume the pyRevit bridge can execute unchanged in APS.
9. Deliver native `.rfa` only when the relevant checks have passed. Include definition identity, configuration, engine/builder versions and verification results in a receipt. Equivalent replay means equivalent governed results, not necessarily byte-identical RFA files.

## Hosting

Proposed address: configurator.lithiccore.com. Web app and backend deploy separately from the local Windows/Revit worker. Select the hosting provider and configure previews, secrets, production DNS and rollback before a production launch. No hosting or DNS changes in this first commit.
