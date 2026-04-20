"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { fetchConfigStatus, sendChat, fetchSessions, fetchSessionHistory, type ChatResult } from "@/utils/api";

type Msg = {
  role: "user" | "assistant";
  text: string;
  meta?: ChatResult;
  isError?: boolean;
};

const SESSION_KEY = "mas_session_id";

function agentLabel(agent?: string | null) {
  switch (agent) {
    case "technical":
      return "Technical";
    case "billing":
      return "Billing";
    case "rag":
      return "Knowledge (RAG)";
    case "escalation":
      return "Escalation";
    default:
      return "Assistant";
  }
}

export default function Chat() {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [llmReady, setLlmReady] = useState<boolean | null>(null);
  const [llmProvider, setLlmProvider] = useState<string | null>(null);
  const [sessions, setSessions] = useState<{session_id: string, title: string, ts: string}[]>([]);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    void fetchSessions().then(setSessions);
  }, []);

  useEffect(() => {
    const existing = sessionStorage.getItem(SESSION_KEY);
    if (existing) {
      setSessionId(existing);
      void loadSession(existing);
    }
  }, []);

  useEffect(() => {
    void fetchConfigStatus().then((c) => {
      setLlmReady(c.llm_configured);
      setLlmProvider(c.llm_provider ?? null);
    });
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const loadSession = useCallback(async (id: string) => {
    setSessionId(id);
    sessionStorage.setItem(SESSION_KEY, id);
    setLoading(true);
    try {
      const history = await fetchSessionHistory(id);
      setMessages(history as any); // map to messages
    } catch(e) {
      console.error("Failed to load session history", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const onSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setError(null);
    setMessages((m) => [...m, { role: "user", text }]);
    setLoading(true);
    try {
      const result = await sendChat({ message: text, session_id: sessionId });
      if (!sessionId) {
        sessionStorage.setItem(SESSION_KEY, result.session_id);
        setSessionId(result.session_id);
        void fetchSessions().then(setSessions);
      }
      setMessages((m) => [...m, { role: "assistant", text: result.answer, meta: result }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setError(msg);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: `${msg}\n\nSetup: in project root .env set GEMINI_API_KEY (Gemini) or OPENAI_API_KEY (OpenAI), save, restart uvicorn. See .env.example.`,
          isError: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, sessionId]);

  const clearSession = () => {
    sessionStorage.removeItem(SESSION_KEY);
    setSessionId(null);
    setMessages([]);
    setError(null);
  };

  return (
    <div className="flex min-h-screen bg-[#0B0F19] text-gray-200 font-sans">
      {/* Sidebar */}
      <aside className="w-72 bg-[#10141F] flex flex-col p-4 border-r border-gray-800 hidden md:flex">
        {/* Brand */}
        <div className="flex items-center gap-2 mb-8 px-2">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#A855F7" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
          <span className="text-xl font-bold text-white tracking-wide">CelestAI</span>
        </div>

        {/* New Chat Button */}
        <button 
          onClick={clearSession}
          className="bg-gradient-to-r from-[#8B5CF6] to-[#A855F7] hover:from-[#7C3AED] hover:to-[#9333EA] text-white rounded-full py-3 px-4 flex items-center justify-center gap-2 transition-all mb-8 shadow-[0_0_15px_rgba(168,85,247,0.4)]"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
          <span className="font-medium text-sm w-full text-center pr-4">New Chat</span>
        </button>

        {/* History dynamic */}
        <div className="flex-1 overflow-y-auto space-y-6 scrollbar-thin scrollbar-thumb-gray-800">
          <div>
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">Recent Chats</h3>
            <div className="space-y-1">
              {sessions.map(s => (
                <div 
                  key={s.session_id} 
                  onClick={() => void loadSession(s.session_id)} 
                  className={`flex items-center justify-between p-2 rounded-xl cursor-pointer text-sm font-medium transition-colors ${sessionId === s.session_id ? 'bg-white/10 text-white' : 'hover:bg-white/5 text-gray-400'}`}
                >
                  <span className="truncate">{s.title}</span>
                </div>
              ))}
              {sessions.length === 0 && (
                <div className="text-xs text-gray-600 italic px-2">No past chats found.</div>
              )}
            </div>
          </div>
        </div>

        {/* User Profile */}
        <div className="mt-4 flex items-center justify-between p-2 hover:bg-white/5 rounded-xl cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-orange-400 to-purple-500 flex items-center justify-center text-white font-bold text-xs shadow-md">
              <img src="https://ui-avatars.com/api/?name=Karina&background=random&color=fff" alt="User" className="w-full h-full rounded-full object-cover" />
            </div>
            <span className="text-sm font-medium text-gray-200">Karina</span>
          </div>
          <div className="w-6 h-6 rounded-full border border-gray-700 flex items-center justify-center text-[10px] text-gray-500">D</div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative w-full h-screen">
        
        {/* Error logic overlay (if needed) */}
        {llmReady === false && (
          <div className="absolute top-4 left-1/2 -translate-x-1/2 rounded-lg border border-amber-500/30 bg-black/60 px-4 py-2 text-xs text-amber-200 backdrop-blur z-10 w-max shadow-lg">
            Backend missing keys. Set GEMINI_API_KEY in .env and restart uvicorn.
          </div>
        )}
        
        {error && (
          <div className="absolute top-14 left-1/2 -translate-x-1/2 rounded-lg border border-red-500/50 bg-red-950/80 px-4 py-2 text-xs text-red-200 backdrop-blur z-10 w-max shadow-lg">
            {error}
          </div>
        )}
        
        <div className="flex-1 overflow-y-auto px-4 sm:px-8 pb-32">
          <div className="max-w-4xl mx-auto w-full h-full flex flex-col">
          
            {messages.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center mt-[-10vh]">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#A855F7" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="mb-6 opacity-80"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                <div className="text-gray-400 text-lg mb-2">
                  Good Evening, <span className="text-[#A855F7]">Karina</span>
                </div>
                <h1 className="text-4xl sm:text-5xl font-bold text-white mb-6 tracking-tight">
                  How can I help you?
                </h1>
                <p className="text-gray-500 text-sm max-w-md text-center mb-12">
                  It all starts with a prompt. Write your own request or get inspired by one of the suggested ones.
                </p>
                
                {/* Embedded input for empty state */}
                <div className="w-full max-w-2xl bg-[#1A1D27] rounded-full flex items-center p-2 shadow-[0_4px_30px_rgba(0,0,0,0.5)] border border-[#232734]">
                  <div className="flex items-center gap-3 pl-4 pr-2 text-gray-500">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                  </div>
                  <input
                    className="flex-1 bg-transparent text-gray-200 placeholder-gray-500 outline-none px-2 py-3 text-sm h-full"
                    placeholder="Type a prompt..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        void onSend();
                      }
                    }}
                    disabled={loading}
                    autoFocus
                  />
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => void onSend()}
                      disabled={loading || !input.trim()}
                      className="w-10 h-10 rounded-full bg-[#8B5CF6] hover:bg-[#7C3AED] text-white flex items-center justify-center transition-colors disabled:opacity-50 shrink-0 shadow-lg shadow-purple-500/20"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
                    </button>
                    <button className="w-10 h-10 rounded-full bg-[#232734] hover:bg-[#2C3140] text-gray-400 flex items-center justify-center transition-colors shrink-0 mr-1">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
                    </button>
                  </div>
                </div>
                
                {/* Suggestions Grid */}
                <div className="mt-8 grid grid-cols-2 lg:flex lg:flex-wrap justify-center gap-3 max-w-3xl">
                  {["Let's talk about...", "Help me with...", "Teach me to...", "Analyse this topic...", "Write a story about..."].map((suggestion, idx) => (
                    <button 
                      key={idx}
                      onClick={() => {
                        setInput(suggestion);
                        setTimeout(() => onSend(), 0);
                      }}
                      className="bg-[#10141F] hover:bg-[#232734] border border-[#232734] text-gray-400 hover:text-gray-200 text-xs px-4 py-2.5 rounded-full flex items-center gap-2 transition-colors whitespace-nowrap shadow-sm"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex-1 py-8 space-y-8">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    {m.role === "assistant" && (
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#8B5CF6] to-[#0B0F19] flex items-center justify-center mr-3 shrink-0 shadow-lg border border-purple-500/20">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                        m.role === "user"
                          ? "bg-gradient-to-r from-[#8B5CF6] to-[#A855F7] text-white rounded-br-sm shadow-[0_4px_15px_rgba(168,85,247,0.15)]"
                          : m.isError
                            ? "bg-red-950/20 border border-red-900/40 text-red-300 rounded-bl-sm"
                            : "bg-[#1A1D27] border border-[#232734] text-gray-300 rounded-bl-sm"
                      }`}
                    >
                      {m.role === "assistant" && m.isError && (
                        <div className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-red-400">
                          Could not reach the AI
                        </div>
                      )}
                      {m.role === "assistant" && m.meta && !m.isError && (
                        <div className="mb-3 flex flex-wrap gap-2 text-[10px] uppercase tracking-wider text-gray-500">
                          <span className="rounded bg-black/40 px-2 py-0.5 border border-white/5">
                            {agentLabel(m.meta.agent)}
                          </span>
                          {m.meta.escalated && (
                            <span className="rounded bg-amber-950/40 px-2 py-0.5 text-amber-500 border border-amber-900/40">
                              Escalated
                            </span>
                          )}
                          {m.meta.sources?.length ? (
                            <span className="rounded bg-black/40 px-2 py-0.5 border border-white/5">
                              Sources: {m.meta.sources.join(", ")}
                            </span>
                          ) : null}
                        </div>
                      )}
                      <p className="whitespace-pre-wrap">{m.text}</p>
                    </div>
                  </div>
                ))}
                
                {loading && (
                  <div className="flex justify-start opacity-70">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#8B5CF6] to-[#0B0F19] flex items-center justify-center mr-3 shrink-0 shadow-lg border border-purple-500/20">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                    </div>
                    <div className="rounded-2xl rounded-bl-sm bg-[#1A1D27] border border-[#232734] px-5 py-4 text-sm text-gray-400">
                      <span className="animate-pulse tracking-widest text-[#A855F7] font-bold">...</span>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} className="h-4" />
              </div>
            )}
          </div>
        </div>

        {/* Input area positioned at bottom when chatting */}
        {messages.length > 0 && (
          <div className="absolute bottom-0 left-0 right-0 p-4 pb-6 bg-gradient-to-t from-[#0B0F19] via-[#0B0F19] to-transparent pointer-events-none">
             <div className="max-w-3xl mx-auto shadow-2xl shadow-[#0B0F19] pointer-events-auto">
                <div className="w-full bg-[#1A1D27] rounded-full flex items-center p-2 shadow-[0_4px_30px_rgba(0,0,0,0.5)] border border-[#232734]">
                  <div className="flex items-center gap-3 pl-4 pr-2 text-gray-500">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                  </div>
                  <input
                    className="flex-1 bg-transparent text-gray-200 placeholder-gray-500 outline-none px-2 py-3 text-sm h-full"
                    placeholder="Type a prompt..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        void onSend();
                      }
                    }}
                    disabled={loading}
                  />
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => void onSend()}
                      disabled={loading || !input.trim()}
                      className="w-10 h-10 rounded-full bg-[#8B5CF6] hover:bg-[#7C3AED] text-white flex items-center justify-center transition-colors disabled:opacity-50 shrink-0 shadow-lg shadow-purple-500/20"
                    >
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
                    </button>
                    <button className="w-10 h-10 rounded-full bg-[#232734] hover:bg-[#2C3140] text-gray-400 flex items-center justify-center transition-colors shrink-0 mr-1">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>
                    </button>
                  </div>
                </div>
                <div className="text-center mt-3 text-[10px] text-gray-500 font-medium">
                  CelestAI can make mistakes. Consider verifying critical information.
                </div>
             </div>
          </div>
        )}
      </main>
    </div>
  );
}
