# Build Plan: Combined Map + Feed (GDELT + Valyu)

This document is the **single source of truth** for building the combined Global Events Risk Intelligence experience: **our GDELT pipeline + Valyu search/AI** on **one Mapbox map** with **sidebar event feed**, **country panel** (Valyu context + our drilldown), **AI search**, and **extra layers** (military bases, entity search, deep research). It references the **Global Threat Map** reference app (e.g. at `Downloads/globalthreatmap-main`) for exact map behavior, layer configs, and UI patterns. See **Section 11** for a direct index into that repo’s files.

**Related:** `ROADMAP_LIVE_MAP_AI.md` covers Step 2 (map), Step 4 (AI search), etc.; this doc is the **detailed implementation guide** that combines GDELT + Valyu, map, feed, and country panel in one build.

**Our app today:** Backend `http://localhost:8000` (FastAPI); frontend Vite dev `http://localhost:5173` (or 5174); `VITE_API_URL` in frontend points at the API.

---

## 1. Reference vs our stack

| Aspect | Reference (globalthreatmap) | Our app |
|--------|-----------------------------|--------|
| **Framework** | Next.js 16 (App Router) | Vite + React (no Next) |
| **Backend** | Next API routes (server-side) | FastAPI (Python) |
| **Map** | Mapbox GL + react-map-gl, dark-v11 | To add: Mapbox + react-map-gl |
| **Events source** | Valyu Search API + AI classification | GDELT (events table) + Valyu (to add) |
| **State** | Zustand (map-store, events-store) | React state in App.tsx; can add Zustand |
| **Styles** | Tailwind v4, Geist Mono | Tailwind v4, existing slate/cyan |

**Important:** We keep our **FastAPI** backend. Valyu is integrated via **Python** (httpx calls to Valyu API), not valyu-js. Valyu API shape is inferred from the reference `lib/valyu.ts` and their API routes.

---

## 2. Unified data model

### 2.1 MapEvent (frontend)

All items on the map and in the feed use one shape. GDELT events and Valyu search results are normalized to this.

```ts
// frontend: types or api.ts
type MapEventSource = "gdelt" | "valyu";

interface MapEventLocation {
  latitude: number;
  longitude: number;
  placeName?: string;
  country?: string;
  region?: string;
}

interface MapEvent {
  id: string;
  source: MapEventSource;
  title: string;
  summary: string;
  category: string;
  threatLevel: "critical" | "high" | "medium" | "low" | "info";
  location: MapEventLocation;
  timestamp: string; // ISO
  sourceUrl?: string;
  severity_index?: number | null;
  risk_score?: number | null;
  event_count?: number;
}
```

- **GDELT:** We derive `threatLevel` from `severity_index` or `risk_score` (e.g. &lt;20 → low, 20–40 → medium, 40–70 → high, ≥70 → critical; null → info). `title`/`summary` can be built from category + country + date or left minimal; `location` from event lat/lon or country centroid.
- **Valyu:** Use their `ThreatEvent` shape (category, threatLevel, location, title, summary, sourceUrl) and map 1:1 to `MapEvent` with `source: "valyu"`.

### 2.2 Threat level palette (reference)

From `globalthreatmap-main/types/index.ts`:

```ts
threatLevelColors = {
  critical: "#ef4444",
  high: "#f97316",
  medium: "#eab308",
  low: "#22c55e",
  info: "#3b82f6",
}
```

We can reuse these hex values or switch to our own palette (e.g. teal/amber/red); define in one place (e.g. `frontend/src/constants/colors.ts`).

### 2.3 Severity for heatmap (reference)

From `threat-map.tsx`: they map threat level to a numeric severity for the heatmap:

```ts
function getSeverityValue(threatLevel: string): number {
  const values = { critical: 5, high: 4, medium: 3, low: 2, info: 1 };
  return values[threatLevel] || 2;
}
```

We do the same: store `severity` (1–5) on each GeoJSON feature so the heatmap layer works.

---

## 3. Backend (FastAPI) – what to add

### 3.1 Env and Valyu

