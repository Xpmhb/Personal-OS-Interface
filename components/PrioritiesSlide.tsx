
import React from 'react';
import { Priority } from '../types';

interface Props {
  priorities: Priority[];
  onUpdate: (updated: Priority[]) => void;
  onNext: () => void;
}

const PrioritiesSlide: React.FC<Props> = ({ priorities, onUpdate }) => {
  const toggleConfirm = (id: string) => {
    const updated = priorities.map(p => 
      p.id === id ? { ...p, confirmed: !p.confirmed } : p
    );
    onUpdate(updated);
  };

  const movePriority = (index: number, direction: 'up' | 'down') => {
    const newIdx = direction === 'up' ? index - 1 : index + 1;
    if (newIdx < 0 || newIdx >= priorities.length) return;

    const newPriorities = [...priorities];
    const temp = newPriorities[index];
    newPriorities[index] = newPriorities[newIdx];
    newPriorities[newIdx] = temp;

    // Fix ranks
    onUpdate(newPriorities.map((p, i) => ({ ...p, rank: i + 1 })));
  };

  return (
    <div className="w-full max-w-4xl animate-in zoom-in-95 duration-700">
      <header className="mb-12">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Today's Priorities
        </span>
        <h2 className="text-2xl font-medium mt-2">Ranked Objectives</h2>
      </header>

      <div className="space-y-6">
        {priorities.map((p, idx) => (
          <div 
            key={p.id}
            className={`group relative flex items-start p-8 border border-zinc-900 bg-zinc-900/20 rounded-sm transition-all hover:border-zinc-700 ${p.confirmed ? 'opacity-50' : ''}`}
          >
            <div className="flex flex-col items-center mr-8 pt-1">
              <span className="text-3xl font-bold text-zinc-700 group-hover:text-zinc-400 transition-colors">
                {idx + 1}
              </span>
              <div className="flex flex-col mt-4 space-y-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={() => movePriority(idx, 'up')} className="text-zinc-600 hover:text-white"><i className="fa-solid fa-chevron-up"></i></button>
                <button onClick={() => movePriority(idx, 'down')} className="text-zinc-600 hover:text-white"><i className="fa-solid fa-chevron-down"></i></button>
              </div>
            </div>

            <div className="flex-1">
              <h3 className="text-2xl font-medium mb-2">{p.title}</h3>
              <p className="text-zinc-400 mb-6 max-w-xl">{p.why}</p>
              
              <div className="flex flex-wrap gap-6 items-center text-sm font-medium">
                <div className="flex items-center text-zinc-500">
                  <i className="fa-solid fa-clock mr-2 text-xs"></i>
                  {p.estimatedTime}
                </div>
                <div className="flex items-center text-zinc-200">
                  <span className="text-zinc-600 mr-2 uppercase tracking-tighter text-[10px] border border-zinc-800 px-1">Action</span>
                  {p.nextAction}
                </div>
              </div>
            </div>

            <div className="ml-4 pt-1">
              <button 
                onClick={() => toggleConfirm(p.id)}
                className={`w-12 h-12 flex items-center justify-center rounded-full border transition-all ${p.confirmed ? 'bg-zinc-100 border-zinc-100 text-zinc-950' : 'border-zinc-800 text-zinc-700 hover:border-zinc-400'}`}
              >
                <i className="fa-solid fa-check"></i>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PrioritiesSlide;
