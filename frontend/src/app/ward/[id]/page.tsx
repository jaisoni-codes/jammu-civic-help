"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft, ShieldCheck, Sparkles, RefreshCw,
  Clock, Users, TrendingUp, TrendingDown, Minus,
  CheckCircle, AlertCircle, Banknote, BarChart3, MapPin
} from "lucide-react";
import { fetchWardDetails } from "@/lib/api";

const COMPONENT_META = [
  { key: "response",      label: "Response Speed",      weight: "15%", icon: Clock,        desc: "Median first-response vs 24h benchmark",     color: "blue"    },
  { key: "closure",       label: "Verified Closures",   weight: "25%", icon: CheckCircle,  desc: "% tickets closed within SLA with GPS proof",  color: "emerald" },
  { key: "reopen",        label: "Reopen Protection",   weight: "15%", icon: ShieldCheck,  desc: "Inverse of citizen reopen rate (lower = bad)", color: "violet"  },
  { key: "satisfaction",  label: "Citizen Satisfaction",weight: "20%", icon: Sparkles,     desc: "Avg. star rating after verified closure",      color: "amber"   },
  { key: "proactive",     label: "Proactive Alerts",    weight: "10%", icon: BarChart3,    desc: "Water/power/road broadcasts × delivery rate",  color: "cyan"    },
  { key: "participation", label: "Participation",       weight: "15%", icon: Users,        desc: "Active reporters / subscribed citizens ÷ 20%", color: "rose"    },
];

const COLOR_MAP: Record<string, string> = {
  blue:    "bg-blue-50 border-blue-100 text-blue-700",
  emerald: "bg-emerald-50 border-emerald-100 text-emerald-700",
  violet:  "bg-violet-50 border-violet-100 text-violet-700",
  amber:   "bg-amber-50 border-amber-100 text-amber-700",
  cyan:    "bg-cyan-50 border-cyan-100 text-cyan-700",
  rose:    "bg-rose-50 border-rose-100 text-rose-700",
};