- **Env:** `VALYU_API_KEY` (required for Valyu). Optional: `OPENAI_API_KEY` for AI classification/location extraction if we replicate that.
- **Valyu:** Valyu exposes a REST API. Reference uses `valyu-js` (Node). We call Valyu from Python with `httpx`. Endpoints we need (from reference):
  - **Search:** POST body with query, options (max_results, start_date, excluded_sources). Returns `{ results: [{ title, url, content, publishedDate, source }] }`.
  - **Answer:** POST body with query (for country conflicts). Returns synthesized answer + sources.
  - **Deep research / entities:** Document in “Phase 6” below; same idea (proxy from FastAPI).

Check Valyu’s public API docs for exact paths and payloads; reference uses paths like `/v1/answer`, `/v1/search` (or similar) and OAuth proxy for token mode. For self-hosted we use API key only.

### 3.2 New/modified routes

| Route | Method | Purpose |
|-------|--------|--------|
| `GET /map` | GET | Per-country aggregates for one date: country, lat, lon, severity_index, risk_score, event_count. Uses country centroids. |
| `GET /events/combined` | GET | Combined list for map+feed: GDELT events (with threat level derived) + Valyu events (from our proxy). Query params: `date`, `sources=gdelt,valyu`, optional `limit`. |
| `POST /valyu/events` | POST | Proxy to Valyu search: body `{ queries?: string[], accessToken?: string }`. Returns `{ events: MapEvent[] }` (Valyu results normalized to MapEvent). |
| `GET /valyu/countries/conflicts` | GET | Proxy to Valyu “answer” for country: `?country=XX`. Returns `{ country, past: { conflicts, sources }, current: { conflicts, sources } }`. Optional streaming later. |
| `GET /valyu/military-bases` | GET | Return static list of US/NATO bases (reference: `lib/valyu.ts` `getMilitaryBases()`). Can be JSON file or hardcoded in Python; 1h cache. |
| `POST /search` or `POST /chat` | POST | AI search: body `{ query: "..." }`. LLM extracts filters, runs our APIs + optional Valyu, returns summary + events/spikes/links. (Phase 5.) |

### 3.3 Country centroids

- Add `backend/app/data/country_centroids.json` (or Python dict in `backend/app/country_centroids.py`). Format: `{ "US": [38.0, -97.0], "GB": [55.4, -3.4], ... }`. Used by `GET /map` to attach lat/lon to each country.

### 3.4 Map response shape

```json
[
  {
    "country": "US",
    "lat": 38.0,
    "lon": -97.0,
    "severity_index": 45.2,
    "risk_score": 62.1,
    "event_count": 1200
  }
]
```

One object per country for the requested date (from `daily_metrics` aggregated by country: max risk, max severity_index, sum event_count).

### 3.5 Combined events response shape

```json
{
  "events": [ /* MapEvent[] */ ],
  "count": 42,
  "sources": { "gdelt": 30, "valyu": 12 }
}
```

Backend either merges in Python or returns two arrays (`gdelt`, `valyu`) and frontend merges; in both cases frontend gets a single `MapEvent[]` for map and feed.

---

## 4. Frontend – map (reference behavior)

Our current “Map” is country chips (`MapView.tsx`). Replace with a **full-screen Mapbox map** matching the reference.

### 4.1 Dependencies

From `globalthreatmap-main/package.json`:

- `mapbox-gl`: ^3.18.0
- `react-map-gl`: ^8.1.0

Add to our frontend:

```bash
npm install mapbox-gl react-map-gl
```

Env: `VITE_MAPBOX_TOKEN` (or `VITE_MAPBOX_TOKEN`). Mapbox token from https://account.mapbox.com/access-tokens/.

### 4.2 Map style

Reference uses:

```ts
mapStyle="mapbox://styles/mapbox/dark-v11"
```

We use the same for “exact same type of map.” Viewport: reference default `{ longitude: 0, latitude: 20, zoom: 2 }`.

### 4.3 Layers (reference: threat-map.tsx)

