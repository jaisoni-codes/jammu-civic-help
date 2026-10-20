"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  ShieldCheck, ArrowUpRight, TrendingUp, Award, 
  CheckCircle2, AlertCircle, RefreshCw, MapPin, 
  Clock, Users, Flame, ChevronRight
} from "lucide-react";
import { fetchCityOverview } from "@/lib/api";

export default function CityOverviewPage() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchCityOverview();
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-3" />
        <p className="text-slate-600 font-semibold text-sm">Aggregating Municipal Data Across 10 Jammu Wards...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-red-600">
        <AlertCircle className="w-10 h-10 mx-auto mb-2" />
        <p className="font-bold">Failed to load civic data</p>
        <button onClick={loadData} className="mt-4 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      
      {/* ── Modern Civic Hero ── */}
      <div className="relative overflow-hidden rounded-3xl bg-slate-950 text-white p-6 sm:p-10 border border-slate-800 shadow-2xl">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-emerald-900/40 via-transparent to-transparent pointer-events-none" />
        
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-8">
          <div className="max-w-2xl space-y-3">
            <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Civic Dashboard · Jammu Smart City
            </div>
            
            <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight text-white">
              Public Ward Trust Index
            </h1>
            
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              Real-time municipal performance benchmark for Jammu. Every grievance requires field photo evidence, GPS verification, and citizen confirmation before closure.
            </p>

            <div className="pt-2 flex flex-wrap gap-3">
              <Link 
                href="/report" 
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs sm:text-sm flex items-center gap-2 shadow-lg transition"
              >
                Report Ground Issue <ChevronRight className="w-4 h-4" />
              </Link>
              <Link 
                href="/officer" 
                className="bg-white/10 hover:bg-white/15 text-white font-semibold px-4 py-2.5 rounded-xl text-xs sm:text-sm border border-white/20 transition"
              >
                Officer Portal
              </Link>
            </div>
          </div>

          {/* City Score Meter */}
          <div className="bg-slate-900/90 border border-slate-700/80 p-6 rounded-2xl text-center min-w-[220px] shadow-xl backdrop-blur-md">
            <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400 block mb-1">
              Overall City Trust Score
            </span>
            <div className="text-6xl font-black text-white tracking-tight flex items-baseline justify-center gap-1">
              {data.city_trust_index}
              <span className="text-xl text-slate-400 font-semibold">/100</span>
            </div>
            <div className="mt-3 pt-3 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
              <span>Trailing 30-Day Evaluation</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Key Metrics Grid ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold block">TOTAL GRIEVANCES</span>
          <p className="text-3xl font-black text-slate-900 mt-1">{data.total_tickets}</p>
          <p className="text-[11px] text-slate-400 mt-1">Logged across all departments</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold block">ACTIVE UNDER WORK</span>
          <p className="text-3xl font-black text-amber-600 mt-1">{data.open_tickets}</p>
          <p className="text-[11px] text-amber-700/80 font-medium mt-1">Assigned to field engineers</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold block">VERIFIED CLOSURES</span>
          <p className="text-3xl font-black text-emerald-600 mt-1">{data.verified_closed}</p>
          <p className="text-[11px] text-emerald-700/80 font-semibold mt-1">✓ Citizen & GPS confirmed</p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold block">MUNICIPAL WARDS</span>
          <p className="text-3xl font-black text-slate-900 mt-1">{data.wards?.length || 10}</p>
          <p className="text-[11px] text-slate-400 mt-1">Jammu Municipal Corporation</p>
        </div>
      </div>

      {/* ── Ward Leaderboard Table ── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 bg-slate-50/50">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-500" />
              Ward Trust Leaderboard (वार्ड विश्वास सूचकांक)
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Ranked objectively by response speed, closure rate, citizen ratings, and proactive public advisories.
            </p>
          </div>
          <button 
            onClick={loadData} 
            className="text-xs font-semibold text-slate-600 hover:text-emerald-700 flex items-center gap-1.5 border bg-white px-3 py-1.5 rounded-lg shadow-xs hover:bg-slate-50 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Live
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {data.wards?.map((ward: any, idx: number) => {
            const isTop = idx === 0;
            return (
              <div 
                key={ward.id} 
                className={`p-4 sm:px-6 hover:bg-slate-50/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition ${
                  isTop ? "bg-amber-50/20" : ""
                }`}
              >
                <div className="flex items-center gap-3.5">
                  <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs ${
                    idx === 0 ? "bg-amber-500 text-white shadow-sm" :
                    idx === 1 ? "bg-slate-300 text-slate-800" :
                    idx === 2 ? "bg-amber-700 text-white" : "bg-slate-100 text-slate-600"
                  }`}>
                    #{idx + 1}
                  </span>

                  <div>
                    <div className="flex items-center gap-2">
                      <Link 
                        href={`/ward/${ward.id}`} 
                        className="font-bold text-slate-900 hover:text-emerald-700 hover:underline text-sm sm:text-base"
                      >
                        {ward.name}
                      </Link>
                      {ward.is_champion && (
                        <span className="bg-amber-100 text-amber-900 text-[10px] font-extrabold px-2 py-0.5 rounded-full border border-amber-300 flex items-center gap-1">
                          ⭐ Ward Champion
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-slate-500 block mt-0.5">
                      Pop. ~{ward.population.toLocaleString()} · Active Open Issues: <span className="font-semibold text-slate-700">{ward.open_tickets}</span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center justify-between sm:justify-end gap-5">
                  <div className="text-right">
                    <div className="flex items-center gap-1 justify-end">
                      <span className="text-xl font-black text-slate-900">{ward.trust_index}</span>
                      <span className="text-[11px] text-slate-400 font-bold">/100</span>
                    </div>
                    <div className="w-24 bg-slate-200 rounded-full h-1.5 mt-1 overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all ${
                          ward.trust_index >= 75 ? "bg-emerald-500" :
                          ward.trust_index >= 60 ? "bg-amber-500" : "bg-rose-500"
                        }`}
                        style={{ width: `${ward.trust_index}%` }}
                      />
                    </div>
                  </div>

                  <Link 
                    href={`/ward/${ward.id}`} 
                    className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-lg flex items-center gap-1 shadow-xs transition"
                  >
                    View Details <ArrowUpRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
