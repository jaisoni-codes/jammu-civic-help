"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Send, RotateCcw, Phone, Video, MoreVertical, ChevronLeft, Check, CheckCheck } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Exact ward centroids from DB — keeps routing accurate
const CITIZENS = [
  { id: "demo_citizen_jammu", name: "Rahul Sharma",  ward: "Ward 7 - Raghunath Bazaar",  lat: 32.7252, lng: 74.8605 },
  { id: "citizen_2",          name: "Priya Devi",    ward: "Ward 18 - Shastri Nagar",     lat: 32.7001, lng: 74.8580 },
  { id: "citizen_3",          name: "Mohd. Rafiq",   ward: "Ward 21 - Talab Tillo",       lat: 32.7230, lng: 74.8250 },
  { id: "citizen_4",          name: "Sunita Bhat",   ward: "Ward 12 - Gandhi Nagar",      lat: 32.7056, lng: 74.8622 },
];

const QUICK_MESSAGES = [
  { emoji: "🕳️", label: "Road Pothole",  text: "Bada sa gaddha hai main road pe, kafi accident ho rahe hain." },
  { emoji: "💡", label: "Streetlight",   text: "3 din se light nahi hai, raat ko bahut andhera rehta hai." },
  { emoji: "🗑️", label: "Garbage",       text: "5 din se kachra nahi utha, bahut smell aa rahi hai." },
  { emoji: "💧", label: "Water Supply",  text: "Kal se paani nahi aa raha hai, please jaldi bhejein." },
  { emoji: "🐕", label: "Stray Animals", text: "Bahut saare aawara kutte hain school ke pass, bachon ko khatra hai." },
  { emoji: "📋", label: "Status Check",  text: "status" },
];

interface ChatMsg {
  id: number;
  from: "user" | "bot";
  text: string;
  header?: string;
  buttons?: { id: string; title: string }[];
  media_url?: string;
  ts: string;
  delivered?: boolean;
}

