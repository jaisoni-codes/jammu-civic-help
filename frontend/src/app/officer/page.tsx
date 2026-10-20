"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import Link from "next/link";
import { 
  UserCheck, RefreshCw, ArrowRight,
  Clock, CheckCircle, AlertTriangle,
  ArrowDownUp, CalendarClock, Flame, TrendingUp, Bell, Image as ImageIcon, Eye, X
} from "lucide-react";
import { officerLogin, fetchOfficerTickets } from "@/lib/api";

const PENDING_STATUSES = ["open", "assigned", "in_progress", "reopened"];
const COMPLETED_STATUSES = ["resolved_pending_verification", "verified_closed", "unverified_closed"];

type SortKey = "priority" | "newest" | "sla" | "escalation";

const SORT_OPTIONS: { key: SortKey; label: string; icon: any }[] = [
  { key: "priority",   label: "Priority",   icon: Flame },
  { key: "newest",     label: "Newest",     icon: CalendarClock },
  { key: "sla",        label: "SLA Left",   icon: Clock },
  { key: "escalation", label: "Escalated",  icon: TrendingUp },
];

function sortTickets(tickets: any[], sortKey: SortKey) {
  const arr = [...tickets];
  switch (sortKey) {
    case "priority":
      return arr.sort((a, b) => (b.priority_score || 0) - (a.priority_score || 0));
    case "newest":
      return arr.sort((a, b) => {
        const timeA = new Date(a.updated_at || a.created_at || 0).getTime();
        const timeB = new Date(b.updated_at || b.created_at || 0).getTime();
        if (timeB !== timeA) return timeB - timeA;
        return (b.id || 0) - (a.id || 0);
      });
    case "sla":
      // sort ascending — smallest (most urgent) first; null last
      return arr.sort((a, b) => {
        if (a.sla_hours_left == null) return 1;
        if (b.sla_hours_left == null) return -1;
        return a.sla_hours_left - b.sla_hours_left;
      });
    case "escalation":
      return arr.sort((a, b) => (b.escalation_level || 0) - (a.escalation_level || 0));
    default:
      return arr;
  }
}

