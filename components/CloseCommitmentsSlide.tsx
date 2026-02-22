
import React, { useEffect, useState } from 'react';
import { BriefingData } from '../types';
import { gemini } from '../services/geminiService';

interface Props {
  data: BriefingData;
  journalNote: string;
  onExit: () => void;
}

const CloseCommitmentsSlide: React.FC<Props> = ({ data, journalNote, onExit }) => {
  const [robotCommitments, setRobotCommitments] = useState<string[]>(data.robotCommitments);

  useEffect(() => {
    const fetchAICommitments = async () => {
      const pTitles = data.priorities.map(p => p.title);
      const commitments = await gemini.generateCommitments(pTitles);
      setRobotCommitments(commitments);
    };
    fetchAICommitments();
  }, [data.priorities]);

  return (
    <div className="w-full max-w-5xl animate-in zoom-in-95 duration-1000">
      <header className="mb-16">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Final Alignment
        </span>
        <h2 className="text-4xl font-light text-zinc-100 mt-4 leading-tight">Briefing Concluded.</h2>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
        <div>
          <h3 className="text-zinc-500 font-bold text-[10px] tracking-widest uppercase mb-6 border-b border-zinc-800 pb-2">
            Your Commitments
          </h3>
          <ul className="space-y-4">
            {data.priorities.map((p) => (
              <li key={p.id} className="flex items-start">
                <i className={`fa-solid fa-circle-check mr-4 mt-1 ${p.confirmed ? 'text-zinc-200' : 'text-zinc-800'}`}></i>
                <span className={`text-lg font-light ${p.confirmed ? 'text-zinc-100' : 'text-zinc-500'}`}>
                  {p.title}
                </span>
              </li>
            ))}
            {journalNote && (
              <li className="flex items-start italic text-zinc-500 text-sm mt-8 pt-8 border-t border-zinc-900">
                <i className="fa-solid fa-quote-left mr-4 opacity-30"></i>
                <span>{journalNote}</span>
              </li>
            )}
          </ul>
        </div>

        <div>
          <h3 className="text-zinc-500 font-bold text-[10px] tracking-widest uppercase mb-6 border-b border-zinc-800 pb-2">
            AI Operating Commitments
          </h3>
          <ul className="space-y-6">
            {robotCommitments.map((c, i) => (
              <li key={i} className="flex items-start">
                <div className="w-1.5 h-1.5 bg-zinc-700 rounded-full mt-2.5 mr-5 shrink-0"></div>
                <span className="text-lg font-light text-zinc-400 leading-relaxed">
                  {c}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="mt-24 pt-12 border-t border-zinc-900 flex flex-col md:flex-row md:items-center justify-between gap-8">
        <p className="text-2xl font-light text-zinc-400 italic">
          "I’ll work on these and prepare tomorrow’s briefing. The day begins."
        </p>
        <button 
          onClick={onExit}
          className="bg-zinc-100 text-zinc-950 px-12 py-4 font-bold text-lg rounded-sm hover:bg-white transition-all active:scale-95 whitespace-nowrap"
        >
          Exit to OS
        </button>
      </div>
    </div>
  );
};

export default CloseCommitmentsSlide;
