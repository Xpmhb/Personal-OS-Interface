
import React, { useState } from 'react';
import { InboxItem } from '../types';

interface Props {
  items: InboxItem[];
  onResolve: (id: string) => void;
  onNext: () => void;
}

const InboxSlide: React.FC<Props> = ({ items, onResolve }) => {
  const [activeId, setActiveId] = useState<string | null>(null);

  const pendingItems = items.filter(i => !i.resolved);

  if (pendingItems.length === 0) {
    return (
      <div className="text-center animate-in zoom-in duration-500">
        <div className="w-16 h-16 bg-zinc-900 rounded-full flex items-center justify-center mx-auto mb-6">
          <i className="fa-solid fa-check text-zinc-500"></i>
        </div>
        <h2 className="text-2xl font-light text-zinc-100">Inbox Cleared</h2>
        <p className="text-zinc-500 mt-2">All immediate decisions have been resolved.</p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-3xl animate-in fade-in duration-700">
      <header className="mb-12">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Inbox & Approvals
        </span>
        <h2 className="text-2xl font-medium mt-2">Clear Friction</h2>
      </header>

      <div className="space-y-4">
        {pendingItems.map((item) => (
          <div key={item.id} className={`border border-zinc-900 rounded-sm overflow-hidden transition-all ${activeId === item.id ? 'bg-zinc-900/40 ring-1 ring-zinc-700' : 'bg-zinc-900/10'}`}>
            <div 
              onClick={() => setActiveId(activeId === item.id ? null : item.id)}
              className="p-6 cursor-pointer flex items-center justify-between hover:bg-zinc-900/30 transition-colors"
            >
              <div>
                <span className="text-[10px] font-bold tracking-widest text-zinc-600 uppercase mb-1 block">{item.source}</span>
                <h3 className="text-lg font-medium text-zinc-100">{item.subject}</h3>
                <p className="text-sm text-zinc-500 mt-1 line-clamp-1">{item.summary}</p>
              </div>
              <i className={`fa-solid fa-chevron-right text-zinc-800 transition-transform ${activeId === item.id ? 'rotate-90' : ''}`}></i>
            </div>

            {activeId === item.id && (
              <div className="px-6 pb-6 pt-2 animate-in slide-in-from-top-4 duration-300">
                <div className="bg-zinc-950 p-6 rounded-sm border border-zinc-800">
                  <span className="text-[10px] font-bold text-zinc-600 tracking-widest uppercase block mb-4">Recommended Response</span>
                  <p className="text-zinc-300 italic mb-8 leading-relaxed">
                    "{item.draftResponse}"
                  </p>
                  
                  <div className="flex items-center space-x-4">
                    <button 
                      onClick={() => onResolve(item.id)}
                      className="bg-zinc-100 text-zinc-950 px-6 py-2 text-sm font-bold rounded-sm hover:bg-white transition-all"
                    >
                      Approve & Send
                    </button>
                    <button className="text-zinc-500 hover:text-zinc-300 px-4 py-2 text-sm font-medium">Revise</button>
                    <button className="text-zinc-500 hover:text-zinc-300 px-4 py-2 text-sm font-medium">Defer</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default InboxSlide;
