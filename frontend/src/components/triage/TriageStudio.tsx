import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  BookOpen,
  Building,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Copy,
  FileText,
  Flame,
  Layers,
  PhoneCall,
  RefreshCw,
  Send,
  ShieldAlert,
  Sparkles,
  UserCheck,
  Zap,
} from 'lucide-react';
import { api } from '../../services/api';
import { SampleTicketScenario, TicketBrief } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Input } from '../ui/Input';
import { Textarea } from '../ui/Textarea';

export const TriageStudio: React.FC = () => {
  const [samples, setSamples] = useState<SampleTicketScenario[]>([]);
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [productArea, setProductArea] = useState('dispatch');
  const [submitterEmail, setSubmitterEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [brief, setBrief] = useState<TicketBrief | null>(null);
  const [copiedResponse, setCopiedResponse] = useState(false);

  useEffect(() => {
    api.getTriageSamples()
      .then(setSamples)
      .catch((e) => console.warn('Failed to load triage samples:', e));
  }, []);

  const handleSelectSample = (sample: SampleTicketScenario) => {
    setSubject(sample.ticket_data.subject);
    setDescription(sample.ticket_data.description);
    setProductArea(sample.ticket_data.product_area || 'dispatch');
    setSubmitterEmail(sample.ticket_data.submitter_email || '');
    handleRunTriage({
      subject: sample.ticket_data.subject,
      description: sample.ticket_data.description,
      product_area: sample.ticket_data.product_area,
      submitter_email: sample.ticket_data.submitter_email,
      tenant_id: sample.ticket_data.tenant_id,
      ticket_id: sample.ticket_data.ticket_id,
    });
  };

  const handleRunTriage = async (customData?: Record<string, any>) => {
    const data = customData || {
      subject,
      description,
      product_area: productArea,
      submitter_email: submitterEmail,
    };

    if (!data.subject?.trim() || !data.description?.trim()) return;

    setIsLoading(true);
    try {
      const res = await api.triageTicket(data);
      setBrief(res);
    } catch (err: any) {
      console.error('Triage error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const copySuggestedResponse = () => {
    if (!brief?.suggested_response) return;
    navigator.clipboard.writeText(brief.suggested_response);
    setCopiedResponse(true);
    setTimeout(() => setCopiedResponse(false), 2000);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold text-white tracking-tight">Support Ticket Triage Studio</h1>
            <Badge variant="purple">5-Source Intelligence</Badge>
          </div>
          <p className="text-xs text-slate-400">
            Synthesizes customer profile, dispatch telemetry, past tickets, call sentiment, and KB articles.
          </p>
        </div>
      </div>

      {/* 1-Click Assignment Test Scenarios */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="py-3">
          <CardTitle className="text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            <span>Assignment Benchmark Test Tickets</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {samples.map((s) => (
              <button
                key={s.scenario_id}
                onClick={() => handleSelectSample(s)}
                className="flex flex-col text-left p-3 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800/90 hover:border-primary-500/50 transition-all group active:scale-[0.98]"
              >
                <div className="flex items-center justify-between w-full mb-1.5">
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-primary-400 transition-colors">
                    {s.title}
                  </span>
                  <Badge
                    variant={
                      s.scenario_type === 'low_health_expiring'
                        ? 'danger'
                        : s.scenario_type === 'duplicate_ticket'
                        ? 'warning'
                        : 'info'
                    }
                    size="sm"
                  >
                    {s.scenario_type.replace('_', ' ')}
                  </Badge>
                </div>
                <p className="text-xs text-slate-400 line-clamp-2">{s.description}</p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Main Grid: Input Form vs Output Brief */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Ticket Input */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-slate-800">
            <CardHeader>
              <CardTitle>
                <FileText className="h-4 w-4 text-primary-400" />
                <span>Ticket Details</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Subject</label>
                <Input
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  placeholder="e.g. TankLink device not sending data"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Submitter Email</label>
                <Input
                  value={submitterEmail}
                  onChange={(e) => setSubmitterEmail(e.target.value)}
                  placeholder="contact_4_0@desertsunpetroleum.com"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Product Area</label>
                <select
                  value={productArea}
                  onChange={(e) => setProductArea(e.target.value)}
                  className="w-full bg-[#0d1322] border border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                >
                  <option value="dispatch">dispatch</option>
                  <option value="pricing">pricing</option>
                  <option value="tank_monitor">tank_monitor</option>
                  <option value="route_builder">route_builder</option>
                  <option value="invoicing">invoicing</option>
                  <option value="customer_portal">customer_portal</option>
                  <option value="analytics">analytics</option>
                  <option value="driver_app">driver_app</option>
                  <option value="login_access">login_access</option>
                  <option value="integration">integration</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description / Notes</label>
                <Textarea
                  rows={4}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Paste support ticket description, customer report, or phone transcript..."
                />
              </div>

              <Button
                variant="primary"
                className="w-full mt-2"
                onClick={() => handleRunTriage()}
                isLoading={isLoading}
                disabled={!subject.trim() || !description.trim()}
              >
                <Zap className="h-4 w-4 mr-1.5" /> Run 5-Source Triage
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Structured Ticket Brief */}
        <div className="lg:col-span-7">
          {brief ? (
            <div className="space-y-4">
              {/* Executive Summary Card */}
              <Card className="glass-panel border-primary-500/30 overflow-hidden shadow-2xl">
                {/* Escalation Risk Header */}
                <div
                  className={`px-5 py-4 flex items-center justify-between border-b ${
                    brief.escalation.level === 'CRITICAL'
                      ? 'bg-rose-950/70 border-rose-800/80 text-rose-200'
                      : brief.escalation.level === 'HIGH'
                      ? 'bg-amber-950/70 border-amber-800/80 text-amber-200'
                      : 'bg-emerald-950/70 border-emerald-800/80 text-emerald-200'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <ShieldAlert className="h-5 w-5 shrink-0" />
                    <div>
                      <h3 className="font-bold text-sm">
                        Escalation Level: {brief.escalation.level} (Score: {brief.escalation.score}/100)
                      </h3>
                      <span className="text-[11px] opacity-90">
                        {brief.escalation.churn_risk ? '⚠️ High Churn Risk Account' : 'Standard Operational Escalation'}
                      </span>
                    </div>
                  </div>
                  <Badge
                    variant={
                      brief.escalation.level === 'CRITICAL'
                        ? 'danger'
                        : brief.escalation.level === 'HIGH'
                        ? 'warning'
                        : 'success'
                    }
                    size="md"
                  >
                    {brief.escalation.level}
                  </Badge>
                </div>

                <CardContent className="space-y-4">
                  {/* Warning Alerts */}
                  {brief.inactive_module_warning && (
                    <div className="p-3 rounded-lg bg-amber-950/70 border border-amber-800/80 text-amber-300 text-xs flex items-start gap-2.5">
                      <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold">Inactive Module Warning</span>
                        <p className="mt-0.5">{brief.inactive_module_warning}</p>
                      </div>
                    </div>
                  )}

                  {brief.duplicate_detection?.is_duplicate && (
                    <div className="p-3 rounded-lg bg-sky-950/70 border border-sky-800/80 text-sky-300 text-xs flex items-start gap-2.5">
                      <RefreshCw className="h-4 w-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold">Duplicate Ticket Detected</span>
                        <p className="mt-0.5">{brief.duplicate_detection.duplicate_note}</p>
                      </div>
                    </div>
                  )}

                  {/* Customer Commercial Snapshot */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Building className="h-3.5 w-3.5 text-primary-400" />
                      <span>Commercial Profile — {brief.customer_profile.name}</span>
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Health Score</span>
                        <span
                          className={`font-bold text-sm ${
                            brief.customer_profile.health_score < 40
                              ? 'text-rose-400'
                              : brief.customer_profile.health_score < 70
                              ? 'text-amber-400'
                              : 'text-emerald-400'
                          }`}
                        >
                          {brief.customer_profile.health_score}/100
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Annual CARR</span>
                        <span className="font-bold text-sm text-slate-200">
                          ${brief.customer_profile.carr.toLocaleString()}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Contract Expiry</span>
                        <span className="font-bold text-sm text-slate-200">
                          {brief.customer_profile.contract_end_date}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Assigned CSM</span>
                        <span className="font-bold text-sm text-sky-400">
                          {brief.customer_profile.assigned_csm}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Dispatch Telemetry */}
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <Flame className="h-3.5 w-3.5 text-amber-400" />
                      <span>Live Dispatch Telemetry (Last 30 Days)</span>
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Deliveries</span>
                        <span className="font-semibold text-slate-200">
                          {brief.operational_snapshot.deliveries_last_30d.toLocaleString()}
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Fill Rate</span>
                        <span className="font-semibold text-emerald-400">
                          {(brief.operational_snapshot.fill_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="p-2 rounded bg-slate-900/60 border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Emergency Orders</span>
                        <span className="font-semibold text-rose-400">
                          {brief.operational_snapshot.emergency_orders_count}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Relevant Knowledge Base Articles */}
                  {brief.relevant_kb_articles.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <BookOpen className="h-3.5 w-3.5 text-sky-400" />
                        <span>Recommended KB Resolutions</span>
                      </h4>
                      <div className="space-y-2">
                        {brief.relevant_kb_articles.map((kb) => (
                          <div key={kb.article_id} className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
                            <div className="flex items-center justify-between font-semibold text-slate-200 mb-1">
                              <span>[{kb.article_id}] {kb.title}</span>
                              <Badge variant="info" size="sm">Score: {kb.relevance_score}</Badge>
                            </div>
                            <p className="text-slate-400 mb-1.5"><strong className="text-slate-300">Root Cause:</strong> {kb.root_cause}</p>
                            <p className="text-emerald-400 bg-emerald-950/30 p-2 rounded border border-emerald-900/40">
                              <strong>Resolution:</strong> {kb.resolution}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Call History & Sentiment */}
                  {brief.recent_calls.length > 0 && (
                    <div>
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <PhoneCall className="h-3.5 w-3.5 text-purple-400" />
                        <span>Recent Call History & Sentiment</span>
                      </h4>
                      <div className="space-y-1.5">
                        {brief.recent_calls.map((call) => (
                          <div key={call.call_id} className="p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 text-xs flex items-start justify-between gap-2">
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-slate-200">{call.topic}</span>
                                <span className="text-[10px] text-slate-500">{call.date}</span>
                              </div>
                              <p className="text-slate-400 text-[11px] mt-0.5">{call.summary}</p>
                            </div>
                            <Badge
                              variant={
                                call.sentiment === 'negative'
                                  ? 'danger'
                                  : call.sentiment === 'positive'
                                  ? 'success'
                                  : 'default'
                              }
                              size="sm"
                            >
                              {call.sentiment}
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggested Response Draft */}
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                        <Send className="h-3.5 w-3.5 text-primary-400" />
                        <span>Suggested Response Draft</span>
                      </h4>
                      <Button variant="outline" size="sm" onClick={copySuggestedResponse}>
                        {copiedResponse ? <Check className="h-3 w-3 text-emerald-400 mr-1" /> : <Copy className="h-3 w-3 mr-1" />}
                        {copiedResponse ? 'Copied' : 'Copy Draft'}
                      </Button>
                    </div>
                    <pre className="text-xs font-sans text-slate-200 bg-slate-950 p-3.5 rounded-lg border border-slate-800 whitespace-pre-wrap leading-relaxed">
                      {brief.suggested_response}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card className="border-dashed border-slate-800 h-96 flex flex-col items-center justify-center text-center p-8">
              <Layers className="h-10 w-10 text-slate-600 mb-3" />
              <h3 className="text-sm font-semibold text-slate-300">No Ticket Triage Generated Yet</h3>
              <p className="text-xs text-slate-500 max-w-sm mt-1">
                Select one of the benchmark test scenarios above or paste a custom support ticket to generate a complete 5-source brief.
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

