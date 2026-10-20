"use client";

import { useState, useEffect } from "react";
import { 
  ShieldCheck, AlertTriangle, Users, Flame, 
  Send, BarChart3, RefreshCw, CheckCircle2 
} from "lucide-react";
import { fetchAdminOverview, fetchAdminHeatmap, officerLogin } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AdminHQPage() {
  const [token, setToken] = useState<string | null>(null);
  const [overview, setOverview] = useState<any>(null);
  const [heatmap, setHeatmap] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Broadcast composer
  const [broadcastWard, setBroadcastWard] = useState<number | "">("");
  const [broadcastTitle, setBroadcastTitle] = useState("Planned Power Maintenance in Ward 1");
  const [broadcastBody, setBroadcastBody] = useState("Power supply in Purani Mandi area will be suspended tomorrow from 10 AM to 1 PM for transformer upgrade.");
  const [broadcastMsg, setBroadcastMsg] = useState<string | null>(null);

  useEffect(() => {
    // Auto-login admin with seeded credentials for presentation
    adminAutoLogin();
  }, []);

  const adminAutoLogin = async () => {
    setLoading(true);
    try {
      const res = await officerLogin(12, "1234");
      setToken(res.access_token);
      loadDashboard(res.access_token);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboard = async (authToken: string) => {
    try {
      const [ov, hm] = await Promise.all([
        fetchAdminOverview(authToken),
        fetchAdminHeatmap(authToken)
      ]);
      setOverview(ov);
      setHeatmap(hm);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSendBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/admin/broadcasts`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          ward_id: broadcastWard ? Number(broadcastWard) : null,
          kind: "power",
          title: broadcastTitle,
          body: broadcastBody,
        }),
      });
      const data = await res.json();
      setBroadcastMsg(`✓ Broadcast dispatched to ${data.recipients} citizens (${data.delivered} delivered successfully)!`);
    } catch (err: any) {
      setBroadcastMsg("Failed to dispatch broadcast");
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Commissioner & Admin HQ</h1>
          <p className="text-xs text-slate-500">Real-time City Surveillance, Workload Management & Proactive Broadcasts</p>
        </div>
        <button onClick={() => token && loadDashboard(token)} className="text-xs font-semibold px-3 py-1.5 border bg-white rounded-lg shadow-sm flex items-center gap-1 self-start">
          <RefreshCw className="w-3.5 h-3.5" /> Refresh Realtime Data
        </button>
      </div>

      {/* KPI Cards */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-500 block">Total Active Complaints</span>
            <span className="text-2xl font-black text-slate-900">{overview.open_tickets}</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-500 block">Level 1 Escalated (EE)</span>
            <span className="text-2xl font-black text-amber-600">{overview.escalated_level_1}</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-500 block">Level 2 (Commissioner)</span>
            <span className="text-2xl font-black text-red-600">{overview.escalated_level_2}</span>
          </div>
          <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
            <span className="text-xs text-slate-500 block">Subscribed Citizens</span>
            <span className="text-2xl font-black text-emerald-600">{overview.total_citizens}</span>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Heatmap / Intensity List */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Flame className="w-4 h-4 text-orange-500" />
            Active Spatial Heatmap & Severity Clustered Points
          </h2>
          <p className="text-xs text-slate-500">
            Complaints dynamically weighted by proximity to hospitals/schools and citizen affected counts.
          </p>

          <div className="max-h-64 overflow-y-auto divide-y divide-slate-100 text-xs">
            {heatmap.slice(0, 8).map((pt, i) => (
              <div key={i} className="py-2.5 flex items-center justify-between">
                <div>
                  <span className="font-bold text-slate-800">{pt.code}</span>
                  <span className="text-slate-500 block text-[11px] capitalize">
                    {pt.category.replace(/_/g, " ")} • GPS ({pt.lat.toFixed(3)}, {pt.lng.toFixed(3)})
                  </span>
                </div>
                <div className="text-right">
                  <span className="font-bold text-amber-600">Priority {pt.priority_score}</span>
                  <span className="text-[10px] text-slate-400 block">Intensity {(pt.intensity * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Proactive Broadcast Composer */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Send className="w-4 h-4 text-emerald-600" />
            Dispatch Ward-Wise Citizen Broadcast
          </h2>
          <p className="text-xs text-slate-500">
            Reaches subscribed citizens across WhatsApp & Telegram in the selected ward.
          </p>

          {broadcastMsg && (
            <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-lg font-medium">
              {broadcastMsg}
            </div>
          )}

          <form onSubmit={handleSendBroadcast} className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Target Ward</label>
              <select 
                value={broadcastWard}
                onChange={(e) => setBroadcastWard(e.target.value ? Number(e.target.value) : "")}
                className="w-full text-xs p-2 border rounded-lg bg-slate-50"
              >
                <option value="">All Jammu Wards (City-wide)</option>
                <option value="1">Ward 1 - Old Heritage City / Purani Mandi</option>
                <option value="2">Ward 7 - Raghunath Bazaar</option>
                <option value="3">Ward 12 - Gandhi Nagar South</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Advisory Title</label>
              <input 
                type="text" 
                value={broadcastTitle} 
                onChange={(e) => setBroadcastTitle(e.target.value)}
                className="w-full text-xs p-2 border rounded-lg"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Advisory Message</label>
              <textarea 
                rows={3}
                value={broadcastBody} 
                onChange={(e) => setBroadcastBody(e.target.value)}
                className="w-full text-xs p-2 border rounded-lg"
              />
            </div>

            <button type="submit" className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold p-2.5 rounded-lg text-xs shadow">
              Send Proactive Broadcast
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
