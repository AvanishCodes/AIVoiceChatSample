import React, { useState } from 'react';
import { LoginPage } from './components/auth/LoginPage';
import { ChatContainer } from './components/chat/ChatContainer';
import { Header } from './components/layout/Header';
import { SqlExplorer } from './components/sql/SqlExplorer';
import { TriageStudio } from './components/triage/TriageStudio';
import { VoiceHUD } from './components/voice/VoiceHUD';
import { useAuth } from './context/AuthContext';

export const App: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [activeMode, setActiveMode] = useState<'chat' | 'voice' | 'triage' | 'sql'>('chat');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#090d16] flex flex-col items-center justify-center text-slate-400 gap-3">
        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-mono">Initializing FleetPanda Support Agent...</span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return (
    <div className="min-h-screen bg-[#090d16] flex flex-col text-slate-100 antialiased">
      <Header activeMode={activeMode} onModeChange={setActiveMode} />

      <main className="flex-1">
        {activeMode === 'chat' && <ChatContainer />}
        {activeMode === 'voice' && <VoiceHUD />}
        {activeMode === 'triage' && <TriageStudio />}
        {activeMode === 'sql' && <SqlExplorer />}
      </main>
    </div>
  );
};

