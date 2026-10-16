# LITHIC Configurator

Evidence-reviewed product definitions, interactive configuration and a staged native BIM handoff.

## Current proof

- Add images/PDFs and a description; the connected interpretation service proposes a bounded fixed timber window with exterior aluminium caps. Review dimensions and evidence before session approval.
- Resize approved windows from 300–3000 mm in the browser. Original evidence remains separate from selected size; these limits are not manufacturer availability claims.
- Review LITHIC Fixed Window, using the separate Elitfonster AFKC source construction: stepped timber rebates, folded aluminium, 105 mm depth, 53.5 mm face and reviewed 4 / 18 / 4 / 18 / 4 mm glazing assembly. Profile polygons and drawing evidence remain unapproved manufacturer content.
- Orbit, section, change finishes and export the same deterministic geometry as a build request.
- LITHIC Fixed Window can prepare a Revit desktop handoff ZIP, executed with pyRevit in Revit 2024+. Builder 0.3.0 makes native sweep/void cladding, separate panes/spacers/beads/seals, material parameters and LOD plan graphics as fixed-size .rfa snapshots, with isolated test .rvt files and drawing exports. The APS adapter uses the same native authoring functions; native dimensional flex is not claimed.
- Import a matching unsigned desktop report. Size/finish/approval changes invalidate the displayed report. It is local execution evidence, not independent certification.

The approved off-white/forest-green interface uses React, TypeScript, Vite and React Three Fiber. Browser review and references are session-only; reload clears them.

## Development

Node.js 22+ and Python 3 are used for checks. Dependencies are locked in package-lock.json.

```sh
npm ci
npm run dev
npm test
npm run test:native-contract
npm run build:worker
npm run test:e2e
```

Live image interpretation uses a server-only OPENAI_API_KEY. Do not put credentials in client code or commit local .env files. The deployed owner-only Site already has its runtime secret; no new key is needed for the desktop handoff.

## Boundaries

AI interprets. The engine decides. The browser produces validated data; the native command is fixed reviewed code and never executes a prompt or code embedded in a request. Both adapters use millimetres and validate the same reviewed source profiles independently.

See [AFKC authoring rules](docs/AFKC-AUTHORING.md), [source profiles](docs/SOURCE-PROFILES.md), [interpretation](docs/INTERPRETATION.md), [desktop handoff](docs/REVIT-HANDOFF.md) and [roadmap](docs/ROADMAP.md).

## Product identity

Customer-facing models are LITHIC Fixed Window and LITHIC Side-Hung Outward
Window. Supplier model codes are retained only as source/construction records
and legacy compatibility identifiers. Fixed-window requests and new native
exports use the versioned neutral 0.3.0 contract. Side-hung remains a native
study and is not yet enabled in the web configurator. See
[product naming](docs/PRODUCT-NAMING.md).
