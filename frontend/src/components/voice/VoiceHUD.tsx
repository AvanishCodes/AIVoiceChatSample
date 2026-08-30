import React, { useEffect, useState } from 'react';
import { Bot, Mic, MicOff, Sparkles, Volume2, VolumeX, Zap } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { audioService } from '../../services/audio';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Card, CardContent } from '../ui/Card';

type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';

export const VoiceHUD: React.FC = () => {
  const { activeTenantId, llmProvider } = useAuth();
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [transcript, setTranscript] = useState<string>('');
  const [agentResponse, setAgentResponse] = useState<string>('');
  const [lastExecutedSql, setLastExecutedSql] = useState<string | null>(null);
  const [micError, setMicError] = useState<string | null>(null);

  const startListening = async () => {
    setVoiceState('listening');
    setTranscript('');
    setAgentResponse('');
    setLastExecutedSql(null);
    setMicError(null);

    if (audioService.isSpeechRecognitionSupported()) {
      audioService.startSpeechRecognition(
        (text, isFinal) => {
          setTranscript(text);
          if (isFinal) {
            processVoiceQuery(text);
          }
        },
        (err) => {
          console.warn('Voice error:', err);
          setVoiceState('idle');
          if (err === 'not-allowed' || err?.name === 'NotAllowedError') {
            setMicError(
              'Microphone access was blocked (not-allowed). Please click the Lock 🔒 or Mic 🎙️ icon in your address bar and grant permission.'
            );
          }
        }
      );
    } else {
      // Fallback MediaRecorder
      try {
        await audioService.startRecording();
      } catch (e: any) {
        setVoiceState('idle');
        setMicError('Microphone permission blocked. Please allow microphone access in your browser settings.');
      }
    }
  };

  const stopListening = async () => {
    if (voiceState === 'listening') {
      audioService.stopSpeechRecognition();
      if (!audioService.isSpeechRecognitionSupported()) {
        setVoiceState('processing');
        try {
          const blob = await audioService.stopRecording();
          const resp = await api.sendVoiceMessage(blob, activeTenantId, llmProvider);
          handleAgentResult(resp);
        } catch (e) {
          console.error(e);
          setVoiceState('idle');
        }
      }
    }
  };

  const processVoiceQuery = async (queryText: string) => {
    setVoiceState('processing');
    try {
      const resp = await api.sendChatMessage(queryText, activeTenantId, llmProvider, true);
      handleAgentResult(resp);
    } catch (err: any) {
      setAgentResponse(`Error: ${err.message}`);
      setVoiceState('idle');
    }
  };

  const handleAgentResult = (resp: any) => {
    setAgentResponse(resp.reply);
    if (resp.sql_result && resp.sql_result.sql) {
      setLastExecutedSql(resp.sql_result.sql);
    }
    setVoiceState('speaking');

    if (resp.audio_base64) {
      audioService.playAudioBase64(resp.audio_base64, () => setVoiceState('idle'));
    } else {
      audioService.speakBrowserTTS(resp.reply, () => setVoiceState('idle'));
    }
  };

  const handleQuickPrompt = (promptText: string) => {
    setTranscript(promptText);
    processVoiceQuery(promptText);
  };

  return (
    <div className="flex flex-col items-center justify-between min-h-[calc(100vh-4rem)] max-w-4xl mx-auto px-4 py-8">
      {/* Top Banner */}
      <div className="text-center mb-6">
        <Badge variant="info" size="md" className="mb-2">
          Voice Mode (Speech-In / Speech-Out)
        </Badge>
        <h2 className="text-2xl font-bold text-white tracking-tight">
          FleetPanda AI Voice Dispatch Assistant
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Tap the voice orb below to speak your question or ticket brief request.
        </p>

        {micError && (
          <div className="mt-3 p-3 rounded-lg bg-amber-950/80 border border-amber-800/80 text-amber-200 text-xs text-left max-w-md mx-auto">
            <span className="font-semibold block mb-1">⚠️ Microphone Permission Blocked:</span>
            <span>{micError}</span>
          </div>
        )}
      </div>

      {/* Center Interactive Voice Orb */}
      <div className="relative flex flex-col items-center justify-center my-auto">
        {/* Glow rings */}
        <div
          className={`absolute w-72 h-72 rounded-full transition-all duration-700 pointer-events-none ${
            voiceState === 'listening'
              ? 'bg-rose-500/20 scale-125 animate-ping'
              : voiceState === 'processing'
              ? 'bg-amber-500/20 scale-110 animate-pulse'
              : voiceState === 'speaking'
              ? 'bg-sky-500/20 scale-125 animate-pulse'
              : 'bg-primary-600/10 scale-90'
          }`}
        />

        <div
          className={`absolute w-56 h-56 rounded-full transition-all duration-500 pointer-events-none ${
            voiceState === 'listening'
              ? 'bg-rose-500/30'
              : voiceState === 'processing'
              ? 'bg-amber-500/30'
              : voiceState === 'speaking'
              ? 'bg-sky-500/30'
              : 'bg-primary-500/10'
          }`}
        />

        {/* Main Microphone Orb Button */}
        <button
          onClick={voiceState === 'listening' ? stopListening : startListening}
          className={`relative z-10 w-36 h-36 rounded-full flex flex-col items-center justify-center transition-all duration-300 shadow-2xl active:scale-95 ${
            voiceState === 'listening'
              ? 'bg-gradient-to-tr from-rose-600 to-red-500 text-white shadow-rose-500/50'
              : voiceState === 'processing'
              ? 'bg-gradient-to-tr from-amber-600 to-yellow-500 text-white shadow-amber-500/50 animate-pulse'
              : voiceState === 'speaking'
              ? 'bg-gradient-to-tr from-sky-600 to-cyan-500 text-white shadow-sky-500/50'
              : 'bg-gradient-to-tr from-primary-600 to-sky-500 text-white hover:shadow-primary-500/40 hover:scale-105'
          }`}
        >
          {voiceState === 'listening' ? (
            <Mic className="h-12 w-12 animate-bounce" />
          ) : voiceState === 'processing' ? (
            <Zap className="h-12 w-12 animate-spin" />
          ) : voiceState === 'speaking' ? (
            <Volume2 className="h-12 w-12 animate-pulse" />
          ) : (
            <Mic className="h-12 w-12" />
          )}
          <span className="text-[11px] font-semibold uppercase tracking-wider mt-2">
            {voiceState === 'listening'
              ? 'Listening...'
              : voiceState === 'processing'
              ? 'Analyzing...'
              : voiceState === 'speaking'
              ? 'Speaking...'
              : 'Tap to Speak'}
          </span>
        </button>

        {/* Live Audio Wave Bars Visualizer */}
        <div className="flex items-center gap-1.5 mt-8 h-8">
          {[40, 75, 100, 60, 90, 45, 80, 60, 95, 30].map((h, i) => (
            <div
              key={i}
              className={`w-1.5 rounded-full transition-all duration-200 ${
                voiceState === 'listening'
                  ? 'bg-rose-400 animate-pulse'
                  : voiceState === 'speaking'
                  ? 'bg-sky-400 animate-pulse'
                  : 'bg-slate-800'
              }`}
              style={{
                height: voiceState === 'listening' || voiceState === 'speaking' ? `${(h * Math.sin(i + 1) + 50)}%` : '8px',
                animationDelay: `${i * 0.1}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* Transcript & Response Area */}
      <div className="w-full space-y-4 max-w-2xl mt-6">
        {/* User Speech Transcript */}
        {transcript && (
          <Card className="bg-slate-900/80 border-slate-800 p-4">
            <div className="text-xs font-semibold text-slate-400 mb-1 flex items-center gap-1.5">
              <Mic className="h-3.5 w-3.5 text-rose-400" />
              <span>You said:</span>
            </div>
            <p className="text-sm text-slate-100 italic">"{transcript}"</p>
          </Card>
        )}

        {/* Agent Response Card */}
        {agentResponse && (
          <Card className="glass-panel border-primary-500/30 p-5 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-sky-400" />
                <span className="text-xs font-bold text-slate-200">Agent Voice Answer</span>
              </div>
              <Badge variant="success">Synthesized Neural Speech</Badge>
            </div>
            <p className="text-sm text-slate-100 whitespace-pre-wrap leading-relaxed">
              {agentResponse}
            </p>

            {lastExecutedSql && (
              <div className="mt-3 pt-3 border-t border-slate-800/80">
                <span className="text-[11px] font-mono text-slate-400 block mb-1">Executed SQL:</span>
                <pre className="text-xs font-mono text-emerald-400 bg-black/40 p-2 rounded overflow-x-auto">
                  {lastExecutedSql}
                </pre>
              </div>
            )}
          </Card>
        )}

        {/* 1-Click Voice Test Scenarios */}
        <div className="pt-2">
          <span className="text-xs text-slate-500 block mb-2 font-medium">Or speak one of these quick test queries:</span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            <button
              onClick={() => handleQuickPrompt('How many deliveries were completed in the last 7 days?')}
              className="text-left text-xs p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-all hover:border-primary-500/40"
            >
              🎙️ "How many deliveries were completed in the last 7 days?"
            </button>
            <button
              onClick={() => handleQuickPrompt('Show me the top 5 drivers by total deliveries for tenant 3')}
              className="text-left text-xs p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-800 border border-slate-800 text-slate-300 transition-all hover:border-primary-500/40"
            >
              🎙️ "Top 5 drivers for tenant 3"
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

