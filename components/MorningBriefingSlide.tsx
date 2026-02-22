
import React from 'react';
import { BriefingBlock } from '../types';

interface Props {
  blocks: BriefingBlock[];
  onNext: () => void;
}

const MorningBriefingSlide: React.FC<Props> = ({ blocks }) => {
  return (
    <div className="w-full max-w-5xl animate-in fade-in slide-in-from-right duration-700">
      <header className="mb-12">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Morning Briefing
        </span>
        <h2 className="text-2xl font-medium mt-2">External Context</h2>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {blocks.map((block, idx) => (
          <div key={idx} className="flex flex-col p-6 border-l border-zinc-800">
            <h3 className="text-zinc-500 font-bold text-xs tracking-widest uppercase mb-6">
              {block.title}
            </h3>
            <ul className="space-y-6">
              {block.insights.map((insight, i) => (
                <li key={i} className="text-zinc-100 text-lg font-light leading-relaxed">
                  {insight}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
};

export default MorningBriefingSlide;