- **Events source:** One GeoJSON `Source` with `data={geojsonData}` (FeatureCollection of points). Each feature: `properties: { id, title, category, threatLevel, severity (1–5), timestamp }`, `geometry: Point([lng, lat])`.
- **Clustering:** `cluster={true}`, `clusterMaxZoom={14}`, `clusterRadius={50}`.
- **Layers:**
  - **clusterLayer:** circle layer, filter `["has", "point_count"]`, paint by `point_count` (blue → yellow → orange → red) and radius steps (12, 16, 20, 24). Reference lines 27–47.
  - **clusterCountLayer:** symbol layer for count text.
  - **unclusteredPointLayer:** circle layer, filter `["!", ["has", "point_count"]]`, `circle-color` by `["get", "threatLevel"]` mapping to threatLevelColors, radius 8.
  - **heatmapLayer:** heatmap type, weight by `severity`, intensity by zoom; heatmap-color gradient blue → yellow → orange → red. Reference lines 89–124.

Toggle heatmap and clusters with map controls (reference: `map-store` `showHeatmap`, `showClusters`).

### 4.4 Map controls (reference: map-controls.tsx, threat-map)

- **NavigationControl, GeolocateControl, ScaleControl** (reference: top-right / bottom-right).
- **Heatmap / Clusters toggles** (reference: TimelineScrubber or similar; we add two buttons).
- **Military bases toggle** (reference: one button, `toggleMilitaryBases`).

### 4.5 Click behavior (reference: handleMapClick)

- **Cluster:** get cluster expansion zoom, easeTo cluster center with that zoom.
- **Unclustered point:** set `selectedEvent` to the event, show Popup with EventPopup content.
- **Empty map (no feature):** reverse geocode (Mapbox Geocoding API) to get country; set `selectedCountry` + `selectedCountryCode` and open **Country panel** (Valyu context + our drilldown).
- **Military base / entity:** show their popups as in reference (base name, type; entity name, place).

### 4.6 Country highlight (reference)

When a country is selected and loading, show fill layer using Mapbox country boundaries (`mapbox://mapbox.country-boundaries-v1`), filter by `iso_3166_1 === selectedCountryCode`, red fill with blinking opacity (e.g. 0.15 ↔ 0.4). Outline layer same filter.

### 4.7 Popups

- **Event popup:** Same content as reference `EventPopup`: title (link), threat badge, summary (expandable), location, time, category/keywords, source link.
- **Military base popup:** Base name, type (US/NATO), country.
- **Entity location popup:** Entity name, place, country.

### 4.8 Files to create/change (map)

| File | Action |
|------|--------|
| `frontend/src/components/ThreatMap.tsx` (or replace `MapView.tsx`) | New full-screen Mapbox map: viewport state, GeoJSON source, cluster + unclustered + heatmap layers, click handlers, country highlight, Popups. Copy layer config from reference `threat-map.tsx` (lines 27–124, 334–398, 586–612). |
| `frontend/src/components/MapControls.tsx` | New: heatmap toggle, clusters toggle, military bases toggle. |
| `frontend/src/stores/map-store.ts` | New (Zustand): viewport, showHeatmap, showClusters, showMilitaryBases, militaryBases, flyTo, toggles. Mirror reference `stores/map-store.ts`. |
| `frontend/src/stores/events-store.ts` | New (Zustand): events (MapEvent[]), filteredEvents, selectedEvent, filters (category, threatLevel, searchQuery, severity/risk bands), applyFilters, setEvents, selectEvent. Mirror reference `stores/events-store.ts` but add severity/risk and source filter. |
| `frontend/src/constants/colors.ts` | threatLevelColors, optional severity bands. |
| `frontend/package.json` | Add mapbox-gl, react-map-gl, zustand. |

---

## 5. Frontend – sidebar event feed

### 5.1 Layout

Reference: full-screen map + right sidebar (collapsible, ~w-96). Sidebar has two tabs: “Live Feed” and “Intel” (entity search). We do the same: **Map** fills the screen, **Sidebar** with “Event Feed” and optionally “Intel” / “AI Search.”

### 5.2 Event feed content (reference: EventFeed, FeedFilters, EventCard)

