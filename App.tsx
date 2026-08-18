import React, { FormEvent, useEffect, useMemo, useState } from 'react';

type Integration = {
  id: string;
  name: string;
  status: string;
  detail: string;
};

type Evidence = {
  id: string;
  source_type: string;
  source_title: string;
  source_url?: string | null;
  excerpt: string;
  confidence: number;
  is_inference: boolean;
};

type PlanStep = {
  id: string;
  title: string;
  description?: string | null;
  owner_name: string;
  status: string;
  risk_class: string;
  position: number;
  depends_on: string[];
};

type Approval = {
  id: string;
  action_type: string;
  target_system: string;
  action_summary: string;
  impact_summary?: string | null;
  risk_class: string;
  status: string;
  requested_by: string;
  requested_at: string;
  expires_at?: string | null;
};

type WorkEvent = {
  id: string;
  event_type: string;
  message: string;
  created_at: string;
};

type WorkObject = {
  id: string;
  title: string;
  objective: string;
  completion_test?: string | null;
  status: string;
  authority_lane: string;
  source_scope: string[];
  owner_name: string;
  priority: string;
  due_at?: string | null;
  evidence?: Evidence[];
  decisions?: { id: string; recommendation: string; rationale?: string | null; confidence: number; status: string }[];
  plan_steps?: PlanStep[];
  approvals?: Approval[];
  receipts?: { id: string; target_system: string; operation: string; summary: string; status: string }[];
  events?: WorkEvent[];
};

type Dashboard = {
  summary: { active_work: number; pending_approvals: number; evidence_items: number; receipts: number };
  work_objects: WorkObject[];
  pending_approvals: Approval[];
  activity: WorkEvent[];
  integrations: Integration[];
};

const API_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000/api' : '/api');

const demoDashboard: Dashboard = {
  summary: { active_work: 1, pending_approvals: 1, evidence_items: 2, receipts: 0 },
  work_objects: [
    {
      id: 'demo-work',
      title: 'Launch the XPM Jarvis operating pilot',
      objective: 'Validate the @Jarvis delegation workflow for XPM operations with a real ClickUp project and meeting evidence.',
      completion_test: 'A delegated ClickUp task produces a cited plan, an approved task update, and a receipt without duplicate writes.',
      status: 'awaiting_approval',
      authority_lane: 'draft_only',
      source_scope: ['clickup', 'otter', 'cognee', 'approved_web'],
      owner_name: 'You',
      priority: 'high',
      evidence: [
        {
          id: 'e-1',
          source_type: 'ClickUp',
          source_title: 'XPM Jarvis build task',
          excerpt: 'The pilot needs a command center, durable delegation, approvals, and a source-linked action receipt.',
          confidence: 0.96,
          is_inference: false,
        },
        {
          id: 'e-2',
          source_type: 'Otter',
          source_title: 'Pilot planning meeting',
          excerpt: 'A source-linked meeting decision should become a proposed ClickUp task rather than an untracked note.',
          confidence: 0.78,
          is_inference: false,
        },
      ],
      decisions: [
        {
          id: 'd-1',
          recommendation: 'Start with a tightly scoped research-to-ClickUp flow and keep writes behind action-specific approval.',
          rationale: 'It validates the product thesis while limiting the pilot’s blast radius.',
          confidence: 0.9,
          status: 'proposed',
        },
      ],
      plan_steps: [
        { id: 'p-1', title: 'Complete XPM Jarvis command-center foundation', owner_name: 'XPM Jarvis', status: 'in_progress', risk_class: 'read', position: 1, depends_on: [] },
        { id: 'p-2', title: 'Re-authorize ClickUp and configure the pilot list', owner_name: 'You', status: 'blocked', risk_class: 'credential', position: 2, depends_on: ['p-1'] },
        { id: 'p-3', title: 'Run the first @Jarvis delegation', owner_name: 'XPM Jarvis', status: 'proposed', risk_class: 'reversible_write', position: 3, depends_on: ['p-1', 'p-2'] },
      ],
      approvals: [
        {
          id: 'a-1',
          action_type: 'create_clickup_tasks',
          target_system: 'ClickUp',
          action_summary: 'Create the approved pilot task structure after the plan has been reviewed.',
          impact_summary: 'This will create project work items and may notify configured assignees.',
          risk_class: 'reversible_write',
          status: 'pending',
          requested_by: 'XPM Jarvis',
          requested_at: new Date().toISOString(),
        },
      ],
      events: [
        { id: 'v-1', event_type: 'approval_requested', message: 'A ClickUp write is ready for action-specific approval.', created_at: new Date().toISOString() },
        { id: 'v-2', event_type: 'evidence_ready', message: 'Evidence pack assembled from scoped work context.', created_at: new Date(Date.now() - 1000 * 60 * 13).toISOString() },
      ],
    },
  ],
  pending_approvals: [],
  activity: [],
  integrations: [
    { id: 'jarvis', name: 'XPM Jarvis', status: 'scaffolded', detail: 'The XPM control plane is ready; the private Hermes runtime remains an internal adapter to configure.' },
    { id: 'cognee', name: 'Cognee Memory', status: 'scaffolded', detail: 'Memory connector is ready to configure.' },
    { id: 'clickup', name: 'ClickUp', status: 'reauthorization_required', detail: 'Live delegation needs re-authorization.' },
    { id: 'otter', name: 'Otter', status: 'connected', detail: 'Read-only meeting evidence is available.' },
  ],
};

