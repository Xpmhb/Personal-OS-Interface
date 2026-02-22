
import React, { useState } from 'react';
import { OvernightUpdate } from '../types';

interface Props {
  updates: OvernightUpdate[];
  onNext: () => void;
}

const OvernightUpdateSlide: React.FC<Props> = ({ updates }) => {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const getStatusIcon = (status: string) => {
    switch(status) {
      case 'completed': return <i className="fa-solid fa-check-circle text-zinc-500"></i>;
      case 'blocked': return <i className="fa-solid fa-circle-exclamation text-amber-500"></i>;
      case 'in-progress': return <i className="fa-solid fa-spinner animate-spin-slow text-zinc-600"></i>;
      default: return <i className="fa-solid fa-circle text-zinc-700"></i>;
    }
  };

  return (
    <div className="w-full max-w-2xl flex flex-col animate-in fade-in duration-700">
      <header className="mb-10">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Overnight Update
        </span>
        <h2 className="text-2xl font-medium mt-2">Executive Summary</h2>
      </header>

      <div className="space-y-4">
        {updates.map((update) => (
          <div 
            key={update.id}
            onClick={() => setExpandedId(expandedId === update.id ? null : update.id)}
            className={`group p-4 border border-zinc-900 bg-zinc-900/30 hover:bg-zinc-900/60 transition-all cursor-pointer rounded-sm ${expandedId === update.id ? 'border-zinc-700 bg-zinc-900/80' : ''}`}
          >
            <div className="flex items-center">
              <span className="w-8 flex-shrink-0">{getStatusIcon(update.status)}</span>
              <p className="flex-1 text-zinc-200 font-medium leading-relaxed">
                {update.outcome}
              </p>
              <i className={`fa-solid fa-chevron-down text-zinc-700 text-xs transition-transform duration-300 ${expandedId === update.id ? 'rotate-180' : ''}`}></i>
            </div>
            
            {expandedId === update.id && update.details && (
              <div className="mt-4 pl-8 pr-4 py-3 border-t border-zinc-800 text-zinc-400 text-sm leading-relaxed animate-in slide-in-from-top-2">
                {update.details}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-12 flex items-center text-zinc-600 text-xs tracking-wider">
        <i className="fa-solid fa-clock mr-2 opacity-50"></i>
        <span>60s estimated review time</span>
      </div>
    </div>
  );
};

export default OvernightUpdateSlide;