- **Header:** “Event Feed”, event count.
- **Filters:**
  - Search input (search in title/summary/location).
  - Threat level: badges critical / high / medium / low / info (toggle).
  - Category: badges (our categories + Valyu categories normalized).
  - **Extra for us:** Severity band (e.g. 0–20, 20–40, 40–70, 70+), Risk band, Source (GDELT / Valyu / Both).
- **List:** ScrollArea of event cards. Each card: icon by category, title, threat badge, summary line, location, time; click → select event and fly to location on map (reference EventCard uses `flyTo` from map-store).

### 5.3 Data flow

- **Fetch:** On load and refresh, call `GET /events/combined` (and optionally `GET /valyu/events` if we keep them separate). Put result into `events-store.setEvents(mapEvents)`.
- **Filter:** Client-side (or server params) by category, threatLevel, searchQuery, severity, risk, source. Sort by threat priority then date (reference `THREAT_LEVEL_PRIORITY`).
- **Map:** Map reads `filteredEvents` from store and builds GeoJSON from it.

### 5.4 Files

| File | Action |
|------|--------|
| `frontend/src/components/Sidebar.tsx` | New: collapsible sidebar, tabs “Event Feed” | “Intel” (or “AI Search”). |
| `frontend/src/components/feed/EventFeed.tsx` | New: header, count, FeedFilters, ScrollArea, list of EventCards. |
| `frontend/src/components/feed/FeedFilters.tsx` | New: search input, threat badges, category badges, severity/risk bands, source filter, clear. |
| `frontend/src/components/feed/EventCard.tsx` | New: card for MapEvent, threat color, category icon, click → selectEvent + flyTo. |
| `frontend/src/components/map/EventPopup.tsx` | New: popup content for selected event (title, threat, summary, location, link). |

---

## 6. Country panel (Valyu context + our drilldown)

### 6.1 Behavior (reference: CountryConflictsModal)

On country click (reverse geocode → country code):

- Open a **modal or side panel**.
- **Tabs:** “Context” (Valyu) | “Metrics” | “Spikes” | “Evidence”.
- **Context tab:** Historical + current conflicts from Valyu. Reference: two sections, “Current” (red theme) and “Historical” (blue theme), each with Markdown content and sources (links). We call `GET /valyu/countries/conflicts?country=...` and render the same.
- **Metrics tab:** Our existing drilldown metrics for that country (from `GET /metrics?country=XX`).
- **Spikes tab:** Our spikes for that country (`GET /spikes?country=XX`).
- **Evidence tab:** Our events for that country (`GET /events?country=XX` or reuse Evidence panel content).

### 6.2 Loading and highlight

While loading country data, show country fill with blinking opacity (reference). On close, clear selected country and hide highlight.

### 6.3 Files

| File | Action |
|------|--------|
| `frontend/src/components/CountryPanel.tsx` (or CountryConflictsModal) | New: modal/panel with tabs Context | Metrics | Spikes | Evidence. Context = fetch Valyu conflicts, render markdown + sources. Other tabs = existing API calls and our existing UI (or reuse CountryDrilldown content). |
| `frontend/src/components/CountryContextTab.tsx` | New: current + historical conflict sections, markdown, source links. |

---

## 7. Military bases layer

### 7.1 Data (reference: lib/valyu.ts getMilitaryBases)

Reference uses a **static list** of bases: `{ country, baseName, latitude, longitude, type: "usa" | "nato" }`. We do not call Valyu for this; we host the same list.

- **Backend:** `GET /valyu/military-bases` (or `GET /military-bases`) returns that list. Implement in Python: copy the array from reference `lib/valyu.ts` (lines 821–~900+) into a JSON file or Python list; 1h cache optional.
- **Frontend:** Fetch on map mount; store in map-store. When `showMilitaryBases` true, add a GeoJSON source and two layers (reference): circle layer (military-bases-circle) by type (usa=green, nato=blue), symbol layer for base name. Click → popup with base name, type, country.

### 7.2 Reference layer config

