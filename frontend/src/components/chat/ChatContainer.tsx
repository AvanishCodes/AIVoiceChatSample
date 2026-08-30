import React, { useEffect, useRef, useState } from 'react';
import { Bot, Check, Copy, Database, Fuel, Mic, MicOff, Paperclip, Play, Send, Sparkles, User, Volume2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { audioService } from '../../services/audio';
import { ChatMessage, SqlQueryResult, TicketBrief } from '../../types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';

export const ChatContainer: React.FC = () => {
  const { user, activeTenantId, llmProvider } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      role: 'assistant',
      content:
        "👋 **Welcome to FleetPanda AI Support Agent!**\n\nI can answer **dispatch database questions** (e.g. *'How many deliveries were completed in the last 7 days?'*) or **triage incoming support tickets** from any of our 12 fuel delivery tenants.\n\nType a question below or tap the microphone to speak.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [autoPlayVoice, setAutoPlayVoice] = useState(true);
  const [playingMsgId, setPlayingMsgId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || inputValue;
    if (!query.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const resp = await api.sendChatMessage(
        query,
        activeTenantId,
        llmProvider,
        autoPlayVoice
      );

      const botMsg: ChatMessage = {
        id: `msg-resp-${Date.now()}`,
        role: 'assistant',
        content: resp.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        sqlResult: resp.sql_result,
        ticketBrief: resp.ticket_brief,
        audioBase64: resp.audio_base64,
      };

      setMessages((prev) => [...prev, botMsg]);

      // Auto-play audio if available
      if (autoPlayVoice && resp.audio_base64) {
        setPlayingMsgId(botMsg.id);
        audioService.playAudioBase64(resp.audio_base64, () => setPlayingMsgId(null));
      } else if (autoPlayVoice && !resp.audio_base64) {
        setPlayingMsgId(botMsg.id);
        audioService.speakBrowserTTS(resp.reply, () => setPlayingMsgId(null));
      }
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: `msg-err-${Date.now()}`,
        role: 'assistant',
        content: `❌ **Error**: ${err.message || 'Failed to process request.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMicToggle = async () => {
    if (isRecording) {
      audioService.stopSpeechRecognition();
      setIsRecording(false);
      try {
        const audioBlob = await audioService.stopRecording();
        if (audioBlob.size > 0) {
          setIsLoading(true);
          const resp = await api.sendVoiceMessage(audioBlob, activeTenantId, llmProvider);
          const botMsg: ChatMessage = {
            id: `msg-voice-${Date.now()}`,
            role: 'assistant',
            content: resp.reply,
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            sqlResult: resp.sql_result,
            ticketBrief: resp.ticket_brief,
            audioBase64: resp.audio_base64,
          };
          setMessages((prev) => [...prev, botMsg]);
          if (resp.audio_base64) {
            setPlayingMsgId(botMsg.id);
            audioService.playAudioBase64(resp.audio_base64, () => setPlayingMsgId(null));
          }
          setIsLoading(false);
        }
      } catch (err: any) {
        console.warn('Voice recording upload error:', err);
        setIsLoading(false);
      }
    } else {
      setIsRecording(true);
      if (audioService.isSpeechRecognitionSupported()) {
        audioService.startSpeechRecognition(
          (transcribedText, isFinal) => {
            setInputValue(transcribedText);
            if (isFinal) {
              setIsRecording(false);
              handleSend(transcribedText);
            }
          },
          (err) => {
            console.warn('Speech recognition error:', err);
            setIsRecording(false);
          }
        );
      } else {
        await audioService.startRecording();
      }
    }
  };

  const playMessageAudio = (msg: ChatMessage) => {
    if (playingMsgId === msg.id) {
      audioService.stopAudio();
      setPlayingMsgId(null);
      return;
    }
    setPlayingMsgId(msg.id);
    if (msg.audioBase64) {
      audioService.playAudioBase64(msg.audioBase64, () => setPlayingMsgId(null));
    } else {
      audioService.speakBrowserTTS(msg.content, () => setPlayingMsgId(null));
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] max-w-5xl mx-auto w-full px-4 py-4">
      {/* Quick Prompts Bar */}
      <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1 text-xs no-scrollbar">
        <span className="text-slate-500 shrink-0 flex items-center gap-1 font-medium">
          <Sparkles className="h-3 w-3 text-sky-400" /> Try:
        </span>
        <button
          onClick={() => handleSend('How many deliveries were completed in the last 7 days?')}
          className="shrink-0 bg-slate-900/80 hover:bg-slate-800 text-slate-300 px-3 py-1.5 rounded-full border border-slate-800 hover:border-primary-500/40 transition-all"
        >
          Deliveries in last 7 days
        </button>
        <button
          onClick={() => handleSend('Which tenant delivered the most gallons of diesel last month?')}
          className="shrink-0 bg-slate-900/80 hover:bg-slate-800 text-slate-300 px-3 py-1.5 rounded-full border border-slate-800 hover:border-primary-500/40 transition-all"
        >
          Top diesel tenant last month
        </button>
        <button
          onClick={() => handleSend('Show me the top 5 drivers by total deliveries for tenant 3')}
          className="shrink-0 bg-slate-900/80 hover:bg-slate-800 text-slate-300 px-3 py-1.5 rounded-full border border-slate-800 hover:border-primary-500/40 transition-all"
        >
          Top drivers for tenant 3
        </button>
        <button
          onClick={() => handleSend('Which trucks are currently in maintenance status?')}
          className="shrink-0 bg-slate-900/80 hover:bg-slate-800 text-slate-300 px-3 py-1.5 rounded-full border border-slate-800 hover:border-primary-500/40 transition-all"
        >
          Trucks in maintenance
        </button>
      </div>

      {/* Messages Timeline */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 mb-3">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.role === 'assistant' && (
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-primary-600 to-sky-500 flex items-center justify-center shrink-0 shadow-md shadow-primary-600/20 mt-1">
                <Bot className="h-4 w-4 text-white" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl p-4 transition-all shadow-sm ${
                msg.role === 'user'
                  ? 'bg-primary-600 text-white rounded-tr-sm'
                  : 'bg-[#111827] border border-slate-800/80 text-slate-100 rounded-tl-sm'
              }`}
            >
              {/* Message Content */}
              <div className="text-sm whitespace-pre-wrap leading-relaxed">
                {msg.content}
              </div>

              {/* Inline SQL Result Accordion */}
              {msg.sqlResult && msg.sqlResult.sql && (
                <div className="mt-3 p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-xs font-mono">
                  <div className="flex items-center justify-between text-slate-400 mb-1.5 pb-1 border-b border-slate-800">
                    <span className="flex items-center gap-1.5 text-sky-400 font-semibold">
                      <Database className="h-3.5 w-3.5" /> Generated SQL ({msg.sqlResult.execution_time_ms}ms)
                    </span>
                    <span className="text-[10px] text-slate-500">{msg.sqlResult.row_count} rows returned</span>
                  </div>
                  <pre className="text-slate-300 overflow-x-auto p-1 bg-black/30 rounded">{msg.sqlResult.sql}</pre>
                </div>
              )}

              {/* Message Footer: Audio Playback & Timestamp */}
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-700/30 text-[10px] text-slate-400">
                <span>{msg.timestamp}</span>
                {msg.role === 'assistant' && (
                  <button
                    onClick={() => playMessageAudio(msg)}
                    className="flex items-center gap-1 hover:text-sky-300 transition-colors p-1 rounded hover:bg-slate-800/60"
                    title={playingMsgId === msg.id ? 'Stop Speech' : 'Play Voice'}
                  >
                    <Volume2 className={`h-3.5 w-3.5 ${playingMsgId === msg.id ? 'text-sky-400 animate-pulse' : ''}`} />
                    <span>{playingMsgId === msg.id ? 'Speaking...' : 'Listen'}</span>
                  </button>
                )}
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="h-8 w-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 shadow-sm mt-1">
                <User className="h-4 w-4 text-slate-300" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start items-center text-slate-400 text-xs p-2">
            <div className="h-8 w-8 rounded-lg bg-primary-600/30 flex items-center justify-center animate-pulse">
              <Bot className="h-4 w-4 text-primary-400" />
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce" />
              <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce [animation-delay:0.2s]" />
              <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce [animation-delay:0.4s]" />
              <span>Querying dispatch intelligence & executing MCP tools...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="relative glass-panel rounded-xl p-2 border-slate-800">
        <div className="flex items-center gap-2">
          {/* Voice Mic Button */}
          <button
            onClick={handleMicToggle}
            className={`p-2.5 rounded-lg transition-all flex items-center justify-center ${
              isRecording
                ? 'bg-rose-600 text-white shadow-lg shadow-rose-600/40 animate-pulse'
                : 'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'
            }`}
            title={isRecording ? 'Stop Recording' : 'Speak to Agent'}
          >
            {isRecording ? <Mic className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={isRecording ? 'Listening to speech...' : "Ask a dispatch database question or paste a support ticket..."}
            className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
            disabled={isLoading}
          />

          {/* Auto Voice Toggle */}
          <button
            onClick={() => setAutoPlayVoice(!autoPlayVoice)}
            className={`p-2 text-xs rounded-lg flex items-center gap-1 transition-all ${
              autoPlayVoice ? 'text-primary-400 bg-primary-950/60 border border-primary-800/40' : 'text-slate-500 hover:text-slate-300'
            }`}
            title="Toggle Voice Speech Output"
          >
            <Volume2 className="h-4 w-4" />
          </button>

          {/* Send Button */}
          <Button
            variant="primary"
            size="md"
            onClick={() => handleSend()}
            disabled={!inputValue.trim() || isLoading}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