function StatusBadge({ status }: { status: string }) {
  const cfg: Record<string, { color: string; label: string }> = {
    open:                          { color: "bg-blue-100 text-blue-800",    label: "Open" },
    assigned:                      { color: "bg-indigo-100 text-indigo-800", label: "Assigned" },
    in_progress:                   { color: "bg-amber-100 text-amber-800",  label: "In Progress" },
    reopened:                      { color: "bg-red-100 text-red-800",      label: "Reopened" },
    resolved_pending_verification: { color: "bg-purple-100 text-purple-800", label: "Awaiting Verification" },
    verified_closed:               { color: "bg-emerald-100 text-emerald-800", label: "Verified Closed ✓" },
    unverified_closed:             { color: "bg-slate-100 text-slate-600",  label: "Unverified Closed" },
  };
  const c = cfg[status] ?? { color: "bg-slate-100 text-slate-600", label: status };
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${c.color}`}>
      {c.label}
    </span>
  );
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}

export default function OfficerInboxPage() {
  const [token, setToken]       = useState<string | null>(null);
  const [officer, setOfficer]   = useState<any>(null);
  const [officerId, setOfficerId] = useState("1");
  const [pin, setPin]           = useState("1234");
  const [loginError, setLoginError] = useState<string | null>(null);

  const [tickets, setTickets]   = useState<any[]>([]);
  const [loading, setLoading]   = useState(false);
  const [newAlert, setNewAlert] = useState<{ title: string; subtitle?: string; code?: string } | null>(null);
  const knownTicketIdsRef       = useRef<Set<number>>(new Set());
  const isInitializedRef        = useRef<boolean>(false);

  // Tab: "pending" | "awaiting" | "completed"
  const [tab, setTab]           = useState<"pending" | "awaiting" | "completed">("pending");
  const [sortKey, setSortKey]   = useState<SortKey>("newest");
  const [previewPhoto, setPreviewPhoto] = useState<string | null>(null);

  // Keep token in a ref for the interval callback
  const tokenRef = useRef<string | null>(null);
  tokenRef.current = token;

  useEffect(() => {
    const savedToken   = localStorage.getItem("bharosa_officer_token");
    const savedOfficer = localStorage.getItem("bharosa_officer_user");
    if (savedToken && savedOfficer) {
      setToken(savedToken);
      setOfficer(JSON.parse(savedOfficer));
      loadTickets(savedToken);
    }
  }, []);

  // Auto-refresh every 5 seconds when logged in for fast real-time notifications
  useEffect(() => {
    if (!token) return;
    const interval = setInterval(() => {
      if (tokenRef.current) silentRefresh(tokenRef.current);
    }, 5000);
    return () => clearInterval(interval);
  }, [token]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    try {
      const res = await officerLogin(parseInt(officerId), pin);
      setToken(res.access_token);
      setOfficer(res.officer);
      localStorage.setItem("bharosa_officer_token", res.access_token);
      localStorage.setItem("bharosa_officer_user", JSON.stringify(res.officer));
      loadTickets(res.access_token);
    } catch (err: any) {
      setLoginError(err.message || "Login failed");
    }
  };

  const loadTickets = async (authToken: string) => {
    setLoading(true);
    try {
      const res = await fetchOfficerTickets(authToken);
      // Populate known tickets set on initial load so we NEVER alert on pre-existing tickets
      knownTicketIdsRef.current = new Set(res.map((t: any) => t.id));
      isInitializedRef.current = true;
      setTickets(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Silent background refresh — detects genuine newly submitted or updated complaints
  const silentRefresh = async (authToken: string) => {
    try {
      const res = await fetchOfficerTickets(authToken);
      if (!isInitializedRef.current) {
        knownTicketIdsRef.current = new Set(res.map((t: any) => t.id));
        isInitializedRef.current = true;
        setTickets(res);
        return;
      }

      // Check for tickets whose IDs were never seen before
      const brandNewTickets = res.filter((t: any) => !knownTicketIdsRef.current.has(t.id));

      if (brandNewTickets.length > 0) {
        // Register newly seen tickets so alert does not repeat
        brandNewTickets.forEach((t: any) => knownTicketIdsRef.current.add(t.id));

        const latest = brandNewTickets[0];
        const count = brandNewTickets.length;
        setNewAlert({
          title: count === 1 ? `New Complaint Filed!` : `${count} New Complaints Filed!`,
          subtitle: count === 1 ? `${latest.category?.replace(/_/g, " ")} • ${latest.ward}` : `Latest: ${latest.code}`,
          code: latest.code,
        });

        // Auto dismiss toast after 7s
        setTimeout(() => setNewAlert(null), 7000);

        // Switch to pending tab and sort newest to highlight it immediately
        setTab("pending");
        setSortKey("newest");
      }

      setTickets(res);
    } catch (err) { /* silent */ }
  };

  const handleLogout = () => {
    setToken(null);
    setOfficer(null);
    localStorage.removeItem("bharosa_officer_token");
    localStorage.removeItem("bharosa_officer_user");
  };

  // Split tickets into buckets
  const pendingTickets   = useMemo(() =>
    sortTickets(tickets.filter(t => PENDING_STATUSES.includes(t.status)), sortKey),
    [tickets, sortKey]
  );
  const awaitingTickets  = useMemo(() =>
    sortTickets(tickets.filter(t => t.status === "resolved_pending_verification"), sortKey),
    [tickets, sortKey]
  );
  const completedTickets = useMemo(() =>
    sortTickets(tickets.filter(t => ["verified_closed","unverified_closed"].includes(t.status)), sortKey),
    [tickets, sortKey]
  );

  const activeList =
    tab === "pending"   ? pendingTickets :
    tab === "awaiting"  ? awaitingTickets :
    completedTickets;

  if (!token) {
    return (
      <div className="max-w-md mx-auto px-4 py-16">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-lg space-y-6">
          <div className="text-center">
            <div className="w-12 h-12 bg-emerald-100 text-emerald-800 rounded-xl flex items-center justify-center mx-auto mb-3">
              <UserCheck className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">CivicHelp Officer Portal</h1>
            <p className="text-xs text-slate-500 mt-1">JMC Field Officer Inbox & Verified Resolution Console</p>
          </div>

          {loginError && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg font-medium">
              {loginError}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Select Seeded Officer</label>
              <select
                value={officerId}
                onChange={(e) => setOfficerId(e.target.value)}
                className="w-full border rounded-lg p-2.5 text-sm bg-slate-50 focus:bg-white outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value="1">Rajesh Sharma (JE - JMC Roads)</option>
                <option value="2">Sunil Verma (JE - JMC Electrical)</option>
                <option value="3">Pooja Rajput (JE - JMC Sanitation)</option>
                <option value="9">Er. Kuldeep Kotwal (EE - JMC Roads)</option>
                <option value="11">Devinder Singh IAS (Commissioner)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Officer PIN (Default: 1234)</label>
              <input
                type="password"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                className="w-full border rounded-lg p-2.5 text-sm outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="4-digit PIN"
                maxLength={4}
              />
            </div>

            <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-bold p-2.5 rounded-lg text-sm shadow">
              Sign In to Inbox
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-4">
      {/* Officer Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900">{officer.name}</span>
            <span className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded uppercase">
              {officer.role}
            </span>
          </div>
          <span className="text-xs text-slate-500">{officer.department}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-slate-400">Live Sync: Active</span>
          <button onClick={() => loadTickets(token!)} className="p-2 border rounded-lg text-slate-600 hover:bg-slate-50" title="Manual refresh">
            <RefreshCw className="w-4 h-4" />
          </button>
          <button onClick={handleLogout} className="text-xs text-red-600 font-semibold px-2 py-1">
            Logout
          </button>
        </div>
      </div>

      {/* ── MAIN TABS ── */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl">
        {[
          { key: "pending",   label: "Pending",           count: pendingTickets.length,   icon: Clock,         color: "text-amber-700" },
          { key: "awaiting",  label: "Awaiting Verify",   count: awaitingTickets.length,  icon: AlertTriangle, color: "text-purple-700" },
          { key: "completed", label: "Completed",         count: completedTickets.length, icon: CheckCircle,   color: "text-emerald-700" },
        ].map(({ key, label, count, icon: Icon, color }) => (
          <button
            key={key}
            onClick={() => setTab(key as any)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2 px-2 rounded-lg text-xs font-bold transition-all ${
              tab === key
                ? "bg-white shadow text-slate-900"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${tab === key ? color : ""}`} />
            <span>{label}</span>
            <span className={`text-[10px] font-black px-1.5 py-0.5 rounded-full ml-0.5 ${
              tab === key ? "bg-slate-900 text-white" : "bg-slate-200 text-slate-600"
            }`}>{count}</span>
          </button>
        ))}
      </div>

      {/* ── SORT BAR (only for pending) ── */}
      {tab === "pending" && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-slate-500 flex items-center gap-1">
            <ArrowDownUp className="w-3.5 h-3.5" /> Sort by:
          </span>
          {SORT_OPTIONS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setSortKey(key)}
              className={`flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-full border transition-all ${
                sortKey === key
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-white text-slate-600 border-slate-200 hover:border-slate-400"
              }`}
            >
              <Icon className="w-3 h-3" />
              {label}
            </button>
          ))}
        </div>
      )}

      {/* ── TICKET LIST ── */}
      <div className="space-y-3">
        <p className="text-xs text-slate-400 font-medium">
          {activeList.length} ticket{activeList.length !== 1 ? "s" : ""} in this view
          {tab === "pending" && ` · sorted by ${sortKey}`}
        </p>

        {loading ? (
          <div className="py-12 text-center text-slate-500 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-emerald-600 mb-2" />
            Loading assigned grievances...
          </div>
        ) : activeList.length === 0 ? (
          <div className="bg-white rounded-xl p-10 text-center border">
            {tab === "pending"   && <p className="text-slate-500 text-sm">🎉 No pending tickets right now!</p>}
            {tab === "awaiting"  && <p className="text-slate-500 text-sm">No tickets awaiting citizen verification.</p>}
            {tab === "completed" && <p className="text-slate-500 text-sm">No completed tickets yet.</p>}
          </div>
        ) : (
          activeList.map((t) => {
            const slaColor =
              t.sla_status === "red"   ? "bg-red-100 text-red-800 border-red-300" :
              t.sla_status === "amber" ? "bg-amber-100 text-amber-800 border-amber-300" :
              "bg-emerald-100 text-emerald-800 border-emerald-300";

            const fullPhotoUrl = getMediaUrl(t.photo_url);

            return (
              <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-slate-300 transition">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 min-w-0">
                    {/* Citizen Photo Thumbnail */}
                    {fullPhotoUrl ? (
                      <div 
                        onClick={() => setPreviewPhoto(fullPhotoUrl)}
                        className="relative w-16 h-16 sm:w-20 sm:h-20 shrink-0 rounded-lg overflow-hidden border border-slate-200 cursor-pointer group bg-slate-100 shadow-inner"
                        title="Click to view full photo proof"
                      >
                        <img 
                          src={fullPhotoUrl} 
                          alt="Citizen Proof" 
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                        />
                        <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                          <Eye className="w-5 h-5 text-white drop-shadow" />
                        </div>
                        <span className="absolute bottom-0 inset-x-0 bg-black/60 text-[9px] text-white text-center py-0.5 font-bold tracking-tight">
                          PROOF
                        </span>
                      </div>
                    ) : (
                      <div className="w-16 h-16 sm:w-20 sm:h-20 shrink-0 rounded-lg border border-dashed border-slate-200 bg-slate-50 flex flex-col items-center justify-center text-slate-300">
                        <ImageIcon className="w-6 h-6 mb-0.5 opacity-60" />
                        <span className="text-[9px] font-semibold text-slate-400">No Photo</span>
                      </div>
                    )}

                    <div className="space-y-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-black text-slate-900">{t.code}</span>
                        <StatusBadge status={t.status} />
                        {t.sla_hours_left != null && (
                          <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${slaColor}`}>
                            {t.sla_hours_left > 0 ? `${t.sla_hours_left}h left` : `${Math.abs(t.sla_hours_left)}h overdue`}
                          </span>
                        )}
                        {t.escalation_level > 0 && (
                          <span className="bg-red-600 text-white text-[10px] font-black px-1.5 py-0.5 rounded">
                            L{t.escalation_level} ESCALATED
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-slate-600 font-medium capitalize truncate">
                        {t.category?.replace(/_/g, " ")} · {t.ward}
                      </p>
                      {t.address && (
                        <p className="text-[11px] text-slate-500 line-clamp-1 italic">
                          📍 {t.address}
                        </p>
                      )}
                      {t.affected_count > 1 && (
                        <span className="text-[10px] text-indigo-600 font-semibold block">
                          👥 {t.affected_count} citizens affected
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span className="text-[10px] text-slate-400 block font-bold">Priority</span>
                    <span className={`text-lg font-black ${
                      (t.priority_score || 0) >= 70 ? "text-red-600" :
                      (t.priority_score || 0) >= 50 ? "text-amber-600" : "text-emerald-600"
                    }`}>
                      {t.priority_score ?? "—"}
                    </span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-400">ID #{t.id}</span>
                  <Link
                    href={`/officer/t/${t.id}`}
                    className="bg-slate-900 hover:bg-slate-800 text-white font-bold px-3 py-1.5 rounded-lg flex items-center gap-1 shadow"
                  >
                    Action & Resolve <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Toast Notification (Bottom-Right) */}
      {newAlert && (
        <aside 
          aria-live="polite"
          className="fixed bottom-6 right-6 z-50 max-w-sm w-full bg-slate-900/95 backdrop-blur-md text-white p-4 rounded-2xl shadow-2xl border border-slate-700/80 animate-in slide-in-from-bottom-5 duration-300 flex items-start gap-3"
        >
          <div className="w-9 h-9 rounded-xl bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center justify-center shrink-0">
            <Bell className="w-5 h-5 animate-bounce" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-black tracking-wide text-emerald-400 uppercase">
                {newAlert.title}
              </span>
              <button 
                onClick={() => setNewAlert(null)}
                className="text-slate-400 hover:text-white p-0.5 rounded transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {newAlert.code && (
              <p className="text-sm font-black text-white mt-0.5">
                {newAlert.code}
              </p>
            )}
            {newAlert.subtitle && (
              <p className="text-xs text-slate-300 capitalize truncate mt-0.5">
                {newAlert.subtitle}
              </p>
            )}
            <p className="text-[10px] text-emerald-400/90 font-medium mt-1">
              ✓ Added to top of Pending inbox
            </p>
          </div>
        </aside>
      )}

      {/* Full Photo Preview Modal */}
      {previewPhoto && (
        <div 
          className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-150"
          onClick={() => setPreviewPhoto(null)}
        >
          <div 
            className="relative max-w-2xl w-full bg-slate-900 rounded-2xl overflow-hidden shadow-2xl border border-slate-700 p-2"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-3 py-2 text-white border-b border-slate-800">
              <span className="text-xs font-bold text-slate-200">📸 Citizen Grievance Photo Proof</span>
              <button 
                onClick={() => setPreviewPhoto(null)} 
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-2 flex items-center justify-center max-h-[75vh]">
              <img 
                src={previewPhoto} 
                alt="Citizen Grievance Proof Full" 
                className="max-h-[70vh] w-auto max-w-full rounded-lg object-contain bg-black/40"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
