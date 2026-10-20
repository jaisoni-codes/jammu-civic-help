"use client";

import { useState } from "react";
import Link from "next/link";
import { 
  Sliders, FastForward, Users, CheckCircle2, 
  XCircle, RotateCcw, AlertTriangle, ArrowRight, ShieldAlert 
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DemoControlPanel() {
  const [targetCode, setTargetCode] = useState("BH-0001");
  const [fastForwardHours, setFastForwardHours] = useState("24");
  const [simOutput, setSimOutput] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const simulateThreeComplaints = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/demo/simulate-complaint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ward_id: 1,
          category: "road_pothole",
          text: "Massive pothole near Purani Mandi chowk causing scooter falls.",
          citizen_count: 3
        }),
      });
      const data = await res.json();
      setSimOutput(data);
      if (data.ticket_code) setTargetCode(data.ticket_code);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const advanceTime = async (hours: number) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/demo/advance-time`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hours }),
      });
      setSimOutput(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const replyCitizen = async (result: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/demo/citizen-reply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: targetCode, result }),
      });
      setSimOutput(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const resetAll = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/demo/reset`, { method: "POST" });
      setSimOutput(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div className="bg-amber-50 border border-amber-300 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="bg-amber-500 text-white p-2 rounded-lg font-bold">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-black text-amber-950">90-Second Demo Master Control Panel</h1>
            <p className="text-xs text-amber-800">
              Control the entire civic accountability cycle live for hackathon evaluators without waiting for real days.
            </p>
          </div>
        </div>

        {/* 90-Second Script Stepper Guide */}
        <div className="mt-4 bg-white/80 p-4 rounded-xl border border-amber-200 text-xs text-slate-700 space-y-1">
          <p className="font-bold text-slate-900 mb-1">90-Second Hackathon Storyline:</p>
          <p>1. Tap <b>"Simulate 3 Nearby Reports"</b> → Watch 1 single ticket created with <i>3 Collective Voices</i>.</p>
          <p>2. Open <b>/officer</b> → View ticket with auto-calculated priority score & reasons.</p>
          <p>3. Officer uploads after-repair proof → Citizen receives WhatsApp verification prompt.</p>
          <p>4. Tap <b>"Citizen: NOT SOLVED (No)"</b> → Reopens ticket, escalates to Level 1, alerts EE.</p>
          <p>5. Re-resolve → Tap <b>"Citizen: SOLVED (Yes)"</b> → Verified Closed & Ward Trust Index increases live!</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Collective Voice Simulator */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-4 h-4 text-emerald-600" />
            1. Collective Voice (Duplicate Merge)
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            Simulates 3 distinct citizens within 40 meters reporting the same road pothole. The duplicate clustering engine coalesces them into 1 ticket with 3 voices.
          </p>
          <button 
            onClick={simulateThreeComplaints}
            disabled={loading}
            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold p-2.5 rounded-lg text-xs shadow flex items-center justify-center gap-1.5"
          >
            <Users className="w-4 h-4" /> Simulate 3 Nearby Reports
          </button>
        </div>

        {/* Time Fast-Forwarder */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <FastForward className="w-4 h-4 text-indigo-600" />
            2. Simulated Clock Fast-Forward
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            Fast-forward simulated clock to trigger 100% and 150% SLA breach escalations or 72-hour unverified auto-closures instantly.
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button onClick={() => advanceTime(24)} className="p-2 border rounded-lg text-xs font-bold hover:bg-slate-50">
              +24 Hours
            </button>
            <button onClick={() => advanceTime(48)} className="p-2 border rounded-lg text-xs font-bold hover:bg-slate-50">
              +48 Hours
            </button>
            <button onClick={() => advanceTime(72)} className="p-2 bg-indigo-50 border border-indigo-200 text-indigo-900 rounded-lg text-xs font-bold">
              +72 Hours (Auto-close)
            </button>
          </div>
        </div>

        {/* Citizen Verification Replier */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            3. Citizen Verification Simulator
          </h2>
          <p className="text-xs text-slate-500">
            Target Ticket: <input type="text" value={targetCode} onChange={(e) => setTargetCode(e.target.value.toUpperCase())} className="font-bold border px-1.5 py-0.5 rounded text-slate-900 text-xs w-28" />
          </p>
          <div className="flex gap-2">
            <button 
              onClick={() => replyCitizen("yes")}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold p-2.5 rounded-lg text-xs shadow flex items-center justify-center gap-1"
            >
              <CheckCircle2 className="w-4 h-4" /> Tap YES (Solved)
            </button>
            <button 
              onClick={() => replyCitizen("no")}
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold p-2.5 rounded-lg text-xs shadow flex items-center justify-center gap-1"
            >
              <XCircle className="w-4 h-4" /> Tap NO (Reopen)
            </button>
          </div>
        </div>

        {/* State Reset */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <RotateCcw className="w-4 h-4 text-slate-600" />
            4. Reset Demo State
          </h2>
          <p className="text-xs text-slate-500">
            Resets demo clock offset back to 0.0 and clears temporary simulator logs for repeated fresh pitch runs.
          </p>
          <button 
            onClick={resetAll}
            className="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold p-2.5 rounded-lg text-xs"
          >
            Reset Clock & Outbox
          </button>
        </div>
      </div>

      {/* Output Console */}
      {simOutput && (
        <div className="bg-slate-900 text-emerald-400 p-4 rounded-xl text-xs font-mono overflow-x-auto shadow">
          <span className="text-slate-400 block mb-1 text-[11px]">// Live Action Response:</span>
          {JSON.stringify(simOutput, null, 2)}
        </div>
      )}
    </div>
  );
}
