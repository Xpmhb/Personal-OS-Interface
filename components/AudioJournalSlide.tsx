
import React, { useState, useEffect, useRef } from 'react';

interface Props {
  onFinished: (note: string) => void;
}

const AudioJournalSlide: React.FC<Props> = ({ onFinished }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);
  const intervalRef = useRef<number | null>(null);

  const startRecording = () => {
    setIsRecording(true);
    intervalRef.current = window.setInterval(() => {
      setSeconds(s => s + 1);
    }, 1000);
  };

  const stopRecording = () => {
    setIsRecording(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
    onFinished("Captured reflective session at " + new Date().toLocaleTimeString());
  };

  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="max-w-2xl w-full flex flex-col items-center text-center animate-in fade-in duration-700">
      <header className="mb-16">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Audio Journal
        </span>
        <h2 className="text-3xl font-light text-zinc-100 mt-4 leading-relaxed">
          Anything worth capturing for future decisions or reflection?
        </h2>
      </header>

      <div className="relative flex flex-col items-center">
        <button 
          onClick={isRecording ? stopRecording : startRecording}
          className={`w-32 h-32 rounded-full flex items-center justify-center transition-all ${isRecording ? 'bg-red-500/10 border-2 border-red-500 text-red-500 scale-110' : 'bg-zinc-100 text-zinc-950 hover:bg-white'}`}
        >
          {isRecording ? (
            <i className="fa-solid fa-stop text-2xl"></i>
          ) : (
            <i className="fa-solid fa-microphone text-2xl"></i>
          )}
        </button>

        <div className={`mt-10 transition-opacity duration-500 ${isRecording ? 'opacity-100' : 'opacity-0'}`}>
          <div className="flex items-center space-x-2 text-red-500 font-mono text-xl">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            <span>{formatTime(seconds)}</span>
          </div>
          <p className="text-zinc-600 mt-2 text-sm tracking-tight uppercase">System is listening...</p>
        </div>

        {!isRecording && (
          <button 
            onClick={() => onFinished("")}
            className="mt-12 text-zinc-600 hover:text-zinc-400 text-sm font-bold uppercase tracking-widest"
          >
            Skip Journaling
          </button>
        )}
      </div>
    </div>
  );
};

export default AudioJournalSlide;
