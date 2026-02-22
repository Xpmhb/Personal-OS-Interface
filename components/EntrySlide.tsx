
import React from 'react';

interface Props {
  onStart: () => void;
}

const EntrySlide: React.FC<Props> = ({ onStart }) => {
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  return (
    <div className="flex flex-col items-center text-center animate-in fade-in zoom-in duration-1000">
      <h1 className="text-4xl md:text-6xl font-light tracking-tight mb-4 text-zinc-100">
        Morning Briefing
      </h1>
      <p className="text-zinc-500 text-lg md:text-xl font-medium mb-12">
        {today}
      </p>
      
      <div className="flex flex-col items-center">
        <button 
          onClick={onStart}
          className="group relative px-12 py-4 bg-zinc-100 text-zinc-950 text-xl font-semibold transition-all hover:bg-white active:scale-95 rounded-sm"
        >
          Start Briefing
          <div className="absolute inset-0 border border-zinc-100 group-hover:scale-110 opacity-0 group-hover:opacity-20 transition-all rounded-sm"></div>
        </button>
        <p className="mt-6 text-zinc-600 text-sm tracking-widest uppercase">
          Estimated 8 to 12 minutes
        </p>
      </div>
    </div>
  );
};

export default EntrySlide;
