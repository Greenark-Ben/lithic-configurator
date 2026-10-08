# LITHIC Configurator

Governed product definitions, interactive 3D configuration and verified native BIM generation.

## Prototype 0.1

A functional browser prototype of the approved Create → Review → Configure design, using an **illustrative fixed-frame window definition**. This is not manufacturer-approved geometry and does not generate a native Revit family yet.

- Add PNG/JPG/PDF references and describe a product. Files stay in memory in this browser session; they are not uploaded or interpreted. Reload clears session state.
- Explore the explicitly labelled sample definition.
- Confirm frame depth (70–200 mm prototype range) and enter its source before approval.
- Configure the supported 900 × 1200, 1200 × 1500 and 1500 × 1800 mm sizes.
- Orbit the calculated Three.js geometry, toggle dimensions and inspect an illustrative section (right members hidden).
- Choose sample finishes and download the approved definition or a JSON build request.
- The deterministic prototype helper accepts supported size pairs. No AI service is connected.
- The Revit build control is disabled until a native worker is connected. No `.rfa` output or native verification is claimed.

## Development

Node.js 22+ recommended. Dependencies are locked in `package-lock.json`.

```sh
npm ci
npm run dev
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

Vite builds static browser files to `dist/`. Serve that folder with a static HTTPS host. The proposed production address is `configurator.lithiccore.com`; no hosting provider or DNS has been configured by this commit.

## Architecture

`src/engine.ts` is the deterministic definition/configuration/geometry boundary. Geometry uses millimetres. The preview adapter converts to metres. JSON build requests carry the same nine calculated parts, definition, approval timestamp, configuration, units, engine version and explicit native status.

Prototype components are rectangular: four timber members, four exterior aluminium caps, one glazing box. A 70 mm frame face and 36 mm glazing thickness are illustrative fixtures. Before approval, 120 mm depth is a labelled preview assumption only.

The next integration must replace fixture preparation with source-grounded interpretation, versioned proposal review and a validated product definition. Native builders consume approved data through supported operations; AI output must never be executed as arbitrary code.

See [implementation roadmap](docs/ROADMAP.md).
