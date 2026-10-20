"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ShieldCheck, UserCheck, BarChart3, Zap, Search, X } from "lucide-react";
import LanguageSelector from "./LanguageSelector";

export default function Navbar() {
  const router = useRouter();
  const [showTrack, setShowTrack] = useState(false);
  const [trackCode, setTrackCode] = useState("");
  const [trackError, setTrackError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (showTrack) setTimeout(() => inputRef.current?.focus(), 50);
  }, [showTrack]);

  const handleTrack = (e: React.FormEvent) => {
    e.preventDefault();
    const code = trackCode.trim().toUpperCase();
    if (!code) { setTrackError("Please enter your complaint ID"); return; }
    setShowTrack(false);
    setTrackCode("");
    setTrackError("");
    router.push(`/t/${code}`);
  };

  return (
    <>
      <header className="border-b bg-white sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between gap-2">
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="bg-emerald-600 text-white p-2 rounded-lg font-bold shadow-md">
              <ShieldCheck className="w-6 h-6 inline-block" />
            </div>
            <div>
              <span className="font-extrabold text-xl tracking-tight text-slate-900 block leading-tight">
                CivicHelp <span className="text-xs bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-semibold ml-1">Jammu</span>
              </span>
              <span className="text-xs text-slate-500 font-medium hidden sm:block">Jammu Smart City Civic Trust Engine</span>
            </div>
          </Link>

          <nav className="flex items-center gap-1 sm:gap-2 text-sm font-semibold">
            <Link href="/" className="text-slate-700 hover:text-emerald-700 px-2 py-1 flex items-center gap-1.5 text-xs sm:text-sm">
              <BarChart3 className="w-4 h-4" /> <span className="hidden sm:inline">City Trust</span>
            </Link>
            <Link href="/officer" className="text-slate-700 hover:text-emerald-700 px-2 py-1 flex items-center gap-1.5 text-xs sm:text-sm">
              <UserCheck className="w-4 h-4" /> <span className="hidden sm:inline">Officer</span>
            </Link>

            {/* Track & Feedback Button */}
            <button
              onClick={() => { setShowTrack(true); setTrackError(""); }}
              className="flex items-center gap-1.5 text-xs font-bold px-3 py-1.5 rounded-lg border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition shrink-0"
            >
              <Search className="w-3.5 h-3.5 text-slate-500" />
              <span className="hidden sm:inline">Track &amp; Feedback</span>
              <span className="sm:hidden">Track</span>
            </button>

            {/* Report Issue */}
            <Link href="/report" className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold shadow flex items-center gap-1.5 shrink-0">
              <Zap className="w-3.5 h-3.5" /> <span className="hidden sm:inline">Report Issue</span>
              <span className="sm:hidden">Report</span>
            </Link>

            {/* Language Selector */}
            <div className="ml-1 shrink-0">
              <LanguageSelector />
            </div>
          </nav>
        </div>
      </header>

      {/* Track & Feedback Modal */}
      {showTrack && (
        <div
          className="fixed inset-0 z-[100] bg-black/50 backdrop-blur-sm flex items-start justify-center pt-24 px-4"
          onClick={() => setShowTrack(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md p-6 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-black text-slate-900">Track Your Complaint</h2>
                <p className="text-xs text-slate-500 mt-0.5">Enter your unique complaint ID to view status and give feedback</p>
              </div>
              <button onClick={() => setShowTrack(false)} className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleTrack} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Complaint Tracking ID</label>
                <input
                  ref={inputRef}
                  type="text"
                  value={trackCode}
                  onChange={(e) => { setTrackCode(e.target.value.toUpperCase()); setTrackError(""); }}
                  placeholder="e.g. JMC-ROA-0042 or BH-0012"
                  className="w-full border border-slate-300 rounded-xl p-3 text-sm font-mono font-bold tracking-wide outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50 focus:bg-white uppercase"
                />
                {trackError && <p className="text-xs text-red-600 mt-1 font-medium">{trackError}</p>}
              </div>
              <button
                type="submit"
                className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl text-sm shadow flex items-center justify-center gap-2 transition"
              >
                <Search className="w-4 h-4" /> View Complaint Status & Give Feedback
              </button>
            </form>

            <p className="text-[11px] text-slate-400 text-center">
              Your complaint ID was shown after submission on the report confirmation screen.
            </p>
          </div>
        </div>
      )}
    </>
  );
}
