
import { BriefingData } from './types';

export const MOCK_BRIEFING_DATA: BriefingData = {
  openingSentence: "Good morning. I've filtered yesterday's noise into three core decisions that require your attention today.",
  overnightUpdates: [
    {
      id: '1',
      status: 'completed',
      outcome: 'Completed competitor pricing scan across major markets.',
      details: 'Analyzed 12 direct competitors. Found 2 price hikes in the mid-tier segment.'
    },
    {
      id: '2',
      status: 'blocked',
      outcome: 'Blocked on Q3 budget approval for the marketing rollout.',
      details: 'CFO requested a more detailed breakdown of the customer acquisition cost projections.'
    },
    {
      id: '3',
      status: 'in-progress',
      outcome: 'Synchronizing customer feedback logs with product development roadmaps.',
      details: 'Processing 450 new feedback items. Completion expected by 2 PM.'
    }
  ],
  briefingBlocks: [
    {
      title: 'AI and Tech',
      insights: [
        'Major LLM version update released; potential 20% efficiency gain in internal automation.',
        'Regulatory shifts in EU may impact our upcoming data processing model.'
      ]
    },
    {
      title: 'Markets and Assets',
      insights: [
        'Equity markets show stable growth; Tech sector leading by 1.2% this morning.',
        'Volatility index at 3-month lows; calm environment for execution.'
      ]
    },
    {
      title: 'External Signals',
      insights: [
        'Primary competitor launched a pilot program in the APAC region.',
        'Industry sentiment shifting toward "Privacy First" architectures.'
      ]
    }
  ],
  priorities: [
    {
      id: 'p1',
      rank: 1,
      title: 'Finalize Hiring Strategy',
      why: 'Key roles remain unfilled, stalling the Q4 expansion.',
      estimatedTime: '45 mins',
      nextAction: 'Review finalist resumes and sign offer letters.',
      confirmed: false
    },
    {
      id: 'p2',
      rank: 2,
      title: 'Investor Deck Refinement',
      why: 'Board meeting is in 48 hours; clarity on growth metrics is crucial.',
      estimatedTime: '1.5 hours',
      nextAction: 'Update the revenue projection slides with real-time data.',
      confirmed: false
    },
    {
      id: 'p3',
      rank: 3,
      title: 'Infrastructure Audit',
      why: 'Scaling issues were detected in the staging environment.',
      estimatedTime: '30 mins',
      nextAction: 'Approve the migration to the high-availability cluster.',
      confirmed: false
    }
  ],
  inboxItems: [
    {
      id: 'i1',
      source: 'Elena (Product)',
      subject: 'UI Redesign Approval',
      summary: 'Final mocks for the mobile dashboard are ready for your sign-off.',
      recommendedAction: 'Approve for development.',
      draftResponse: "Excellent work, Elena. I've reviewed the mocks and the contrast adjustments look perfect. Approved for development.",
      resolved: false
    },
    {
      id: 'i2',
      source: 'James (Legal)',
      subject: 'Contract Renewal - Cloud Services',
      summary: 'Current contract expires in 10 days. 5% increase proposed.',
      recommendedAction: 'Counter-offer or approve.',
      draftResponse: "James, let's proceed with the approval but request a clause for a volume discount if we hit our Tier 2 growth targets by year-end.",
      resolved: false
    }
  ],
  questions: [
    {
      id: 'q1',
      text: 'Do we authorize the 15% increase in compute budget for the training run?',
      why: 'This is the difference between a 48-hour and a 12-hour training window.',
      suggestions: ['Yes, priority is speed.', 'No, stick to the original budget.', 'Let\'s wait for more data.']
    }
  ],
  robotCommitments: [
    "Compile the finalized hiring strategy updates.",
    "Draft the investor deck revenue slides.",
    "Monitor the infrastructure migration once approved."
  ]
};
