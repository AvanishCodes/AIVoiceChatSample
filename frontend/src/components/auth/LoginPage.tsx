import React, { useEffect, useState } from 'react';
import { Bot, Fuel, Lock, Mail, ShieldCheck, Sparkles, UserCheck, Zap } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { DemoUser } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Input } from '../ui/Input';

export const LoginPage: React.FC = () => {
  const { login, quickLogin, isLoading } = useAuth();
  const [email, setEmail] = useState('csm@fleetpanda.com');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState<string | null>(null);
  const [demoUsers, setDemoUsers] = useState<DemoUser[]>([]);

  useEffect(() => {
    api.getDemoUsers()
      .then(setDemoUsers)
      .catch((err) => console.warn('Failed to load demo accounts:', err));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify credentials.');
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] flex flex-col justify-center items-center px-4 py-12 relative overflow-hidden">
      {/* Background glow effects */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="w-full max-w-5xl grid grid-cols-1 lg:grid-cols-12 gap-8 z-10">
        {/* Left Column: Branding & Overview */}
        <div className="lg:col-span-5 flex flex-col justify-between py-2">
          <div>
            <div className="flex items-center gap-3 mb-6">
              <div className="h-11 w-11 rounded-xl bg-gradient-to-tr from-primary-600 to-sky-400 flex items-center justify-center shadow-lg shadow-primary-600/30">
                <Fuel className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                  FleetPanda <span className="text-xs bg-primary-950 text-primary-300 border border-primary-800/60 px-2 py-0.5 rounded-full font-mono">AI AGENT</span>
                </h1>
                <p className="text-xs text-slate-400">Voice & Chat Multi-Tenant Support Agent</p>
              </div>
            </div>

            <h2 className="text-3xl font-extrabold text-slate-100 tracking-tight leading-snug mb-4">
              Operational Intelligence & Automated Ticket Triage
            </h2>
            <p className="text-sm text-slate-400 leading-relaxed mb-6">
              Empowering dispatchers and CSMs with natural language Text-to-SQL querying, voice control, and deep multi-source triage across 12 fuel delivery tenants.
            </p>

            {/* Architecture Highlights */}
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <ShieldCheck className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Hard Multi-Tenant Isolation & MCP</h4>
                  <p className="text-xs text-slate-400">Deterministic AST verification, SQLite read-only authorizers, and Bearer token data segregation.</p>
                </div>
              </div>

              <div className="flex items-start gap-3 p-3 rounded-lg bg-slate-900/60 border border-slate-800">
                <Sparkles className="h-5 w-5 text-sky-400 shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-xs font-semibold text-slate-200">Speech-In & Neural Speech-Out</h4>
                  <p className="text-xs text-slate-400">Full duplex voice mode with real-time waveform visualizer and edge-tts neural synthesis.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
            <span>FastAPI + SQLite + MCP Server</span>
            <span>React 18 + Vite + shadcn</span>
          </div>
        </div>

        {/* Right Column: Login Form & Demo Accounts */}
        <div className="lg:col-span-7 flex flex-col gap-6">
          <Card className="glass-panel shadow-2xl border-slate-800">
            <CardHeader>
              <CardTitle>
                <Lock className="h-4 w-4 text-primary-400" />
                <span>Sign in to Support Portal</span>
              </CardTitle>
              <Badge variant="info">JWT Bearer Auth</Badge>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
                    <span>⚠️</span>
                    <span>{error}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 text-slate-400" />
                    <span>Email Address</span>
                  </label>
                  <Input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@fleetpanda.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1.5 flex items-center gap-1.5">
                    <Lock className="h-3.5 w-3.5 text-slate-400" />
                    <span>Password</span>
                  </label>
                  <Input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    required
                  />
                </div>

                <Button type="submit" variant="primary" className="w-full mt-2" isLoading={isLoading}>
                  Authenticate & Launch Agent
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Quick-Login Demo Accounts */}
          <Card className="bg-slate-900/50 border-slate-800">
            <CardHeader className="py-3">
              <CardTitle className="text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <Zap className="h-3.5 w-3.5 text-amber-400" />
                <span>1-Click Demo Profiles (Multi-Tenant Isolation Testing)</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 max-h-72 overflow-y-auto pr-1">
                {demoUsers.map((demo) => (
                  <button
                    key={demo.email}
                    onClick={() => quickLogin(demo)}
                    className="flex flex-col text-left p-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800/90 hover:border-primary-500/50 transition-all group active:scale-[0.98]"
                  >
                    <div className="flex items-center justify-between w-full mb-1">
                      <span className="text-xs font-semibold text-slate-200 group-hover:text-primary-400 transition-colors truncate">
                        {demo.name}
                      </span>
                      <Badge variant={demo.tenant_id === null ? 'purple' : 'default'} size="sm">
                        {demo.tenant_id === null ? 'Global' : `Tenant ${demo.tenant_id}`}
                      </Badge>
                    </div>
                    <span className="text-[11px] text-slate-500 truncate mb-1">{demo.email}</span>
                    <p className="text-[11px] text-slate-400 line-clamp-1">{demo.description}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

