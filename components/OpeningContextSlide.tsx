
import React, { useEffect } from 'react';

interface Props {
  sentence: string;
  onNext: () => void;
}

const OpeningContextSlide: React.FC<Props> = ({ sentence, onNext }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onNext();
    }, 15000); // Auto-advance after 15 seconds
    return () => clearTimeout(timer);
  }, [onNext]);

  return (
    <div className="max-w-3xl w-full flex flex-col items-start md:items-center animate-in slide-in-from-bottom duration-1000">
      <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase mb-8">
        Opening Context
      </span>
      <h2 className="text-3xl md:text-5xl leading-tight font-light text-zinc-100 md:text-center">
        {sentence}
      </h2>
      <div className="mt-12 opacity-40">
        <i className="fa-solid fa-volume-high text-zinc-400"></i>
      </div>
    </div>
  );
};

export default OpeningContextSlide;
