
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { SlideType, BriefingData, Priority, InboxItem, Question } from './types';
import { MOCK_BRIEFING_DATA } from './constants';
import { gemini } from './services/geminiService';

// Slide Components
import EntrySlide from './components/EntrySlide';
import OpeningContextSlide from './components/OpeningContextSlide';
import OvernightUpdateSlide from './components/OvernightUpdateSlide';
import MorningBriefingSlide from './components/MorningBriefingSlide';
import PrioritiesSlide from './components/PrioritiesSlide';
import InboxSlide from './components/InboxSlide';
import ClarifyingQuestionsSlide from './components/ClarifyingQuestionsSlide';
import AudioJournalSlide from './components/AudioJournalSlide';
import CloseCommitmentsSlide from './components/CloseCommitmentsSlide';

const App: React.FC = () => {
  const [currentSlide, setCurrentSlide] = useState<SlideType>(SlideType.ENTRY);
  const [data, setData] = useState<BriefingData>(MOCK_BRIEFING_DATA);
  const [loading, setLoading] = useState(false);
  const [journalNote, setJournalNote] = useState<string>("");

  // Navigation Logic
  const nextSlide = useCallback(() => {
    if (currentSlide < SlideType.CLOSE_COMMITMENTS) {
      setCurrentSlide(prev => prev + 1);
    }
  }, [currentSlide]);

  const prevSlide = useCallback(() => {
    if (currentSlide > SlideType.ENTRY) {
      setCurrentSlide(prev => prev - 1);
    }
  }, [currentSlide]);

  // Initial greeting generation
  useEffect(() => {
    const fetchGreeting = async () => {
      const greeting = await gemini.generateExecutiveGreeting();
      setData(prev => ({ ...prev, openingSentence: greeting }));
    };
    fetchGreeting();
  }, []);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'Enter' || e.key === ' ') {
        if (currentSlide === SlideType.ENTRY) return; // Wait for explicit start
        if (currentSlide === SlideType.AUDIO_JOURNAL) return; // Prevent skip while journaling
        nextSlide();
      } else if (e.key === 'ArrowLeft') {
        prevSlide();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentSlide, nextSlide, prevSlide]);

  // Data Updates
  const updatePriority = (updatedPriorities: Priority[]) => {
    setData(prev => ({ ...prev, priorities: updatedPriorities }));
  };

  const resolveInboxItem = (id: string) => {
    setData(prev => ({
      ...prev,
      inboxItems: prev.inboxItems.map(item => item.id === id ? { ...item, resolved: true } : item)
    }));
  };

  const answerQuestion = (id: string, answer: string) => {
    setData(prev => ({
      ...prev,
      questions: prev.questions.map(q => q.id === id ? { ...q, answer } : q)
    }));
  };

  // Progress calculation
  const totalSlides = 9;
  const progress = (currentSlide / (totalSlides - 1)) * 100;

  const renderSlide = () => {
    switch (currentSlide) {
      case SlideType.ENTRY:
        return <EntrySlide onStart={nextSlide} />;
      case SlideType.OPENING_CONTEXT:
        return <OpeningContextSlide sentence={data.openingSentence} onNext={nextSlide} />;
      case SlideType.OVERNIGHT_UPDATE:
        return <OvernightUpdateSlide updates={data.overnightUpdates} onNext={nextSlide} />;
      case SlideType.MORNING_BRIEFING:
        return <MorningBriefingSlide blocks={data.briefingBlocks} onNext={nextSlide} />;
      case SlideType.TODAYS_PRIORITIES:
        return <PrioritiesSlide priorities={data.priorities} onUpdate={updatePriority} onNext={nextSlide} />;
      case SlideType.INBOX_APPROVALS:
        return <InboxSlide items={data.inboxItems} onResolve={resolveInboxItem} onNext={nextSlide} />;
      case SlideType.CLARIFYING_QUESTIONS:
        return <ClarifyingQuestionsSlide questions={data.questions} onAnswer={answerQuestion} onNext={nextSlide} />;
      case SlideType.AUDIO_JOURNAL:
        return <AudioJournalSlide onFinished={(note) => { setJournalNote(note); nextSlide(); }} />;
      case SlideType.CLOSE_COMMITMENTS:
        return <CloseCommitmentsSlide data={data} journalNote={journalNote} onExit={() => setCurrentSlide(SlideType.ENTRY)} />;
      default:
        return null;
    }
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-zinc-950 text-zinc-50 select-none overflow-hidden transition-colors duration-500">
      {/* Global Progress Indicator */}
      {currentSlide !== SlideType.ENTRY && (
        <div className="fixed top-0 left-0 w-full h-1 bg-zinc-900 z-50">
          <div 
            className="h-full bg-zinc-400 transition-all duration-700 ease-in-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 md:p-12 relative">
        {renderSlide()}
      </main>

      {/* Navigation Controls (Persistent CTA) */}
      {currentSlide !== SlideType.ENTRY && currentSlide !== SlideType.AUDIO_JOURNAL && (
        <div className="fixed bottom-8 right-8 flex items-center space-x-4">
          {currentSlide > SlideType.OPENING_CONTEXT && (
            <button 
              onClick={prevSlide}
              className="text-zinc-500 hover:text-zinc-300 transition-colors px-4 py-2 text-sm font-medium tracking-wide uppercase"
            >
              Back
            </button>
          )}
          {currentSlide !== SlideType.CLOSE_COMMITMENTS && (
            <button 
              onClick={nextSlide}
              className="bg-zinc-100 text-zinc-950 px-8 py-3 rounded-sm font-semibold tracking-tight hover:bg-white transition-all active:scale-95 flex items-center"
            >
              <span>Continue</span>
              <i className="fa-solid fa-arrow-right ml-3 text-xs"></i>
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default App;