type View = 'today' | 'delegations' | 'plan' | 'evidence' | 'approvals' | 'activity';

const iconByView: Record<View, string> = {
  today: 'fa-grid-2',
  delegations: 'fa-wand-magic-sparkles',
  plan: 'fa-diagram-project',
  evidence: 'fa-book-open',
  approvals: 'fa-shield-halved',
  activity: 'fa-wave-square',
};

const statusStyle: Record<string, string> = {
  queued: 'bg-slate-700/60 text-slate-200 border-slate-600',
  researching: 'bg-blue-500/10 text-blue-200 border-blue-400/30',
  planning: 'bg-violet-500/10 text-violet-200 border-violet-400/30',
  awaiting_approval: 'bg-amber-400/10 text-amber-200 border-amber-300/30',
  executing: 'bg-emerald-500/10 text-emerald-200 border-emerald-400/30',
  completed: 'bg-emerald-500/10 text-emerald-200 border-emerald-400/30',
  blocked: 'bg-rose-500/10 text-rose-200 border-rose-400/30',
  proposed: 'bg-slate-500/10 text-slate-200 border-slate-400/30',
  in_progress: 'bg-blue-500/10 text-blue-200 border-blue-400/30',
  pending: 'bg-amber-400/10 text-amber-200 border-amber-300/30',
  approved: 'bg-emerald-500/10 text-emerald-200 border-emerald-400/30',
  rejected: 'bg-rose-500/10 text-rose-200 border-rose-400/30',
  connected: 'bg-emerald-500/10 text-emerald-200 border-emerald-400/30',
  ready: 'bg-emerald-500/10 text-emerald-200 border-emerald-400/30',
  scaffolded: 'bg-blue-500/10 text-blue-200 border-blue-400/30',
  reauthorization_required: 'bg-amber-400/10 text-amber-200 border-amber-300/30',
  not_connected: 'bg-slate-700/50 text-slate-300 border-slate-600',
};

const labelize = (value: string) => value.replace(/_/g, ' ');
const titleCase = (value: string) => labelize(value).replace(/\b\w/g, (char) => char.toUpperCase());
const confidence = (value?: number) => `${Math.round((value ?? 0) * 100)}%`;
const timeAgo = (value?: string) => {
  if (!value) return 'Just now';
  const delta = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.round(delta / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.round(minutes / 60)}h ago`;
};

const StatusPill = ({ value }: { value: string }) => (
  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] ${statusStyle[value] || statusStyle.proposed}`}>
    <span className="h-1.5 w-1.5 rounded-full bg-current" />
    {titleCase(value)}
  </span>
);