From `threat-map.tsx`: `militaryBaseCircleLayer`, `militaryBaseLabelLayer` (ids `military-bases-circle`, `military-bases-labels`). Use same paint (green/blue by type).

---

## 8. Entity search and deep research (extra layers)

### 8.1 Entity search (reference: EntitySearch, api/entities)

- User enters entity name → backend calls Valyu entity API → returns profile with locations (lat, lon, placeName, country).
- Frontend: show entity locations as **purple markers** on map (reference: entityLocationsData, entityLocationLayer). Click → popup with entity name and place.
- **Backend:** `POST /valyu/entities` or `GET /valyu/entities?q=...` proxying to Valyu; return `{ locations: GeoLocation[], ... }`.

### 8.2 Deep research (reference: api/deepresearch)

- User requests deep research for an entity → backend creates async task (Valyu deep research API), returns taskId.
- Frontend polls `GET /valyu/deepresearch/{taskId}` until done; then show report / CSV / PDF links.
- **Backend:** `POST /valyu/deepresearch`, `GET /valyu/deepresearch/{taskId}`. Document exact Valyu endpoints from their API.

---

## 9. AI search (natural language)

### 9.1 Flow

- User types a query (e.g. “protests in India”, “regime change”).
- **Backend** `POST /search` or `POST /chat`: send query to LLM (OpenAI/Claude), get structured filters (country, category, date range, keywords). Run our APIs (events, metrics, spikes) and optionally Valyu search with those filters. LLM summarizes and returns `{ summary, events, spikes, links }`.
- **Frontend:** Search box (in sidebar or header); on submit show results in feed or a “Search results” section and optionally fly to first result on map.

### 9.2 Env

`OPENAI_API_KEY` or similar; keep key server-side only.

---

## 10. Build order (logical sequence)

1. **Backend – map and centroids**
   - Add country centroid lookup (JSON or module).
   - Add `GET /map?date=...` (per-country aggregates, with lat/lon).

2. **Backend – Valyu proxy (minimal)**
   - Env VALYU_API_KEY. Add `POST /valyu/events` (or GET) that calls Valyu search, normalizes to MapEvent-like list.
   - Add `GET /valyu/countries/conflicts?country=XX`.
   - Add `GET /military-bases` (static list + cache).

3. **Backend – combined events**
   - Add `GET /events/combined` that merges GDELT events (from DB, with derived threatLevel) and Valyu events (from Valyu proxy). Return unified list.

4. **Frontend – deps and stores**
   - Install mapbox-gl, react-map-gl, zustand.
   - Add map-store (viewport, heatmap, clusters, military bases, flyTo).
   - Add events-store (events, filteredEvents, filters, applyFilters).
   - Add MapEvent type and threatLevelColors.

5. **Frontend – map**
   - New ThreatMap (or replace MapView): Mapbox map, dark-v11, viewport from store. Single GeoJSON source from filteredEvents; cluster + unclustered + heatmap layers (copy reference layer config). Click: cluster expand, point → popup, empty → country panel. Country highlight when selected.

6. **Frontend – popups and controls**
   - EventPopup, military base popup. MapControls: heatmap, clusters, military bases toggles.

7. **Frontend – sidebar and feed**
   - Sidebar with Event Feed tab. EventFeed: fetch combined events, FeedFilters (threat, category, severity, risk, source, search), EventCard list; click card → selectEvent + flyTo.

8. **Frontend – country panel**
   - Country panel/modal: Context (Valyu conflicts), Metrics, Spikes, Evidence. Fetch conflicts on open; other tabs use existing APIs.

9. **Frontend – layout**
   - App layout: full-screen map + sidebar (no tab bar covering map). Header with title and refresh. Optional: Brief / Movers / Drilldown as separate tabs or secondary views.

10. **AI search**
    - Backend POST /search; frontend search box, display results in feed and map.

11. **Entity search and deep research**
    - Backend Valyu proxy for entities and deep research; frontend Entity search tab and deep research trigger.

12. **Polish**
    - Colors, remove redundant comments, minimal UI. Optional: auto-pan (timeline scrubber) like reference.

---

