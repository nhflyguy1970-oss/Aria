# Settings Implementation

Aria **Settings** is a first-class product: the preference **catalog and navigation layer**. Products continue owning their preference stores. Settings indexes them and deep-links.

## Product identity

| | |
|--|--|
| Operator name | **Settings** |
| Architecture term | Preference Catalog |
| Pipeline | `shared_settings_pipeline` |
| Package | `jarvis/settings_product/` |

### Owns

Settings Home, preference catalog/index, schemas, global + appearance prefs, navigation, deep links, diagnostics, profiles, Settings APIs, Mission Control preference health, Settings coach (warn-only).

### Does not own

Voice/Vision/Models/Search/Integrations/Capabilities/HA/Coding/Planner/Calendar preference **stores**, secrets, Security implementation, or a monolithic settings database.

## Mental model

| Entry | Behavior |
|-------|----------|
| **Ctrl+,** / Settings button | Opens **Settings Home** |
| **Voice & Chat** button / modal | Speak replies + Server Whisper only (Voice owns) |
| Product rows in catalog | Deep-link to product Homes |
| Secrets | Integrations |
| PIN / lock | Security view |
| MC **Runtime config** | Ops snapshot — not preference editing |

## Preference hierarchy (IA)

`global` → `appearance` → `security` → `secrets` → `products` → `environment` → `diagnostics` → `profiles`

No overlapping categories.

## Pipeline

```
Operator → Settings Home → Catalog → Search → Deep link → Product Home / store → Diagnostics → Mission Control
```

## Search integration

Settings registers a **`settings` facet** on the Search product (`retrieve_settings`). Do not build a second search engine.

## Appearance / persistence

- Server: `data/settings_product/appearance.json`, `global.json`
- Browser: `AriaUiPrefs.theme` + legacy `aria_theme` (migrated)
- Theme toggles sync to Settings appearance store

Speak replies remain Voice-owned (`/api/voice/settings`); Voice & Chat modal is the compatibility surface.

## APIs

| Path | Role |
|------|------|
| `GET /api/settings/product` | Status |
| `GET /api/settings/product/home` | Settings Home |
| `GET /api/settings/product/catalog` | Catalog |
| `GET /api/settings/product/search` | Preference search |
| `GET /api/settings/product/open` | Deep link resolve |
| `GET/POST /api/settings/product/appearance` | Appearance |
| `GET/POST /api/settings/product/global` | Global |
| `GET/POST /api/settings/product/profiles` | Profiles |
| `GET /api/settings/product/export` · `POST .../import` | Bundle |
| `POST /api/settings/product/reset` | Reset appearance/global |
| `GET /api/settings/product/diagnostics` | Diagnostics |
| `GET /api/settings/product/mission` | MC panel |

## Mission Control

- Snapshot key: `settings_product`
- Overview card: catalog/stores health
- Tab **Runtime config** (formerly “settings”): ops JSON — clearly labeled as not prefs

## Developer guide

```python
from jarvis.settings_product.catalog import search_catalog
from jarvis.settings_product.router import resolve_deep_link

hits = search_catalog("whisper")
open_payload = resolve_deep_link(hits[0]["id"])
```

To add a product preference: keep the store in the product; add a `make_preference(...)` row in `catalog.py` with a deep link.

## Operator guide

1. Press **Ctrl+,** or open **Settings**.
2. Search or filter by category.
3. Open deep links for product-owned prefs.
4. Use **Voice & Chat** only for Speak / Whisper.
5. Use Integrations for API keys; Security for PIN.

## Censored / uncensored

One Settings product. Modes may only differ in presentation/policy — never duplicate catalog or diagnostics.

## Do not build

- Monolithic settings DB
- Duplicate secrets/security/search stacks
- Auto AI security changes
- Replacing product Homes

## Tests

```bash
./venv/bin/pytest tests/test_settings_product.py tests/test_app_settings.py -q
```
