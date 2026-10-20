"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  ShieldCheck, ArrowUpRight, TrendingUp, Award, 
  CheckCircle2, AlertCircle, RefreshCw, Layers 
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
      <div className="max-w-7xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-3" />
        <p className="text-slate-600 font-medium">Computing Live Ward Trust Index across Jammu...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 text-center text-red-600">
        <AlertCircle className="w-10 h-10 mx-auto mb-2" />
        <p className="font-bold">Failed to load civic data</p>
        <button onClick={loadData} className="mt-4 px-4 py-2 bg-slate-900 text-white rounded-lg text-sm">Retry</button>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-2xl p-6 sm:p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 max-w-3xl">
          <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 text-xs px-3 py-1 rounded-full font-semibold uppercase tracking-wider inline-block mb-3">
            Real-time Civic Accountability
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-2">
            City Ward Trust Index
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Measuring citizen-municipality trust across Jammu through verified geotagged closures, collective duplicate reporting, transparent priority ranking, and citizen confirmation.
          </p>
        </div>

        <div className="mt-6 sm:mt-0 sm:absolute sm:right-8 sm:top-1/2 sm:-translate-y-1/2 bg-white/10 backdrop-blur-md border border-white/20 p-5 rounded-2xl text-center min-w-[200px]">
          <span className="text-xs font-semibold uppercase tracking-wider text-emerald-300 block mb-1">
            Jammu City Trust Score
          </span>
          <div className="text-5xl font-black text-white flex items-center justify-center gap-1">
            {data.city_trust_index}
            <span className="text-2xl text-emerald-400 font-bold">/100</span>
          </div>
          <span className="text-[11px] text-slate-300 block mt-1">
            Trailing 30-Day Aggregation
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Total Recorded Grievances</span>
          <p className="text-2xl font-bold text-slate-900 mt-1">{data.total_tickets}</p>
          <span className="text-xs text-emerald-600 font-semibold flex items-center gap-1 mt-1">
            <CheckCircle2 className="w-3.5 h-3.5" /> 100% SHA-256 Audit Chained
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Active Under Action</span>
          <p className="text-2xl font-bold text-amber-600 mt-1">{data.open_tickets}</p>
          <span className="text-xs text-slate-500 font-medium block mt-1">
            Sorted by Public Priority Score
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Citizen-Verified Closures</span>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{data.verified_closed}</p>
          <span className="text-xs text-emerald-700 font-medium block mt-1">
            Photo + GPS + Citizen Confirmed
          </span>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium block">Wards Monitored</span>
          <p className="text-2xl font-bold text-slate-900 mt-1">{data.wards?.length || 10}</p>
          <span className="text-xs text-indigo-600 font-medium block mt-1">
            Smart City Municipal Grid
          </span>
        </div>
      </div>

      {/* Ward Leaderboard */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b flex items-center justify-between bg-slate-50">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-500" />
              Ward Trust Leaderboard (वार्ड विश्वास सूचकांक)
            </h2>
            <p className="text-xs text-slate-500">
              Ranked by 6 weighted dimensions: Response speed, Verified closures, Low reopens, Citizen ratings, Proactive broadcasts & Participation
            </p>
          </div>
          <button onClick={loadData} className="text-xs font-semibold text-slate-600 hover:text-emerald-700 flex items-center gap-1 border bg-white px-2.5 py-1.5 rounded-lg shadow-sm">
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>

        <div className="divide-y divide-slate-100">
          {data.wards?.map((ward: any, idx: number) => (
            <div key={ward.id} className="p-4 sm:px-6 hover:bg-slate-50 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition">
              <div className="flex items-center gap-3">
                <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                  idx === 0 ? "bg-amber-100 text-amber-800 border border-amber-300" :
                  idx === 1 ? "bg-slate-200 text-slate-700" :
                  idx === 2 ? "bg-amber-50 text-amber-900" : "bg-slate-100 text-slate-600"
                }`}>
                  #{idx + 1}
                </span>

                <div>
                  <div className="flex items-center gap-2">
                    <Link href={`/ward/${ward.id}`} className="font-bold text-slate-900 hover:text-emerald-700 hover:underline">
                      {ward.name}
                    </Link>
                    {ward.is_champion && (
                      <span className="bg-amber-100 text-amber-800 text-[10px] font-extrabold px-2 py-0.5 rounded-full border border-amber-300 flex items-center gap-1">
                        🏆 Ward Champion
                      </span>
                    )}
                  </div>
                  <span className="text-xs text-slate-500 block">
                    Pop. Est: {ward.population.toLocaleString()} | Active Open Issues: <span className="font-semibold text-slate-700">{ward.open_tickets}</span>
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between sm:justify-end gap-6">
                <div className="text-right">
                  <div className="flex items-center gap-1.5 justify-end">
                    <span className="text-2xl font-black text-slate-900">{ward.trust_index}</span>
                    <span className="text-xs text-slate-400 font-bold">/100</span>
                  </div>
                  <div className="w-24 bg-slate-100 rounded-full h-2 mt-1 overflow-hidden">
                    <div 
                      className={`h-full rounded-full ${
                        ward.trust_index >= 75 ? "bg-emerald-500" :
                        ward.trust_index >= 60 ? "bg-amber-500" : "bg-red-500"
                      }`}
                      style={{ width: `${ward.trust_index}%` }}
                    />
                  </div>
                </div>

                <Link href={`/ward/${ward.id}`} className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold rounded-lg flex items-center gap-1 shadow">
                  Breakdown <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
