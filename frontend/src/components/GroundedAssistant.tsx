import React, { useState } from 'react';
import { Bot, Send, ShieldCheck, Database, Sparkles, CheckCircle2 } from 'lucide-react';
import type { GroundedAssistantResponse } from '../types';
import { API_BASE } from '../config/api';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  grounded?: boolean;
  citations?: string[];
  data?: any;
  timestamp: string;
}

export const GroundedAssistant: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'm-0',
      sender: 'assistant',
      text: 'Greetings Operator & Traffic Controller. I am the VisionGuard Grounded AI Assistant. You can ask queries regarding license plates, camera congestion, speeding incidents, E-Challans, emergency green corridors, or watchlist alerts. All answers are strictly grounded in deterministic database facts with full legal citations.',
      grounded: true,
      citations: ['SYSTEM_CORE: Database Grounding Active', 'POLICY: Zero Hallucination Mode', 'LEGAL: Motor Vehicles Act 2019 Rules'],
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sampleQueries = [
    'Where was plate DL 01 AB 1234 last seen?',
    'Show active E-Challans and penalties',
    'Clear emergency green corridor for ambulance',
    'Which camera has highest congestion?',
    'Show me all speeding incidents today',
    'What is the status of Camera 1?',
  ];

  const handleSend = async (queryText?: string) => {
    const q = queryText || inputQuery;
    if (!q.trim() || isLoading) return;

    const userMsg: Message = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/assistant/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, user_role: 'traffic_controller_police' }),
      });
      const data: GroundedAssistantResponse = await res.json();

      const assistantMsg: Message = {
        id: `a-${Date.now()}`,
        sender: 'assistant',
        text: data.answer,
        grounded: data.grounded,
        citations: data.citations,
        data: data.data,
        timestamp: new Date().toLocaleTimeString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev,
        {
          id: `a-${Date.now()}`,
          sender: 'assistant',
          text: 'Unable to reach the VisionGuard query backend. Please ensure the server is active.',
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Left Quick Prompts & Grounding Guarantee */}
      <div className="lg:col-span-1 space-y-4">
        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <div className="flex items-center gap-2 mb-2">
            <ShieldCheck className="w-5 h-5 text-[var(--color-forest)]" />
            <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
              GROUNDING GUARANTEE
            </h3>
          </div>
          <p className="text-xs text-[var(--color-text-muted)] leading-relaxed mb-3">
            In compliance with Stage 10 (SIH26127), every generated traffic response is grounded directly against verified SQL/spatial database records to prevent AI hallucinations.
          </p>

          <div className="space-y-1.5 text-[11px] font-mono text-[var(--color-text-muted)] pt-2 border-t border-[var(--color-border-subtle)]">
            <div className="flex items-center gap-1.5 text-[var(--color-forest)]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Deterministic Database Execution</span>
            </div>
            <div className="flex items-center gap-1.5 text-[var(--color-forest)]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Full Audit Trail Logging</span>
            </div>
            <div className="flex items-center gap-1.5 text-[var(--color-forest)]">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Zero-Hallucination Guardrails</span>
            </div>
          </div>
        </div>

        {/* Quick Sample Prompts */}
        <div className="classic-card p-4 bg-[var(--color-surface)]">
          <h4 className="text-xs font-bold text-[var(--color-brown)] font-serif mb-2">
            SUGGESTED OPERATOR QUERIES
          </h4>
          <div className="space-y-2">
            {sampleQueries.map((sq, i) => (
              <button
                key={i}
                onClick={() => handleSend(sq)}
                className="w-full text-left p-2 rounded text-xs bg-[var(--color-canvas-alt)] hover:bg-[var(--color-surface-hover)] border border-[var(--color-border-subtle)] transition-colors text-[var(--color-text-main)]"
              >
                {sq}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right Chat Pane */}
      <div className="lg:col-span-3 classic-card p-4 bg-[var(--color-surface)] flex flex-col h-[600px]">
        {/* Chat Header */}
        <div className="flex items-center justify-between pb-3 border-b border-[var(--color-border-subtle)] mb-4">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-[var(--color-forest)]" />
            <h3 className="font-bold text-sm text-[var(--color-forest)] font-serif">
              CONVERSATIONAL TRAFFIC INTELLIGENCE CONSOLE
            </h3>
          </div>
          <span className="badge-forest text-[10px]">CONNECTED TO LIVE DATABASE</span>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
          {messages.map((m) => {
            const isUser = m.sender === 'user';
            return (
              <div
                key={m.id}
                className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
              >
                <div
                  className={`max-w-xl rounded-lg p-3 text-xs leading-relaxed ${
                    isUser
                      ? 'bg-[var(--color-forest)] text-white'
                      : 'bg-[var(--color-canvas-alt)] text-[var(--color-text-main)] border border-[var(--color-border-subtle)]'
                  }`}
                >
                  <p className="whitespace-pre-line">{m.text}</p>

                  {/* Citations Box for Assistant */}
                  {!isUser && m.citations && m.citations.length > 0 && (
                    <div className="mt-2.5 pt-2 border-t border-[var(--color-border-subtle)] text-[10px] font-mono text-[var(--color-text-muted)] space-y-0.5">
                      <div className="font-bold flex items-center gap-1 text-[var(--color-brown)]">
                        <Database className="w-3 h-3" />
                        <span>DATA CITATIONS & PROVENANCE:</span>
                      </div>
                      {m.citations.map((c, idx) => (
                        <div key={idx} className="pl-3 border-l-2 border-[var(--color-brown)]">
                          {c}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <span className="text-[10px] text-[var(--color-text-faint)] mt-1 px-1 font-mono">
                  {m.timestamp}
                </span>
              </div>
            );
          })}

          {isLoading && (
            <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] font-mono">
              <Sparkles className="w-4 h-4 text-[var(--color-gold)] animate-spin" />
              <span>Querying verified database records & computing spatial graph...</span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="pt-3 border-t border-[var(--color-border-subtle)] flex items-center gap-2">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask anything about vehicles, congestion, cameras, or alerts..."
            className="flex-1 px-3 py-2 text-xs rounded border border-[var(--color-border-subtle)] bg-[var(--color-canvas-alt)] focus:outline-none focus:border-[var(--color-forest)]"
          />
          <button
            onClick={() => handleSend()}
            disabled={isLoading || !inputQuery.trim()}
            className="btn-classic-forest text-xs px-4 py-2"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Send Query</span>
          </button>
        </div>
      </div>
    </div>
  );
};
