const API_BASE = process.env.API_URL || 'http://localhost:8000';

async function fetchApi<T>(path: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(path, API_BASE);
  if (params) {
    Object.entries(params).forEach(([k, v]) => v && url.searchParams.set(k, v));
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`);
  return res.json();
}

export interface Metric {
  date: string;
  country: string;
  category: string;
  event_count: number;
  avg_tone: number | null;
  rolling_center?: number | null;
  rolling_dispersion?: number | null;
  baseline_quality?: string | null;
  baseline_method?: string | null;
  z_score?: number | null;
  risk_score?: number | null;
  reasons_json?: string | null;
  computed_at?: string | null;
  pipeline_version?: string | null;
}

export interface Spike {
  id: number;
  date: string;
  country: string;
  category: string;
  z_score: number;
  z_used?: number | null;
  delta?: number | null;
  rolling_center?: number | null;
  rolling_dispersion?: number | null;
  baseline_quality?: string | null;
  baseline_method?: string | null;
  evidence_event_ids?: string | null;
  computed_at?: string | null;
  pipeline_version?: string | null;
}

export interface BriefResponse {
  top_movers: Array<{
    date: string;
    country: string;
    category: string;
    risk_score?: number | null;
    event_count?: number;
    z_score?: number | null;
  }>;
  top_spikes: Array<{
    date: string;
    country: string;
    category: string;
    z_score?: number | null;
    z_used?: number | null;
    delta?: number | null;
  }>;
  summary: string;
}

export interface EventItem {
  id: string;
  ts: string;
  date: string;
  country: string | null;
  admin1: string | null;
  lat: number | null;
  lon: number | null;
  event_code: string | null;
  quad_class: number | null;
  avg_tone: number | null;
  source_url: string | null;
  category: string | null;
}

export async function getMetrics(params?: { country?: string; start?: string; end?: string; category?: string }): Promise<Metric[]> {
  return fetchApi<Metric[]>('/metrics', params as Record<string, string>);
}

export async function getSpikes(params?: { country?: string; category?: string; start?: string; end?: string; limit?: string }): Promise<Spike[]> {
  return fetchApi<Spike[]>('/spikes', params as Record<string, string>);
}

export async function getBrief(forDate?: string): Promise<BriefResponse> {
  return fetchApi<BriefResponse>('/brief', forDate ? { date: forDate } : undefined);
}

export async function getEvents(params?: { country?: string; start?: string; end?: string; category?: string; limit?: string }): Promise<EventItem[]> {
  return fetchApi<EventItem[]>('/events', params as Record<string, string>);
}

export async function getCountries(): Promise<{ countries: string[] }> {
  return fetchApi<{ countries: string[] }>('/countries');
}

// --- Map + combined events (MapEvent shape) ---

export type MapEventSource = 'gdelt' | 'valyu';

export interface MapEventLocation {
  latitude: number;
  longitude: number;
  placeName?: string | null;
  country?: string | null;
  region?: string | null;
}

export interface MapEvent {
  id: string;
  source: MapEventSource;
  title: string;
  summary: string;
  category: string;
  threatLevel: 'critical' | 'high' | 'medium' | 'low' | 'info';
  location: MapEventLocation;
  timestamp: string;
  sourceUrl?: string | null;
  severity_index?: number | null;
  risk_score?: number | null;
  event_count?: number | null;
}

export interface MapCountryItem {
  country: string;
  lat: number;
  lon: number;
  severity_index?: number | null;
  risk_score?: number | null;
  event_count?: number | null;
}

export interface CombinedEventsResponse {
  events: MapEvent[];
  count: number;
  sources: Record<string, number>;
}

export interface MilitaryBaseItem {
  country: string;
  baseName: string;
  latitude: number;
  longitude: number;
  type: string;
}

export async function getMap(date?: string): Promise<MapCountryItem[]> {
  return fetchApi<MapCountryItem[]>('/map', date ? { date } : undefined);
}

export async function getCombinedEvents(params?: { date?: string; sources?: string; limit?: string }): Promise<CombinedEventsResponse> {
  const p: Record<string, string> = {};
  if (params?.date) p.date = params.date;
  if (params?.sources) p.sources = params.sources;
  if (params?.limit) p.limit = params.limit;
  return fetchApi<CombinedEventsResponse>('/events/combined', Object.keys(p).length ? p : undefined);
}

export async function getMilitaryBases(): Promise<{ bases: MilitaryBaseItem[]; cached?: boolean }> {
  return fetchApi<{ bases: MilitaryBaseItem[]; cached?: boolean }>('/military-bases');
}
