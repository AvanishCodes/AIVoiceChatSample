import React, { useEffect, useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Code,
  Copy,
  Database,
  Download,
  Play,
  ShieldCheck,
  Sparkles,
  Table,
  Zap,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { BenchmarkItem, SqlQueryResult } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Input } from '../ui/Input';

export const SqlExplorer: React.FC = () => {
  const { user, activeTenantId, llmProvider } = useAuth();
  const [benchmarks, setBenchmarks] = useState<BenchmarkItem[]>([]);
  const [inputQuery, setInputQuery] = useState(
    'How many deliveries were completed in the last 7 days across all tenants?'
  );
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SqlQueryResult | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.getSqlBenchmarks()
      .then(setBenchmarks)
      .catch((e) => console.warn('Failed to load SQL benchmarks:', e));
  }, []);

  const handleRunQuery = async (queryText?: string) => {
    const q = queryText || inputQuery;
    if (!q.trim()) return;

    setIsLoading(true);
    try {
      const res = await api.executeSqlQuery(q, activeTenantId, llmProvider);
      setResult(res);
    } catch (err: any) {
      console.error('SQL Query Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const copySql = () => {
    if (!result?.sql) return;
    navigator.clipboard.writeText(result.sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const exportCsv = () => {
    if (!result?.results || result.results.length === 0) return;
    const cols = result.columns;
    const rows = result.results.map((r) =>
      cols.map((c) => JSON.stringify(r[c] ?? '')).join(',')
    );
    const csvContent = [cols.join(','), ...rows].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `fleetpanda_query_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-xl font-bold text-white tracking-tight">Dispatch Text-to-SQL Explorer</h1>
            <Badge variant="success">AST & Authorizer Protected</Badge>
          </div>
          <p className="text-xs text-slate-400">
            Query 90 days of operational dispatch data with hard multi-tenant isolation and zero data leakage.
          </p>
        </div>
      </div>

      {/* 1-Click Assignment 8 Benchmark Buttons */}
      <Card className="bg-slate-900/60 border-slate-800">
        <CardHeader className="py-3">
          <CardTitle className="text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            <span>The 8 SQL Benchmark Test Questions (Assignment Requirements)</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {benchmarks.map((b) => (
              <button
                key={b.id}
                onClick={() => {
                  setInputQuery(b.question);
                  handleRunQuery(b.question);
                }}
                className="flex flex-col text-left p-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800/90 hover:border-primary-500/50 transition-all group active:scale-[0.98]"
              >
                <div className="flex items-center justify-between w-full mb-1">
                  <span className="text-[11px] font-mono text-sky-400">Q{b.id}</span>
                  <Badge variant="default" size="sm">
                    {b.category}
                  </Badge>
                </div>
                <span className="text-xs font-semibold text-slate-200 group-hover:text-primary-400 transition-colors line-clamp-2">
                  {b.question}
                </span>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Query Input Box */}
      <Card className="border-slate-800">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            <Input
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleRunQuery()}
              placeholder="Enter natural language dispatch question or raw SQL..."
              className="text-sm font-medium"
            />
            <Button
              variant="primary"
              onClick={() => handleRunQuery()}
              isLoading={isLoading}
              className="shrink-0"
            >
              <Play className="h-4 w-4 mr-1.5 fill-current" /> Run Query
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results Section */}
      {result && (
        <div className="space-y-4">
          {/* SQL Code Box & Summary */}
          <Card className="glass-panel border-primary-500/30 overflow-hidden shadow-xl">
            <div className="px-5 py-3 border-b border-slate-800/80 bg-slate-950/60 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
                <Code className="h-4 w-4 text-sky-400" />
                <span>Sanitized SQL (Executed via MCP Layer)</span>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={copySql}>
                  <Copy className="h-3 w-3 mr-1" />
                  {copied ? 'Copied' : 'Copy SQL'}
                </Button>
                {result.results.length > 0 && (
                  <Button variant="outline" size="sm" onClick={exportCsv}>
                    <Download className="h-3 w-3 mr-1" /> Export CSV
                  </Button>
                )}
              </div>
            </div>

            <CardContent className="p-4 space-y-3">
              {/* Warnings / Error banner */}
              {result.error && (
                <div className="p-3 rounded-lg bg-rose-950/70 border border-rose-800/80 text-rose-300 text-xs flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <span>{result.error}</span>
                </div>
              )}

              {result.warnings && result.warnings.length > 0 && (
                <div className="p-2.5 rounded-lg bg-amber-950/50 border border-amber-800/60 text-amber-300 text-xs">
                  {result.warnings.map((w, i) => (
                    <div key={i} className="flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5 text-amber-400" />
                      <span>{w}</span>
                    </div>
                  ))}
                </div>
              )}

              <pre className="text-xs font-mono text-emerald-400 bg-black/60 p-3 rounded-lg overflow-x-auto border border-slate-800">
                {result.sql}
              </pre>

              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <span>{result.explanation}</span>
                <div className="flex items-center gap-3">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-sky-400" /> {result.execution_time_ms} ms
                  </span>
                  <span className="font-semibold text-slate-300">
                    {result.row_count} rows returned
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Interactive Data Table */}
          {result.results && result.results.length > 0 ? (
            <Card className="border-slate-800 overflow-hidden shadow-lg">
              <CardHeader className="py-3">
                <CardTitle className="text-xs uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <Table className="h-3.5 w-3.5 text-primary-400" />
                  <span>Query Results Table ({result.row_count} records)</span>
                </CardTitle>
              </CardHeader>
              <div className="overflow-x-auto max-h-96">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-900/90 text-slate-300 sticky top-0 border-b border-slate-800">
                    <tr>
                      {result.columns.map((col) => (
                        <th key={col} className="px-4 py-2.5 font-semibold font-mono tracking-tight">
                          {col}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-[#0d1322]/50">
                    {result.results.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/40 transition-colors">
                        {result.columns.map((col) => (
                          <td key={col} className="px-4 py-2 text-slate-200 font-mono">
                            {row[col] === null ? (
                              <span className="text-slate-600 italic">null</span>
                            ) : typeof row[col] === 'number' ? (
                              row[col].toLocaleString()
                            ) : (
                              String(row[col])
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          ) : !result.error ? (
            <div className="p-6 text-center text-xs text-slate-500 bg-slate-900/30 rounded-xl border border-slate-800">
              Query executed successfully, 0 rows returned.
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

