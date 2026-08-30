import React, { useEffect, useState } from 'react';
import { Bot, Cpu, Fuel, LogOut, Mic, ShieldCheck, User, Users } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { CustomerProfile } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

interface HeaderProps {
  activeMode: 'chat' | 'voice' | 'triage' | 'sql';
  onModeChange: (mode: 'chat' | 'voice' | 'triage' | 'sql') => void;
}

export const Header: React.FC<HeaderProps> = ({ activeMode, onModeChange }) => {
  const { user, logout, activeTenantId, setActiveTenantId, llmProvider, setLlmProvider } = useAuth();
  const [tenants, setTenants] = useState<CustomerProfile[]>([]);

  useEffect(() => {
    api.getTenants()
      .then(setTenants)
      .catch((e) => console.warn('Failed to load tenants list:', e));
  }, []);

  const isTenantScoped = user?.tenant_id !== null && user?.tenant_id !== undefined;

  return (
    <header className="h-16 bg-[#0d1322]/90 border-b border-slate-800/80 backdrop-blur-md px-5 flex items-center justify-between z-30 sticky top-0">
      {/* Brand & Mode Switcher */}
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-tr from-primary-600 to-sky-400 flex items-center justify-center shadow-md shadow-primary-600/20">
            <Fuel className="h-5 w-5 text-white" />
          </div>
          <div>
            <span className="font-bold text-sm text-white tracking-tight flex items-center gap-1.5">
              FleetPanda <span className="text-[10px] text-sky-400 font-mono">SUPPORT AI</span>
            </span>
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
              <ShieldCheck className="h-3 w-3 text-emerald-400" />
              <span>MCP Multi-Tenant Isolated</span>
            </div>
          </div>
        </div>

        {/* Navigation / Mode Switcher */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => onModeChange('chat')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeMode === 'chat'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            Chat Mode
          </button>
          <button
            onClick={() => onModeChange('voice')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all flex items-center gap-1.5 ${
              activeMode === 'voice'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Mic className="h-3 w-3 text-red-400 animate-pulse" />
            Voice HUD
          </button>
          <button
            onClick={() => onModeChange('triage')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeMode === 'triage'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            Ticket Triage
          </button>
          <button
            onClick={() => onModeChange('sql')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
              activeMode === 'sql'
                ? 'bg-primary-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            Dispatch SQL
          </button>
        </nav>
      </div>

      {/* Tenant Context, LLM Selector, and User Info */}
      <div className="flex items-center gap-3">
        {/* LLM Provider Selector */}
        <div className="hidden sm:flex items-center gap-1.5 bg-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-800">
          <Cpu className="h-3.5 w-3.5 text-sky-400" />
          <span className="text-[11px] text-slate-400 font-medium">Model:</span>
          <select
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.target.value)}
            className="bg-transparent text-xs text-slate-200 font-semibold focus:outline-none cursor-pointer"
          >
            <option value="ollama" className="bg-slate-900 text-slate-200">Ollama (Default / Local)</option>
            <option value="openai" className="bg-slate-900 text-slate-200">OpenAI (GPT-4o)</option>
            <option value="gemini" className="bg-slate-900 text-slate-200">Gemini (1.5 Pro)</option>
            <option value="anthropic" className="bg-slate-900 text-slate-200">Anthropic (Claude 3.5)</option>
          </select>
        </div>

        {/* Tenant Context Filter */}
        <div className="flex items-center gap-1.5 bg-slate-900 px-2.5 py-1.5 rounded-lg border border-slate-800">
          <Users className="h-3.5 w-3.5 text-amber-400" />
          <span className="text-[11px] text-slate-400 font-medium">Scope:</span>
          {isTenantScoped ? (
            <Badge variant="warning" size="sm">
              Tenant {user?.tenant_id} ({user?.tenant_name?.split(' ')[0]})
            </Badge>
          ) : (
            <select
              value={activeTenantId === null ? '' : String(activeTenantId)}
              onChange={(e) => setActiveTenantId(e.target.value ? Number(e.target.value) : null)}
              className="bg-transparent text-xs text-slate-200 font-semibold focus:outline-none cursor-pointer"
            >
              <option value="" className="bg-slate-900 text-slate-200">Global (All 12 Tenants)</option>
              {tenants.map((t) => (
                <option key={t.tenant_id} value={t.tenant_id} className="bg-slate-900 text-slate-200">
                  Tenant {t.tenant_id} — {t.name} (Health: {t.health_score})
                </option>
              ))}
            </select>
          )}
        </div>

        {/* User Badge & Logout */}
        <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
          <div className="hidden lg:flex flex-col text-right">
            <span className="text-xs font-semibold text-slate-200 leading-tight">{user?.name}</span>
            <span className="text-[10px] text-slate-400">{user?.role?.toUpperCase()}</span>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Sign Out">
            <LogOut className="h-4 w-4 text-slate-400 hover:text-rose-400 transition-colors" />
          </Button>
        </div>
      </div>
    </header>
  );
};

