
import React, { useState } from 'react';
import { Question } from '../types';

interface Props {
  questions: Question[];
  onAnswer: (id: string, answer: string) => void;
  onNext: () => void;
}

const ClarifyingQuestionsSlide: React.FC<Props> = ({ questions, onAnswer, onNext }) => {
  const [index, setIndex] = useState(0);
  const current = questions[index];

  if (!current) {
    onNext();
    return null;
  }

  const handleSelect = (ans: string) => {
    onAnswer(current.id, ans);
    if (index < questions.length - 1) {
      setIndex(idx => idx + 1);
    } else {
      onNext();
    }
  };

  return (
    <div className="max-w-3xl w-full flex flex-col items-center animate-in fade-in slide-in-from-bottom duration-700">
      <header className="mb-16 text-center">
        <span className="text-zinc-600 text-xs font-bold tracking-[0.2em] uppercase">
          Clarifying Question
        </span>
        <p className="text-zinc-500 mt-2 text-sm">{current.why}</p>
      </header>

      <h2 className="text-3xl md:text-4xl font-light text-zinc-100 text-center leading-snug mb-16">
        {current.text}
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
        {current.suggestions?.map((suggestion, i) => (
          <button 
            key={i}
            onClick={() => handleSelect(suggestion)}
            className="p-6 border border-zinc-800 bg-zinc-900/20 text-zinc-300 hover:bg-zinc-100 hover:text-zinc-950 hover:border-zinc-100 transition-all text-left font-medium rounded-sm"
          >
            {suggestion}
          </button>
        ))}
        <button 
          className="p-6 border border-zinc-900 text-zinc-600 hover:text-zinc-400 text-left text-sm uppercase tracking-widest font-bold"
          onClick={() => handleSelect("Custom Answer")}
        >
          <i className="fa-solid fa-microphone mr-2"></i> Speak Answer
        </button>
      </div>
    </div>
  );
};

export default ClarifyingQuestionsSlide;