const App: React.FC = () => {
  const [view, setView] = useState<View>('today');
  const [dashboard, setDashboard] = useState<Dashboard>(demoDashboard);
  const [selected, setSelected] = useState<WorkObject>(demoDashboard.work_objects[0]);
  const [loading, setLoading] = useState(true);
  const [command, setCommand] = useState('');
  const [notice, setNotice] = useState('');
  const [showNewWork, setShowNewWork] = useState(false);

  const refresh = async () => {
    try {
      const response = await fetch(`${API_BASE}/workspace/dashboard`);
      if (!response.ok) throw new Error('Workspace API unavailable');
      const payload = await response.json() as Dashboard;
      const approvals = payload.pending_approvals.length ? payload.pending_approvals : payload.work_objects.flatMap((work) => work.approvals || []);
      const activity = payload.activity.length ? payload.activity : payload.work_objects.flatMap((work) => work.events || []);
      const normalized = { ...payload, pending_approvals: approvals, activity };
      setDashboard(normalized);
      const active = normalized.work_objects.find((work) => work.id === selected?.id) || normalized.work_objects[0];
      if (active) await loadWork(active.id);
    } catch {
      setDashboard(demoDashboard);
      setSelected(demoDashboard.work_objects[0]);
      setNotice('Showing the local workspace preview. Start the API to activate durable state.');
    } finally {
      setLoading(false);
    }
  };

  const loadWork = async (id: string) => {
    try {
      const response = await fetch(`${API_BASE}/work-objects/${id}`);
      if (!response.ok) throw new Error('Unable to load work object');
      setSelected(await response.json() as WorkObject);
    } catch {
      const fallback = dashboard.work_objects.find((work) => work.id === id);
      if (fallback) setSelected(fallback);
    }
  };

  useEffect(() => { void refresh(); }, []);

  const approvalCount = useMemo(
    () => (selected.approvals || []).filter((approval) => approval.status === 'pending').length,
    [selected],
  );

  const approve = async (approval: Approval, approved: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/approvals/${approval.id}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved, resolved_by: 'You' }),
      });
      if (!response.ok) throw new Error('Approval request could not be resolved');
      setNotice(`${approved ? 'Approved' : 'Declined'}: ${approval.action_type} in ${approval.target_system}.`);
      await refresh();
    } catch {
      setSelected((current) => ({
        ...current,
        status: approved ? 'executing' : 'planning',
        approvals: (current.approvals || []).map((item) => item.id === approval.id ? { ...item, status: approved ? 'approved' : 'rejected' } : item),
      }));
      setNotice(`${approved ? 'Approved' : 'Declined'} in preview mode. Start the API to persist this decision.`);
    }
  };

  const stageResearch = async () => {
    try {
      const response = await fetch(`${API_BASE}/work-objects/${selected.id}/research-draft`, { method: 'POST' });
      if (!response.ok) throw new Error('Draft unavailable');
      setSelected(await response.json() as WorkObject);
      setNotice('XPM Jarvis staged a source-grounded research-to-decision draft for review.');
    } catch {
      setNotice('Research staging is ready once the API is running. The production run will use XPM Jarvis, Cognee, ClickUp, and Otter within the selected tenant scope.');
    }
  };

  const createWork = async (event: FormEvent) => {
    event.preventDefault();
    if (!command.trim()) return;
    const body = {
      title: command.slice(0, 90),
      objective: command,
      completion_test: 'A cited plan is reviewed and any external action has a receipt.',
      authority_lane: 'draft_only',
      source_scope: ['clickup', 'otter', 'cognee', 'approved_web'],
      priority: 'medium',
    };
    try {
      const response = await fetch(`${API_BASE}/work-objects`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
      });
      if (!response.ok) throw new Error('Creation failed');
      const work = await response.json() as WorkObject;
      setSelected(work);
      setCommand('');
      setShowNewWork(false);
      setNotice('New delegation staged. XPM Jarvis will first propose research scope and a plan.');
      await refresh();
    } catch {
      const localWork: WorkObject = { ...body, id: `local-${Date.now()}`, status: 'queued', owner_name: 'You', evidence: [], plan_steps: [], approvals: [], events: [] };
      setDashboard((current) => ({ ...current, work_objects: [localWork, ...current.work_objects], summary: { ...current.summary, active_work: current.summary.active_work + 1 } }));
      setSelected(localWork);
      setCommand('');
      setShowNewWork(false);
      setNotice('Delegation staged locally. Start the API to persist and run it.');
    }
  };

  const navItems: { id: View; label: string; count?: number }[] = [
    { id: 'today', label: 'Today' },
    { id: 'delegations', label: 'Delegations', count: dashboard.summary.active_work },
    { id: 'plan', label: 'Plan Board' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'approvals', label: 'Approvals', count: dashboard.summary.pending_approvals },
    { id: 'activity', label: 'Activity' },
  ];

  const evidence = selected.evidence || [];
  const planSteps = selected.plan_steps || [];
  const decisions = selected.decisions || [];
  const approvals = selected.approvals || [];
  const timeline = selected.events || dashboard.activity;

  return (
    <div className="min-h-screen bg-[#0a0d12] text-slate-100 selection:bg-violet-400/30">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-64 left-[18%] h-[32rem] w-[32rem] rounded-full bg-violet-600/10 blur-[120px]" />
        <div className="absolute bottom-0 right-[-10rem] h-[28rem] w-[28rem] rounded-full bg-cyan-500/5 blur-[100px]" />
      </div>

      <div className="relative flex min-h-screen">
        <aside className="hidden w-[250px] shrink-0 flex-col border-r border-white/[0.07] bg-[#0d1118]/95 px-4 py-5 lg:flex">
          <div className="mb-9 flex items-center gap-3 px-2">
            <div className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-violet-400 to-fuchsia-500 text-sm shadow-lg shadow-violet-500/20">
              <i className="fa-solid fa-sparkles" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-tight">XPM Jarvis</p>
              <p className="text-[10px] font-medium uppercase tracking-[0.18em] text-violet-300">Operations Intelligence</p>
            </div>
          </div>

          <nav className="space-y-1">
            {navItems.map((item) => (
              <button key={item.id} onClick={() => setView(item.id)} className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${view === item.id ? 'bg-white/[0.08] text-white shadow-inner shadow-white/[0.03]' : 'text-slate-400 hover:bg-white/[0.04] hover:text-slate-200'}`}>
                <i className={`fa-solid ${iconByView[item.id]} w-4 text-center text-xs ${view === item.id ? 'text-violet-300' : ''}`} />
                <span className="flex-1 text-left">{item.label}</span>
                {item.count ? <span className="grid h-5 min-w-5 place-items-center rounded-md bg-violet-400/15 px-1 text-[10px] font-bold text-violet-200">{item.count}</span> : null}
              </button>
            ))}
          </nav>

          <div className="mt-auto rounded-2xl border border-white/[0.08] bg-white/[0.025] p-3.5">
            <div className="mb-2 flex items-center gap-2 text-xs font-medium text-slate-200"><span className="h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(74,222,128,.8)]" /> Control plane online</div>
            <p className="text-[11px] leading-relaxed text-slate-500">Research, plans, approvals, and receipts stay connected to one durable work object.</p>
          </div>
        </aside>

        <main className="min-w-0 flex-1 px-4 py-4 sm:px-7 sm:py-6 xl:px-10">
          <header className="mb-7 flex items-center justify-between gap-4">
            <div>
              <div className="mb-1 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-violet-300"><span>Monday operating review</span><span className="h-1 w-1 rounded-full bg-slate-500" /><span>Private workspace</span></div>
              <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-3xl">Good morning, build with intention.</h1>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => void refresh()} className="grid h-10 w-10 place-items-center rounded-xl border border-white/[0.08] bg-white/[0.035] text-slate-400 transition hover:border-violet-400/40 hover:text-white" title="Refresh workspace"><i className={`fa-solid fa-rotate ${loading ? 'animate-spin' : ''}`} /></button>
              <button onClick={() => setShowNewWork(true)} className="rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-violet-100"><i className="fa-solid fa-plus mr-2" />Delegate work</button>
            </div>
          </header>

          {notice && <div className="mb-5 flex items-start gap-3 rounded-xl border border-violet-400/20 bg-violet-400/[0.07] px-4 py-3 text-sm text-violet-100"><i className="fa-solid fa-circle-info mt-0.5 text-violet-300" /><span className="flex-1">{notice}</span><button onClick={() => setNotice('')} className="text-violet-300 hover:text-white"><i className="fa-solid fa-xmark" /></button></div>}

          <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { label: 'Active work', value: dashboard.summary.active_work, hint: 'Delegations in motion', icon: 'fa-bolt', color: 'text-violet-300' },
              { label: 'Needs approval', value: dashboard.summary.pending_approvals, hint: 'Exact actions awaiting you', icon: 'fa-shield-halved', color: 'text-amber-300' },
              { label: 'Evidence on file', value: dashboard.summary.evidence_items, hint: 'Sources and commitments', icon: 'fa-book-open', color: 'text-cyan-300' },
              { label: 'Action receipts', value: dashboard.summary.receipts, hint: 'Verified external outcomes', icon: 'fa-receipt', color: 'text-emerald-300' },
            ].map((metric) => (
              <div key={metric.label} className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-4 shadow-2xl shadow-black/10">
                <div className="mb-4 flex items-center justify-between"><span className="text-xs font-medium text-slate-400">{metric.label}</span><i className={`fa-solid ${metric.icon} ${metric.color} text-xs`} /></div>
                <div className="flex items-end gap-2"><span className="text-3xl font-semibold tracking-tight text-white">{metric.value}</span><span className="mb-1 text-[11px] text-slate-500">{metric.hint}</span></div>
              </div>
            ))}
          </div>

          {view === 'today' && (
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1.4fr)_minmax(320px,.8fr)]">
              <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10 sm:p-6">
                <div className="mb-6 flex items-start justify-between gap-4">
                  <div>
                    <div className="mb-2 flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-violet-400" /><p className="text-xs font-semibold uppercase tracking-[0.15em] text-violet-300">Active delegation</p></div>
                    <h2 className="text-xl font-semibold tracking-tight text-white">{selected.title}</h2>
                    <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">{selected.objective}</p>
                  </div>
                  <StatusPill value={selected.status} />
                </div>

                <div className="mb-6 grid gap-3 rounded-xl border border-white/[0.06] bg-black/15 p-4 sm:grid-cols-3">
                  <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Authority</p><p className="mt-1 text-sm font-medium text-slate-200">{titleCase(selected.authority_lane)}</p></div>
                  <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Source scope</p><p className="mt-1 text-sm font-medium text-slate-200">{selected.source_scope.length} approved sources</p></div>
                  <div><p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">Completion test</p><p className="mt-1 line-clamp-2 text-sm font-medium text-slate-200">{selected.completion_test || 'Define before external action.'}</p></div>
                </div>

                <div className="mb-4 flex items-center justify-between"><h3 className="text-sm font-semibold text-slate-100">Execution plan</h3><button onClick={() => setView('plan')} className="text-xs font-medium text-violet-300 hover:text-violet-100">Open plan board <i className="fa-solid fa-arrow-right ml-1 text-[10px]" /></button></div>
                <div className="space-y-2">
                  {planSteps.slice(0, 3).map((step, index) => (
                    <div key={step.id} className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.025] px-3.5 py-3">
                      <div className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-bold ${step.status === 'in_progress' ? 'bg-violet-400/20 text-violet-200' : step.status === 'blocked' ? 'bg-rose-400/15 text-rose-200' : 'bg-white/[0.08] text-slate-400'}`}>{index + 1}</div>
                      <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-slate-200">{step.title}</p><p className="mt-0.5 text-xs text-slate-500">Owner: {step.owner_name}</p></div>
                      <StatusPill value={step.status} />
                    </div>
                  ))}
                </div>

                <div className="mt-5 flex flex-wrap gap-2">
                  <button onClick={() => void stageResearch()} className="rounded-xl bg-violet-400 px-4 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-violet-300"><i className="fa-solid fa-magnifying-glass-chart mr-2" />Stage research brief</button>
                  <button onClick={() => setView('evidence')} className="rounded-xl border border-white/[0.1] bg-white/[0.03] px-4 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-white/[0.07]">Review evidence</button>
                </div>
              </section>

              <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10">
                <div className="mb-5 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-amber-300">Your decision</p><h2 className="mt-1 text-lg font-semibold text-white">{approvalCount} action waiting</h2></div><i className="fa-solid fa-shield-halved text-xl text-amber-300" /></div>
                {approvals.filter((approval) => approval.status === 'pending').slice(0, 1).map((approval) => (
                  <div key={approval.id} className="rounded-xl border border-amber-300/20 bg-amber-300/[0.055] p-4">
                    <div className="mb-3 flex items-center justify-between"><StatusPill value={approval.status} /><span className="text-[10px] font-medium text-amber-100/70">Expires {timeAgo(approval.expires_at)}</span></div>
                    <p className="text-sm font-semibold leading-6 text-amber-50">{approval.action_summary}</p>
                    <p className="mt-2 text-xs leading-5 text-amber-100/60">{approval.impact_summary}</p>
                    <div className="mt-4 flex gap-2"><button onClick={() => void approve(approval, true)} className="flex-1 rounded-lg bg-amber-300 px-3 py-2 text-xs font-bold text-amber-950 transition hover:bg-amber-200">Approve action</button><button onClick={() => void approve(approval, false)} className="rounded-lg border border-amber-200/20 px-3 py-2 text-xs font-semibold text-amber-100 transition hover:bg-white/[0.06]">Decline</button></div>
                  </div>
                ))}
                {!approvals.some((approval) => approval.status === 'pending') && <div className="rounded-xl border border-dashed border-white/[0.1] p-5 text-center text-sm text-slate-500">No actions are waiting for approval.</div>}
                <button onClick={() => setView('approvals')} className="mt-4 text-xs font-medium text-violet-300 hover:text-violet-100">View approval history <i className="fa-solid fa-arrow-right ml-1 text-[10px]" /></button>
              </section>

              <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10 xl:col-span-2">
                <div className="mb-4 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-cyan-300">Proactive planning queue</p><h2 className="mt-1 text-lg font-semibold text-white">What Jarvis sees next</h2></div><span className="text-xs text-slate-500">Evidence first, action second</span></div>
                <div className="grid gap-3 md:grid-cols-3">
                  {[
                    ['Meeting commitment', 'A source-linked commitment should become a reviewed task proposal.', 'Otter', 'fa-microphone-lines'],
                    ['Connection health', 'ClickUp authorization must be renewed before live delegation.', 'ClickUp', 'fa-plug-circle-xmark'],
                    ['Research run', 'The pilot needs a scope, evidence pack, decision brief, and plan review.', 'XPM Jarvis', 'fa-compass-drafting'],
                  ].map(([title, text, source, icon]) => (
                    <div key={title} className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-4"><div className="mb-3 flex items-center justify-between"><i className={`fa-solid ${icon} text-sm text-cyan-300`} /><span className="rounded-md bg-cyan-400/10 px-2 py-1 text-[10px] font-semibold text-cyan-200">{source}</span></div><p className="text-sm font-semibold text-slate-200">{title}</p><p className="mt-1.5 text-xs leading-5 text-slate-500">{text}</p></div>
                  ))}
                </div>
              </section>
            </div>
          )}

          {view === 'delegations' && <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><div className="mb-5 flex items-end justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-violet-300">Delegation ledger</p><h2 className="mt-1 text-xl font-semibold text-white">Every objective has a visible operating state.</h2></div><button onClick={() => setShowNewWork(true)} className="text-sm font-semibold text-violet-300 hover:text-violet-100">+ New delegation</button></div><div className="space-y-2">{dashboard.work_objects.map((work) => <button key={work.id} onClick={() => { setSelected(work); void loadWork(work.id); setView('today'); }} className={`flex w-full items-center gap-4 rounded-xl border p-4 text-left transition ${selected.id === work.id ? 'border-violet-400/35 bg-violet-400/[0.06]' : 'border-white/[0.06] bg-white/[0.02] hover:border-white/[0.13]'}`}><div className="grid h-10 w-10 place-items-center rounded-xl bg-violet-400/10 text-violet-200"><i className="fa-solid fa-briefcase" /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold text-white">{work.title}</p><p className="mt-1 truncate text-xs text-slate-500">{work.objective}</p></div><StatusPill value={work.status} /><i className="fa-solid fa-chevron-right text-xs text-slate-600" /></button>)}</div></section>}

          {view === 'plan' && <section className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(300px,.75fr)]"><div className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><div className="mb-6"><p className="text-xs font-semibold uppercase tracking-[0.15em] text-violet-300">Editable plan</p><h2 className="mt-1 text-xl font-semibold text-white">{selected.title}</h2><p className="mt-2 text-sm text-slate-400">Review the structure before XPM Jarvis is allowed to make an external change.</p></div><div className="space-y-3">{planSteps.map((step, index) => <div key={step.id} className="rounded-xl border border-white/[0.07] bg-black/15 p-4"><div className="flex items-start gap-3"><div className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/[0.07] text-xs font-bold text-slate-300">{index + 1}</div><div className="flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><p className="text-sm font-semibold text-slate-100">{step.title}</p><StatusPill value={step.status} /></div><p className="mt-1 text-xs leading-5 text-slate-500">{step.description || 'Structured work step awaiting execution detail.'}</p><div className="mt-3 flex flex-wrap gap-2 text-[10px] font-medium text-slate-400"><span className="rounded-md bg-white/[0.06] px-2 py-1">Owner · {step.owner_name}</span><span className="rounded-md bg-white/[0.06] px-2 py-1">Risk · {titleCase(step.risk_class)}</span>{step.depends_on.length > 0 && <span className="rounded-md bg-white/[0.06] px-2 py-1">{step.depends_on.length} dependencies</span>}</div></div></div></div>)}</div></div><aside className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><p className="text-xs font-semibold uppercase tracking-[0.15em] text-cyan-300">Decision brief</p>{decisions.map((decision) => <div key={decision.id} className="mt-4 rounded-xl border border-cyan-300/15 bg-cyan-300/[0.045] p-4"><p className="text-sm font-semibold leading-6 text-cyan-50">{decision.recommendation}</p><p className="mt-2 text-xs leading-5 text-cyan-100/60">{decision.rationale}</p><div className="mt-3 flex items-center justify-between text-[10px] font-semibold uppercase tracking-[0.12em] text-cyan-200/70"><span>Confidence</span><span>{confidence(decision.confidence)}</span></div></div>)}<button onClick={() => setShowNewWork(true)} className="mt-5 w-full rounded-xl border border-white/[0.1] bg-white/[0.035] px-4 py-2.5 text-sm font-semibold text-slate-200 transition hover:bg-white/[0.08]">Revise the objective</button></aside></section>}

          {view === 'evidence' && <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><div className="mb-6 flex items-end justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-cyan-300">Evidence pack</p><h2 className="mt-1 text-xl font-semibold text-white">What Jarvis knows, and why.</h2></div><span className="text-xs text-slate-500">Facts and inferences stay distinct.</span></div><div className="grid gap-3 lg:grid-cols-2">{evidence.map((item) => <article key={item.id} className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-4"><div className="mb-3 flex items-center justify-between"><span className="rounded-md bg-cyan-400/10 px-2 py-1 text-[10px] font-semibold text-cyan-200">{item.source_type}</span><span className="text-[10px] font-semibold text-slate-500">{confidence(item.confidence)} confidence</span></div><p className="text-sm font-semibold text-slate-200">{item.source_title}</p><p className="mt-2 text-sm leading-6 text-slate-400">“{item.excerpt}”</p><div className="mt-4 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.12em] text-slate-500"><i className="fa-solid fa-link" />{item.is_inference ? 'Inference — not a source fact' : 'Source-backed evidence'}</div></article>)}</div>{evidence.length === 0 && <div className="rounded-xl border border-dashed border-white/[0.1] p-8 text-center text-sm text-slate-500">No evidence has been added to this delegation yet.</div>}</section>}

          {view === 'approvals' && <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><div className="mb-6"><p className="text-xs font-semibold uppercase tracking-[0.15em] text-amber-300">Authority queue</p><h2 className="mt-1 text-xl font-semibold text-white">Jarvis never treats a chat message as blanket authority.</h2></div><div className="space-y-3">{(dashboard.pending_approvals.length ? dashboard.pending_approvals : approvals).map((approval) => <div key={approval.id} className="rounded-xl border border-white/[0.07] bg-white/[0.025] p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><div className="mb-2 flex items-center gap-2"><StatusPill value={approval.status} /><span className="text-xs font-medium text-slate-500">{approval.target_system}</span></div><p className="text-sm font-semibold text-slate-100">{approval.action_summary}</p><p className="mt-2 max-w-3xl text-xs leading-5 text-slate-500">{approval.impact_summary || 'No additional impact summary recorded.'}</p></div>{approval.status === 'pending' && <div className="flex gap-2"><button onClick={() => void approve(approval, true)} className="rounded-lg bg-emerald-300 px-3 py-2 text-xs font-bold text-emerald-950">Approve</button><button onClick={() => void approve(approval, false)} className="rounded-lg border border-white/[0.1] px-3 py-2 text-xs font-semibold text-slate-300">Decline</button></div>}</div><div className="mt-4 flex flex-wrap gap-2 text-[10px] text-slate-500"><span>Requested by {approval.requested_by}</span><span>•</span><span>{timeAgo(approval.requested_at)}</span><span>•</span><span>{titleCase(approval.risk_class)}</span></div></div>)}</div></section>}

          {view === 'activity' && <section className="rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><div className="mb-6"><p className="text-xs font-semibold uppercase tracking-[0.15em] text-emerald-300">Run timeline</p><h2 className="mt-1 text-xl font-semibold text-white">Trace every important change.</h2></div><div className="relative ml-2 border-l border-white/[0.1] pl-6">{timeline.map((event) => <div key={event.id} className="relative pb-6 last:pb-0"><span className="absolute -left-[31px] top-1.5 h-3 w-3 rounded-full border-2 border-[#111721] bg-emerald-400 shadow-[0_0_12px_rgba(74,222,128,.65)]" /><div className="flex flex-wrap items-center gap-2"><span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-300">{titleCase(event.event_type)}</span><span className="text-[10px] text-slate-600">{timeAgo(event.created_at)}</span></div><p className="mt-1 text-sm leading-6 text-slate-300">{event.message}</p></div>)}</div></section>}

          <section className="mt-5 rounded-2xl border border-white/[0.08] bg-[#111721]/80 p-5 shadow-2xl shadow-black/10"><div className="mb-4 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-slate-400">Connected systems</p><p className="mt-1 text-sm text-slate-500">Each connector has its own authority and health state.</p></div><button onClick={() => setView('activity')} className="text-xs font-medium text-violet-300 hover:text-violet-100">See activity</button></div><div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">{dashboard.integrations.map((integration) => <div key={integration.id} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-3"><div className="flex items-center justify-between"><p className="text-sm font-semibold text-slate-200">{integration.name}</p><StatusPill value={integration.status} /></div><p className="mt-2 text-xs leading-5 text-slate-500">{integration.detail}</p></div>)}</div></section>
        </main>
      </div>

      {showNewWork && <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm"><form onSubmit={createWork} className="w-full max-w-xl rounded-2xl border border-white/[0.12] bg-[#121925] p-5 shadow-2xl shadow-black/50"><div className="mb-5 flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.15em] text-violet-300">New delegation</p><h2 className="mt-1 text-xl font-semibold text-white">What should Jarvis take on?</h2><p className="mt-2 text-sm text-slate-400">Jarvis will start with research scope and a proposed plan. External writes remain gated.</p></div><button type="button" onClick={() => setShowNewWork(false)} className="text-slate-500 hover:text-white"><i className="fa-solid fa-xmark text-lg" /></button></div><textarea autoFocus value={command} onChange={(event) => setCommand(event.target.value)} placeholder="Example: Investigate the launch blockers, review the latest meeting commitments, and create a proposed ClickUp recovery plan." className="h-32 w-full resize-none rounded-xl border border-white/[0.1] bg-black/20 p-4 text-sm leading-6 text-slate-100 outline-none placeholder:text-slate-600 focus:border-violet-400/50" /><div className="mt-4 flex items-center justify-between"><span className="text-xs text-slate-500"><i className="fa-solid fa-shield-halved mr-1 text-violet-300" />Starts in draft-only authority</span><button type="submit" className="rounded-xl bg-violet-400 px-4 py-2.5 text-sm font-bold text-slate-950 transition hover:bg-violet-300">Stage delegation <i className="fa-solid fa-arrow-right ml-2" /></button></div></form></div>}
    </div>
  );
};

export default App;