export default function ChatSimulatorPage() {
  const [citizenIdx, setCitizenIdx] = useState(0);
  const [inputText, setInputText]   = useState("");
  const [chat, setChat]             = useState<ChatMsg[]>([]);
  const [sending, setSending]       = useState(false);
  const counterRef  = useRef(0);
  const bottomRef   = useRef<HTMLDivElement>(null);
  const inputRef    = useRef<HTMLInputElement>(null);
  const sendingRef  = useRef(false);   // prevents double-fire on send
  const pollingRef  = useRef(false);   // prevents concurrent outbox polls

  const citizen = CITIZENS[citizenIdx];

  const ts = () => {
    const d = new Date();
    return `${d.getHours().toString().padStart(2,"0")}:${d.getMinutes().toString().padStart(2,"0")}`;
  };

  const addMsg = useCallback((msg: Omit<ChatMsg,"id">) => {
    counterRef.current += 1;
    setChat(prev => [...prev, { ...msg, id: counterRef.current }]);
  }, []);

  // Single-flight outbox poll — only one request in flight at a time
  const pollOutbox = useCallback(async () => {
    if (pollingRef.current) return;
    pollingRef.current = true;
    try {
      const res = await fetch(`${API_BASE}/api/demo/outbox`, { cache: "no-store" });
      if (!res.ok) return;
      const data = await res.json();
      const msgs: any[] = data.messages || [];
      // Backend drains on GET, so these are always fresh messages
      msgs.forEach((m: any) => {
        addMsg({
          from: "bot",
          text: m.text || "",
          header: m.header,
          buttons: m.buttons,
          media_url: m.media_url,
          ts: ts(),
        });
      });
    } catch { /* ignore */ } finally {
      pollingRef.current = false;
    }
  }, [addMsg]);

  // Poll every 1.5 s — no extra polls on send (outbox is drain-on-read)
  useEffect(() => {
    const interval = setInterval(pollOutbox, 1500);
    return () => clearInterval(interval);
  }, [pollOutbox]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const sendMessage = async (textToSend?: string, buttonId?: string) => {
    const text = textToSend !== undefined ? textToSend : inputText.trim();
    if (!text && !buttonId) return;
    if (sendingRef.current) return;        // hard debounce
    sendingRef.current = true;

    if (text) addMsg({ from: "user", text, ts: ts(), delivered: true });
    setInputText("");
    setSending(true);

    try {
      await fetch(`${API_BASE}/webhook/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channel: "console",
          sender_id: citizen.id,           // correct citizen ID
          text: buttonId ? null : text,
          button_reply_id: buttonId || null,
          lat: citizen.lat,                // ← correct ward coordinates!
          lng: citizen.lng,
        }),
      });
    } catch (e) {
      console.error(e);
    } finally {
      setSending(false);
      sendingRef.current = false;
      inputRef.current?.focus();
    }
  };

  const handleClear = async () => {
    await fetch(`${API_BASE}/api/demo/reset`, { method: "POST" }).catch(() => {});
    setChat([]);
    counterRef.current = 0;
  };

  return (
    <div className="max-w-sm mx-auto" style={{ height: "calc(100vh - 64px)", display: "flex", flexDirection: "column" }}>

      {/* WhatsApp Header */}
      <div className="bg-[#075E54] text-white px-3 py-2 flex items-center gap-3 shadow-md shrink-0">
        <ChevronLeft className="w-5 h-5 opacity-80" />
        <div className="w-9 h-9 rounded-full bg-[#128C7E] flex items-center justify-center text-sm font-black shrink-0">JMC</div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-sm leading-tight">JMC Bharosa Helpline</p>
          <p className="text-[10px] opacity-75">🟢 Online · Jammu Smart City</p>
        </div>
        <div className="flex gap-3 opacity-80">
          <Video className="w-4 h-4" />
          <Phone className="w-4 h-4" />
          <MoreVertical className="w-4 h-4" />
        </div>
      </div>

      {/* Citizen selector */}
      <div className="bg-[#ECE5DD] px-3 py-1.5 border-b border-[#D1CBC3] flex items-center gap-2 shrink-0">
        <span className="text-[10px] font-semibold text-slate-500 shrink-0">Simulating as:</span>
        <select
          value={citizenIdx}
          onChange={e => {
            setCitizenIdx(Number(e.target.value));
            // Reset chat when switching citizen — new conversation
            setChat([]);
            counterRef.current = 0;
          }}
          className="text-[10px] bg-white border border-slate-200 rounded px-1.5 py-0.5 font-medium text-slate-700 outline-none flex-1"
        >
          {CITIZENS.map((c, i) => (
            <option key={c.id} value={i}>{c.name} ({c.ward})</option>
          ))}
        </select>
        <button onClick={handleClear} className="text-[10px] text-red-600 font-semibold flex items-center gap-0.5 shrink-0">
          <RotateCcw className="w-2.5 h-2.5" /> Reset
        </button>
      </div>

      {/* Quick buttons */}
      <div className="bg-[#ECE5DD] px-2 py-1.5 flex gap-1.5 overflow-x-auto border-b border-[#D1CBC3] shrink-0" style={{ scrollbarWidth: "none" }}>
        {QUICK_MESSAGES.map((q) => (
          <button
            key={q.label}
            onClick={() => sendMessage(q.text)}
            disabled={sending}
            className="flex-shrink-0 bg-white text-slate-700 text-[10px] font-semibold px-2.5 py-1 rounded-full border border-slate-200 hover:bg-[#128C7E] hover:text-white hover:border-[#128C7E] transition-all shadow-sm disabled:opacity-50"
          >
            {q.emoji} {q.label}
          </button>
        ))}
      </div>

      {/* Chat area */}
      <div
        className="flex-1 overflow-y-auto px-3 py-3 space-y-1.5"
        style={{ background: "#E5DDD5" }}
      >
        {chat.length === 0 && (
          <div className="flex justify-center mt-10">
            <div className="bg-[#FFF3CD] text-[#7D6608] text-[11px] font-medium px-4 py-2 rounded-lg text-center shadow-sm max-w-[240px]">
              🔒 Messages are end-to-end encrypted.<br />
              <b>{citizen.name}</b> is reporting from <b>{citizen.ward}</b>.<br />
              Send a complaint to start!
            </div>
          </div>
        )}

        {chat.map((msg) => (
          <div key={msg.id} className={`flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[78%] rounded-2xl px-3 py-2 shadow-sm text-xs relative ${
              msg.from === "user" ? "bg-[#DCF8C6] rounded-tr-none" : "bg-white rounded-tl-none"
            }`}>
              {msg.header && <p className="font-black text-slate-900 text-[11px] mb-1">{msg.header}</p>}
              <p className="text-slate-800 whitespace-pre-line leading-relaxed">{msg.text}</p>
              {msg.media_url && <img src={msg.media_url} alt="proof" className="rounded-lg mt-2 max-h-36 object-cover border" />}
              {msg.buttons && msg.buttons.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200 space-y-1.5">
                  {msg.buttons.map((b) => (
                    <button
                      key={b.id}
                      onClick={() => sendMessage(undefined, b.id)}
                      className="w-full text-center py-1.5 text-[#128C7E] font-bold text-[11px] hover:bg-slate-50 rounded transition border border-[#128C7E]/20"
                    >
                      {b.title}
                    </button>
                  ))}
                </div>
              )}
              <div className={`flex items-center gap-1 mt-1 ${msg.from === "user" ? "justify-end" : "justify-start"}`}>
                <span className="text-[9px] text-slate-400">{msg.ts}</span>
                {msg.from === "user" && (
                  msg.delivered
                    ? <CheckCheck className="w-3 h-3 text-[#34B7F1]" />
                    : <Check className="w-3 h-3 text-slate-400" />
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="bg-[#F0F0F0] px-2 py-2 flex items-center gap-2 border-t border-[#D1CBC3] shrink-0">
        <div className="flex-1 bg-white rounded-full px-4 py-2 flex items-center shadow-sm">
          <input
            ref={inputRef}
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); sendMessage(); } }}
            placeholder={`Message as ${citizen.name}...`}
            className="flex-1 text-xs outline-none bg-transparent text-slate-800 placeholder:text-slate-400"
          />
        </div>
        <button
          onClick={() => sendMessage()}
          disabled={sending || !inputText.trim()}
          className={`w-10 h-10 rounded-full flex items-center justify-center shadow transition ${
            inputText.trim() && !sending ? "bg-[#128C7E] hover:bg-[#075E54]" : "bg-slate-300"
          }`}
        >
          <Send className="w-4 h-4 text-white" />
        </button>
      </div>
    </div>
  );
}
