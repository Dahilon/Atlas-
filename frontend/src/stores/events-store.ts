import { create } from 'zustand';
import type { MapEvent } from '../api';

const THREAT_LEVEL_PRIORITY: Record<string, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
  info: 4,
};

export interface EventFilters {
  searchQuery: string;
  threatLevels: Set<string>;
  categories: Set<string>;
  sources: Set<string>;
}

const defaultFilters: EventFilters = {
  searchQuery: '',
  threatLevels: new Set(),
  categories: new Set(),
  sources: new Set(),
};

export function applyFiltersToEvents(events: MapEvent[], filters: EventFilters): MapEvent[] {
  let out = events;
  if (filters.searchQuery.trim()) {
    const q = filters.searchQuery.trim().toLowerCase();
    out = out.filter(
      (e) =>
        e.title?.toLowerCase().includes(q) ||
        e.summary?.toLowerCase().includes(q) ||
        e.location?.placeName?.toLowerCase().includes(q) ||
        e.location?.country?.toLowerCase().includes(q)
    );
  }
  if (filters.threatLevels.size > 0) {
    out = out.filter((e) => filters.threatLevels.has(e.threatLevel));
  }
  if (filters.categories.size > 0) {
    out = out.filter((e) => e.category && filters.categories.has(e.category));
  }
  if (filters.sources.size > 0) {
    out = out.filter((e) => filters.sources.has(e.source));
  }
  return [...out].sort(
    (a, b) =>
      (THREAT_LEVEL_PRIORITY[a.threatLevel] ?? 5) - (THREAT_LEVEL_PRIORITY[b.threatLevel] ?? 5)
  );
}

interface EventsStore {
  events: MapEvent[];
  filters: EventFilters;
  selectedEvent: MapEvent | null;
  setEvents: (events: MapEvent[]) => void;
  setFilters: (f: Partial<EventFilters> | ((prev: EventFilters) => EventFilters)) => void;
  setSearchQuery: (q: string) => void;
  toggleThreatLevel: (level: string) => void;
  toggleCategory: (cat: string) => void;
  toggleSource: (source: string) => void;
  clearFilters: () => void;
  selectEvent: (event: MapEvent | null) => void;
}

export const useEventsStore = create<EventsStore>((set) => ({
  events: [],
  filters: defaultFilters,
  selectedEvent: null,
  setEvents: (events) => set({ events }),
  setFilters: (f) =>
    set((s) => ({
      filters: typeof f === 'function' ? f(s.filters) : { ...s.filters, ...f },
    })),
  setSearchQuery: (q) =>
    set((s) => ({ filters: { ...s.filters, searchQuery: q } })),
  toggleThreatLevel: (level) =>
    set((s) => {
      const next = new Set(s.filters.threatLevels);
      if (next.has(level)) next.delete(level);
      else next.add(level);
      return { filters: { ...s.filters, threatLevels: next } };
    }),
  toggleCategory: (cat) =>
    set((s) => {
      const next = new Set(s.filters.categories);
      if (next.has(cat)) next.delete(cat);
      else next.add(cat);
      return { filters: { ...s.filters, categories: next } };
    }),
  toggleSource: (source) =>
    set((s) => {
      const next = new Set(s.filters.sources);
      if (next.has(source)) next.delete(source);
      else next.add(source);
      return { filters: { ...s.filters, sources: next } };
    }),
  clearFilters: () => set({ filters: defaultFilters }),
  selectEvent: (event) => set({ selectedEvent: event }),
}));

// Selector for filtered events (derived in component via getState or subscription)
export function getFilteredEvents(store: EventsStore): MapEvent[] {
  return applyFiltersToEvents(store.events, store.filters);
}
