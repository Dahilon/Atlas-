import { useState } from 'react';
import EventFeed from './EventFeed';

export default function Sidebar() {
  const [open, setOpen] = useState(true);
  const [tab, setTab] = useState<'feed' | 'intel'>('feed');

  return (
    <div
      className={`flex shrink-0 flex-col border-l border-slate-700 bg-slate-900/95 transition-[width] ${
        open ? 'w-96' : 'w-10'
      }`}
    >
      {open ? (
        <>
          <div className="flex items-center justify-between border-b border-slate-700 px-3 py-2">
            <div className="flex gap-1">
              <button
                type="button"
                onClick={() => setTab('feed')}
                className={`rounded px-2 py-1 text-sm ${
                  tab === 'feed' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Event Feed
              </button>
              <button
                type="button"
                onClick={() => setTab('intel')}
                className={`rounded px-2 py-1 text-sm ${
                  tab === 'intel' ? 'bg-cyan-600 text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Intel
              </button>
            </div>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-slate-500 hover:text-slate-300"
              aria-label="Collapse sidebar"
            >
              ←
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            {tab === 'feed' && <EventFeed />}
            {tab === 'intel' && (
              <div className="p-4 text-sm text-slate-500">
                AI Search / Intel panel (Phase 5). Use Event Feed for now.
              </div>
            )}
          </div>
        </>
      ) : (
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="p-2 text-slate-500 hover:text-slate-300"
          aria-label="Expand sidebar"
        >
          →
        </button>
      )}
    </div>
  );
}
