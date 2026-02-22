
export enum SlideType {
  ENTRY = 0,
  OPENING_CONTEXT = 1,
  OVERNIGHT_UPDATE = 2,
  MORNING_BRIEFING = 3,
  TODAYS_PRIORITIES = 4,
  INBOX_APPROVALS = 5,
  CLARIFYING_QUESTIONS = 6,
  AUDIO_JOURNAL = 7,
  CLOSE_COMMITMENTS = 8
}

export interface OvernightUpdate {
  id: string;
  status: 'completed' | 'blocked' | 'in-progress' | 'failed';
  outcome: string;
  details?: string;
}

export interface BriefingBlock {
  title: string;
  insights: string[];
}

export interface Priority {
  id: string;
  rank: number;
  title: string;
  why: string;
  estimatedTime: string;
  nextAction: string;
  confirmed: boolean;
}

export interface InboxItem {
  id: string;
  source: string;
  subject: string;
  summary: string;
  recommendedAction: string;
  draftResponse: string;
  resolved: boolean;
}

export interface Question {
  id: string;
  text: string;
  why: string;
  suggestions?: string[];
  answer?: string;
}

export interface BriefingData {
  openingSentence: string;
  overnightUpdates: OvernightUpdate[];
  briefingBlocks: BriefingBlock[];
  priorities: Priority[];
  inboxItems: InboxItem[];
  questions: Question[];
  robotCommitments: string[];
}