function ScoreBar({ value }: { value: number | null }) {
  if (value === null) return <span className="text-xs text-slate-400 italic">No data</span>;
  const pct = Math.round(value * 100);
  const color = pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-400" : "bg-red-400";
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-lg font-black text-slate-900">{pct}%</span>
      </div>
      <div className="w-full bg-slate-200 rounded-full h-1.5">
        <div className={`${color} h-1.5 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function TrustBadge({ score }: { score: number }) {
  if (score >= 75) return <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-2 py-0.5 rounded-full">🏆 Excellent</span>;
  if (score >= 55) return <span className="bg-amber-100 text-amber-800 text-xs font-bold px-2 py-0.5 rounded-full">👍 Good</span>;
  if (score >= 35) return <span className="bg-orange-100 text-orange-800 text-xs font-bold px-2 py-0.5 rounded-full">⚠️ Fair</span>;
  return <span className="bg-red-100 text-red-800 text-xs font-bold px-2 py-0.5 rounded-full">🔴 Poor</span>;
}

function TrendIcon({ history }: { history: any[] }) {
  if (!history || history.length < 3) return <Minus className="w-4 h-4 text-slate-400" />;
  const last = history[history.length - 1]?.score ?? 0;
  const prev = history[history.length - 4]?.score ?? 0;
  if (last > prev + 1) return <TrendingUp className="w-4 h-4 text-emerald-600" />;
  if (last < prev - 1) return <TrendingDown className="w-4 h-4 text-red-500" />;
  return <Minus className="w-4 h-4 text-slate-400" />;
}

const STATUS_CFG: Record<string, { color: string; label: string }> = {
  open:        { color: "bg-blue-100 text-blue-800",    label: "Open" },
  assigned:    { color: "bg-indigo-100 text-indigo-800",label: "Assigned" },
  in_progress: { color: "bg-amber-100 text-amber-800",  label: "In Progress" },
  reopened:    { color: "bg-red-100 text-red-800",      label: "Reopened ⚠️" },
};

const PROJECT_STATUS_CFG: Record<string, { color: string; label: string }> = {
  voting:      { color: "bg-blue-100 text-blue-800",    label: "🗳️ Voting Open" },
  funded:      { color: "bg-indigo-100 text-indigo-800",label: "💰 Funded" },
  in_progress: { color: "bg-amber-100 text-amber-800",  label: "🔨 In Progress" },
  completed:   { color: "bg-emerald-100 text-emerald-800", label: "✅ Completed" },
  verified:    { color: "bg-green-100 text-green-800",  label: "🏅 Verified" },
};

export default function WardDetailPage() {
  const params = useParams();
  const wardId = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"issues" | "projects" | "wins">("issues");

  const loadWard = async () => {
    try {
      setLoading(true);
      const res = await fetchWardDetails(wardId);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (wardId) loadWard();
  }, [wardId]);

  if (loading || !data) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-3" />
        <p className="text-slate-600">Loading Ward Analytics...</p>
      </div>
    );
  }

  const comps = data.components || {};
  const openTickets: any[] = (data.open_tickets || []).slice(0, 10);
  const projects: any[] = data.projects || [];
  const wins: any[] = data.recent_wins || [];

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">

      {/* Back */}
      <Link href="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to City Trust Overview
      </Link>

      {/* Ward Hero */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-extrabold">{data.name}</h1>
            <TrustBadge score={data.trust_index} />
          </div>
          <p className="text-slate-300 text-sm">
            Pop. est. {data.population_est?.toLocaleString()} · {data.open_tickets_count ?? openTickets.length} active issues
          </p>
          <div className="flex items-center gap-2 mt-2">
            <TrendIcon history={data.history} />
            <span className="text-xs text-slate-400">30-day trend</span>
          </div>
        </div>
        <div className="bg-white/10 border border-white/20 p-4 rounded-xl text-center min-w-[140px]">
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-300 block">Trust Score</span>
          <span className="text-5xl font-black text-white">{data.trust_index}</span>
          <span className="text-sm text-slate-400 font-bold">/100</span>
        </div>
      </div>

      {/* 6-Component Grid */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 mb-4 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Trust Index — 6-Component Breakdown (Trailing 30 Days)
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {COMPONENT_META.map(({ key, label, weight, icon: Icon, desc, color }) => (
            <div key={key} className={`p-3 rounded-xl border ${COLOR_MAP[color]}`}>
              <div className="flex items-center gap-1.5 mb-2">
                <Icon className="w-3.5 h-3.5" />
                <span className="text-[10px] font-bold uppercase tracking-wide">{label}</span>
                <span className="ml-auto text-[9px] font-black opacity-60">{weight}</span>
              </div>
              <ScoreBar value={comps[key] ?? null} />
              <p className="text-[10px] opacity-70 mt-1 leading-tight">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* 30-Day Trend Chart */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
        <h2 className="text-sm font-bold text-slate-900 mb-1">30-Day Trust Trajectory</h2>
        <p className="text-[11px] text-slate-400 mb-3">Hover bars to see exact score & date</p>
        <div className="h-32 flex items-end gap-1 border-b border-l border-slate-200 px-1">
          {(data.history || []).slice(-30).map((h: any, i: number) => {
            const pct = Math.max(6, Math.min(100, (h.score / 100) * 100));
            const clr = h.score >= 70 ? "bg-emerald-500" : h.score >= 50 ? "bg-amber-400" : "bg-red-400";
            return (
              <div key={i} className="flex-1 flex flex-col items-center group relative">
                <div
                  className={`w-full ${clr} rounded-t hover:opacity-80 transition cursor-pointer`}
                  style={{ height: `${pct}%` }}
                />
                <span className="opacity-0 group-hover:opacity-100 absolute -top-9 bg-slate-900 text-white text-[9px] px-1.5 py-0.5 rounded shadow pointer-events-none whitespace-nowrap z-10">
                  {h.date?.slice(5)}: <b>{h.score}</b>
                </span>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-[10px] text-slate-400 mt-1">
          <span>30 days ago</span><span>Today</span>
        </div>
      </div>

      {/* Tabs: Issues | Projects | Wins */}
      <div>
        <div className="flex gap-1 bg-slate-100 p-1 rounded-xl mb-4">
          {[
            { key: "issues",   label: "🚨 Active Issues",      count: openTickets.length },
            { key: "projects", label: "🏗️ Mohalla Budget",    count: projects.length },
            { key: "wins",     label: "🏅 Verified Wins",      count: wins.length },
          ].map(({ key, label, count }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key as any)}
              className={`flex-1 py-2 px-2 rounded-lg text-xs font-bold transition ${
                activeTab === key ? "bg-white shadow text-slate-900" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {label}
              <span className={`ml-1.5 text-[10px] px-1.5 py-0.5 rounded-full ${
                activeTab === key ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-500"
              }`}>{count}</span>
            </button>
          ))}
        </div>

        {/* Active Issues */}
        {activeTab === "issues" && (
          <div className="space-y-2">
            {openTickets.length === 0 ? (
              <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-6 text-center text-sm text-emerald-700 font-semibold">
                🎉 No active issues! This ward is doing great.
              </div>
            ) : openTickets.map((t: any) => (
              <Link
                key={t.id || t.code}
                href={`/t/${t.code}`}
                className="block bg-white rounded-xl border border-slate-200 p-3.5 hover:border-slate-400 hover:shadow-sm transition"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-black text-slate-900 text-sm">{t.code}</span>
                    {t.status && (
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${STATUS_CFG[t.status]?.color || "bg-slate-100 text-slate-600"}`}>
                        {STATUS_CFG[t.status]?.label || t.status}
                      </span>
                    )}
                    {t.escalation_level > 0 && (
                      <span className="bg-red-600 text-white text-[9px] font-black px-1.5 py-0.5 rounded">L{t.escalation_level} ESC</span>
                    )}
                  </div>
                  <span className={`text-base font-black shrink-0 ${
                    (t.priority_score || 0) >= 70 ? "text-red-600" :
                    (t.priority_score || 0) >= 50 ? "text-amber-600" : "text-emerald-600"
                  }`}>
                    {t.priority_score ?? "—"}
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-1 capitalize">
                  {t.category?.replace(/_/g, " ")}
                  {t.affected_count > 1 && <span className="ml-2 text-indigo-600 font-semibold">👥 {t.affected_count} affected</span>}
                </p>
              </Link>
            ))}
            {(data.open_tickets_count ?? 0) > openTickets.length && (
              <p className="text-xs text-slate-400 text-center pt-1">
                Showing top 10 of {data.open_tickets_count} active issues
              </p>
            )}
          </div>
        )}

        {/* Mohalla Budget Projects */}
        {activeTab === "projects" && (
          <div className="space-y-2">
            {projects.length === 0 ? (
              <div className="bg-slate-50 border rounded-xl p-6 text-center text-sm text-slate-500">
                No Mohalla Budget projects for this ward yet.
              </div>
            ) : projects.map((p: any) => (
              <div key={p.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-bold text-slate-900 text-sm">{p.title}</p>
                    <p className="text-xs text-slate-500 mt-0.5">{p.description}</p>
                  </div>
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-full whitespace-nowrap ${
                    PROJECT_STATUS_CFG[p.status]?.color || "bg-slate-100 text-slate-600"
                  }`}>
                    {PROJECT_STATUS_CFG[p.status]?.label || p.status}
                  </span>
                </div>
                <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1 font-semibold text-slate-700">
                    <Banknote className="w-3.5 h-3.5 text-emerald-600" />
                    ₹{(p.est_cost / 100000).toFixed(1)}L est.
                  </span>
                  {p.vote_count != null && (
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" /> {p.vote_count} votes
                    </span>
                  )}
                  <span className="ml-auto text-[10px]">Cycle: {p.cycle}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Verified Wins */}
        {activeTab === "wins" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {wins.length === 0 ? (
              <div className="col-span-2 bg-slate-50 border rounded-xl p-6 text-center text-sm text-slate-500">
                No verified closures in this cycle yet.
              </div>
            ) : wins.map((w: any) => (
              <div key={w.code} className="bg-emerald-50 border border-emerald-100 rounded-xl p-4">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-black text-slate-900">{w.code}</span>
                  <span className="text-[10px] text-emerald-600 font-bold bg-emerald-100 px-2 py-0.5 rounded-full">
                    ✓ Verified
                  </span>
                </div>
                <p className="text-xs text-slate-600 capitalize">{w.category?.replace(/_/g, " ")}</p>
                <p className="text-[11px] text-emerald-700 font-semibold mt-2">
                  Confirmed by {w.affected_count} {w.affected_count === 1 ? "citizen" : "citizens"}
                </p>
                <Link href={`/t/${w.code}`} className="text-xs text-emerald-800 underline font-semibold mt-1.5 inline-block">
                  View Audit Chain →
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
