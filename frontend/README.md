# Global Events Dashboard

React frontend for the Global Events Risk Intelligence Dashboard. Shows map, event feed, briefs, and country drilldowns.

## Run

1. Install: `npm install`
2. Copy env: `cp .env.example .env` and set `API_URL` to your backend (default `http://localhost:8000`). Optionally set `MAPBOX_TOKEN` for the map.
3. Dev: `npm run dev` — app runs at http://localhost:1234
4. Build: `npm run build` — output in `dist/`

## Scripts

- `npm run dev` — start dev server (Parcel)
- `npm run build` — production build
- `npm run lint` — run ESLint