## 11. Reference file index (globalthreatmap-main)

Use these for copy-paste or behavior reference:

| What | Path |
|------|------|
| Map component, layers, click, popups | `components/map/threat-map.tsx` |
| Map layer definitions (cluster, heatmap, unclustered, military, entity) | `components/map/threat-map.tsx` lines 27–239 |
| Map sources and layer order | `components/map/threat-map.tsx` lines 586–612 |
| Country highlight, reverse geocode | `components/map/threat-map.tsx` lines 544–584, 460–486 |
| Event popup content | `components/feed/event-popup.tsx` |
| Map controls | `components/map/map-controls.tsx` |
| Map store | `stores/map-store.ts` |
| Events store and filters | `stores/events-store.ts` |
| Feed filters (threat, category) | `components/feed/feed-filters.tsx` |
| Event card (click → flyTo) | `components/feed/event-card.tsx` |
| Country conflicts modal (tabs, current/past) | `components/map/country-conflicts-modal.tsx` |
| Types (ThreatEvent, threatLevelColors) | `types/index.ts` |
| Valyu search, answer, military bases | `lib/valyu.ts` |
| Events API (Valyu search + classification) | `app/api/events/route.ts` |
| Country conflicts API | `app/api/countries/conflicts/route.ts` |
| Military bases API | `app/api/military-bases/route.ts` |
| Sidebar (tabs Feed | Intel) | `components/sidebar.tsx` |
| Main page layout | `app/page.tsx` |
| useEvents hook | `hooks/use-events.ts` |

---

## 12. Acceptance criteria (summary)

- [ ] **Map:** Full-screen Mapbox (dark-v11), events as points with clustering and heatmap; colors by threat level; click point → popup, click empty → country panel.
- [ ] **Feed:** Sidebar with event list and filters (threat, category, severity, risk, source, search); click event → fly to and show popup.
- [ ] **Country panel:** Context (Valyu historical + current), Metrics, Spikes, Evidence (our data).
- [ ] **Data:** Combined events from GDELT + Valyu; no duplicate event IDs; threat level and location on every item.
- [ ] **Military bases:** Toggle layer, green/blue markers, click → popup.
- [ ] **AI search:** Natural language query → summary + events/spikes/links; results in feed/map.
- [ ] **Entity search + deep research:** Optional; document in Phase 6 and implement after map/feed/country panel.

This doc is the single place to build from; use the reference repo for exact layer configs, types, and API shapes.

---

## 13. How we combine both data sources (different perspectives)

- **GDELT** gives a **structured, quantitative** view: event counts by (date, country, category), Goldstein/tone, and our **data-science layer** (rolling baselines, z-scores, severity_index, risk_score, spikes). So you see *where* and *how much* activity and risk, with clear metrics and baselines.
- **Valyu** gives a **search/AI** view: real-time search results, AI-classified threat level and category, and **narrative context** (e.g. country conflicts – historical and current). So you see *what’s being reported* and *how it’s described*, with human-readable summaries and sources.

**Combined:**

1. **Map + feed:** One list of “events” = GDELT events (with derived threat level from our severity/risk) **plus** Valyu search results (with their threat level). Same map and same sidebar feed; each item has `source: "gdelt" | "valyu"` so you can filter or compare.
2. **Country panel:** One place: **Context** tab = Valyu (historical + current conflicts); **Metrics / Spikes / Evidence** = our GDELT pipeline. So for any country you get both the “story” (Valyu) and the “numbers” (our drilldown).
3. **Filters:** In the feed you can filter by source (GDELT / Valyu / Both), threat level, category, severity/risk bands. That gives different perspectives: e.g. “only GDELT” for our risk view, “only Valyu” for breaking-news view, or both for full picture.
4. **AI search (later):** Natural-language query → LLM extracts filters → we run **both** our APIs (events, metrics, spikes) **and** Valyu search → one summary with links to both GDELT evidence and Valyu sources.

So: **GDELT = quantitative + baselines + risk**; **Valyu = qualitative + context + search**. Combining them in one map, one feed, and one country panel gives both perspectives in a single UI.
