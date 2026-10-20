"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, ShieldCheck, CheckCircle2, Clock, 
  MapPin, Users, Award, AlertCircle, RefreshCw, Lock,
  ThumbsUp, RotateCcw
} from "lucide-react";
import { fetchTicketPublic } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function TicketPublicPage() {
  const params = useParams();
  const code = (params.code as string).toUpperCase();
  const [ticket, setTicket] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verifySuccess, setVerifySuccess] = useState<string | null>(null);
  const [reopenReason, setReopenReason] = useState("");
  const [verifyComment, setVerifyComment] = useState("");
  const [showReopenForm, setShowReopenForm] = useState(false);
  const [showVerifyForm, setShowVerifyForm] = useState(false);

  const loadTicket = async () => {
    try {
      setLoading(true);
      const res = await fetchTicketPublic(code);
      setTicket(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/api/public/tickets/${code}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: verifyComment || "Satisfied with resolution" }),
      });
      if (res.ok) {
        setVerifySuccess("✅ Thank you! Your complaint has been marked as resolved and closed.");
        loadTicket();
      } else {
        setVerifySuccess("Something went wrong. Please try again.");
      }
    } catch {
      setVerifySuccess("Network error. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  const handleReopen = async () => {
    if (!reopenReason.trim()) return;
    setVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/api/public/tickets/${code}/reopen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: reopenReason }),
      });
      if (res.ok) {
        setVerifySuccess("🔄 Your complaint has been reopened. The officer has been notified.");
        setShowReopenForm(false);
        setReopenReason("");
        loadTicket();
      }
    } catch {
      setVerifySuccess("Network error. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    if (code) loadTicket();
  }, [code]);

  if (loading || !ticket) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-3" />
        <p className="text-slate-600">Verifying Public Audit Trail for {code}...</p>
      </div>
    );
  }

  const statusColor = 
    ticket.status === "verified_closed" ? "bg-emerald-100 text-emerald-800 border-emerald-300" :
    ticket.status === "resolved_pending_verification" ? "bg-indigo-100 text-indigo-800 border-indigo-300" :
    ticket.status === "reopened" ? "bg-red-100 text-red-800 border-red-300" :
    ticket.status === "in_progress" ? "bg-blue-100 text-blue-800 border-blue-300" :
    "bg-amber-100 text-amber-800 border-amber-300";

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <Link href="/" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Trust Overview
      </Link>

      {/* Ticket Header */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">{ticket.code}</h1>
            <span className={`text-xs uppercase font-extrabold px-3 py-1 rounded-full border ${statusColor}`}>
              {ticket.status.replace(/_/g, " ")}
            </span>
          </div>

          {ticket.audit_chain?.is_valid && (
            <div className="flex items-center gap-1.5 bg-emerald-50 text-emerald-800 text-xs font-bold px-3 py-1.5 rounded-lg border border-emerald-200">
              <Lock className="w-3.5 h-3.5 text-emerald-600" />
              Cryptographic Audit Chain Verified (SHA-256)
            </div>
          )}
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-slate-100 text-sm">
          <div>
            <span className="text-xs text-slate-400 block font-medium">Department</span>
            <span className="font-semibold text-slate-800">{ticket.department}</span>
          </div>
          <div>
            <span className="text-xs text-slate-400 block font-medium">Ward</span>
            <span className="font-semibold text-slate-800">{ticket.ward?.name}</span>
          </div>
          <div>
            <span className="text-xs text-slate-400 block font-medium">Public Location</span>
            <span className="font-semibold text-slate-800 truncate block">{ticket.address_landmark}</span>
          </div>
          <div>
            <span className="text-xs text-slate-400 block font-medium">Collective Voice</span>
            <span className="font-bold text-emerald-700 flex items-center gap-1">
              <Users className="w-3.5 h-3.5" /> {ticket.affected_count} {ticket.affected_count === 1 ? "Citizen" : "Citizens"}
            </span>
          </div>
        </div>
      </div>

      {/* Transparent Priority Scoring Box */}
      <div className="bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-amber-900 block">
              Transparent Priority Index
            </span>
            <h3 className="text-lg font-extrabold text-amber-950 mt-0.5">
              Ward Rank #{ticket.ward_rank} of {ticket.total_ward_open_tickets} Active Open Issues
            </h3>
            <p className="text-xs text-amber-800/80 mt-1">
              Objective formula prevents VIP favoritism: score combines collective reports, severity, age, safety flag and hospital/school proximity.
            </p>
          </div>
          <div className="text-right sm:text-center bg-white/70 border border-amber-200/80 p-3 rounded-lg min-w-[120px]">
            <span className="text-[10px] text-amber-800 uppercase font-bold block">Score</span>
            <span className="text-3xl font-black text-amber-900">{ticket.priority_score}</span>
            <span className="text-xs text-amber-700 font-bold ml-1">/100</span>
          </div>
        </div>

        {ticket.priority_reason && ticket.priority_reason.length > 0 && (
          <div className="mt-4 pt-3 border-t border-amber-200/60 flex flex-wrap gap-2">
            {ticket.priority_reason.map((reason: string, i: number) => (
              <span key={i} className="bg-white/80 border border-amber-200 text-amber-900 text-xs font-medium px-2.5 py-1 rounded-md shadow-xs">
                • {reason}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Before / After Verification Photos */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-emerald-600" />
          Verified Photographic Proof
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase block mb-2">Before Repair (Citizen Report)</span>
            <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden border border-slate-200 relative">
              {ticket.before_photo_url ? (
                <img src={ticket.before_photo_url} alt="Before" className="w-full h-full object-cover" />
              ) : (
                <div className="h-full flex items-center justify-center text-xs text-slate-400">No initial photo</div>
              )}
            </div>
          </div>

          <div>
            <span className="text-xs font-bold text-slate-500 uppercase block mb-2">After Repair (Officer Geotagged Proof)</span>
            <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden border border-slate-200 relative">
              {ticket.after_photo_url ? (
                <img src={ticket.after_photo_url} alt="After" className="w-full h-full object-cover" />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-xs text-slate-400 p-4 text-center">
                  <Clock className="w-6 h-6 text-slate-300 mb-1" />
                  Work in progress — proof photo will be uploaded upon field resolution
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── CITIZEN FEEDBACK SECTION ── */}
      {ticket.status !== "verified_closed" && (
        <div className="bg-white rounded-xl border-2 border-emerald-200 p-6 shadow-sm space-y-4">
          {verifySuccess ? (
            <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm font-semibold p-5 rounded-xl text-center flex flex-col items-center justify-center gap-2">
              <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-600">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <p className="font-bold text-base text-emerald-900">{verifySuccess}</p>
              <p className="text-xs text-emerald-700">Your feedback has been appended to the permanent audit trail below.</p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-emerald-600 flex items-center justify-center shrink-0">
                  <ThumbsUp className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h2 className="text-base font-black text-slate-900">Your Feedback</h2>
                  <p className="text-xs text-slate-500">You have the final say — confirm resolution or raise it again</p>
                </div>
              </div>

              <div className="space-y-3">
                {/* Option 1: Yes — Resolved */}
                {!showReopenForm && (
                  <div className="bg-emerald-50 border-2 border-emerald-300 rounded-xl p-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-full bg-emerald-600 flex items-center justify-center shrink-0">
                        <ThumbsUp className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-black text-emerald-900">Yes, Issue is Resolved! ✅</div>
                        <div className="text-xs text-emerald-700 font-medium">The work has been done.</div>
                      </div>
                    </div>
                    <textarea
                      value={verifyComment}
                      onChange={(e) => setVerifyComment(e.target.value)}
                      rows={2}
                      placeholder="Optional: Share your experience or comments about the repair... (e.g. Road is fixed, good work!)"
                      className="w-full text-xs border border-emerald-200 rounded-lg p-3 outline-none focus:ring-2 focus:ring-emerald-400 bg-white resize-none"
                    />
                    <button
                      onClick={handleVerify}
                      disabled={verifying}
                      className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white font-bold py-2.5 rounded-lg text-xs flex items-center justify-center gap-2 transition"
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                      {verifying ? "Submitting..." : "Confirm & Close Complaint"}
                    </button>
                  </div>
                )}

                {/* Option 2: No — Reopen */}
                {!showVerifyForm && (
                  !showReopenForm ? (
                    <button
                      onClick={() => setShowReopenForm(true)}
                      className="w-full flex items-center gap-3 bg-red-50 hover:bg-red-100 border-2 border-red-200 hover:border-red-400 text-red-900 font-bold py-4 px-5 rounded-xl transition text-left"
                    >
                      <div className="w-9 h-9 rounded-full bg-red-500 flex items-center justify-center shrink-0">
                        <RotateCcw className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="text-sm font-black">No, Problem Still Exists 🔄</div>
                        <div className="text-xs text-red-700 font-medium">Work is incomplete or unsatisfactory. Raise this complaint again.</div>
                      </div>
                    </button>
                  ) : (
                    <div className="bg-red-50 border-2 border-red-200 rounded-xl p-4 space-y-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-red-500 flex items-center justify-center shrink-0">
                          <RotateCcw className="w-4 h-4 text-white" />
                        </div>
                        <div>
                          <div className="text-sm font-black text-red-900">No, Problem Still Exists 🔄</div>
                          <div className="text-xs text-red-700 font-medium">Describe what's still wrong — this will be sent to the officer.</div>
                        </div>
                      </div>
                      <textarea
                        value={reopenReason}
                        onChange={(e) => setReopenReason(e.target.value)}
                        rows={3}
                        placeholder="Describe the issue in detail... (e.g. The pothole is only partially patched, still dangerous for bikes. Drain is still overflowing near school gate.)"
                        className="w-full text-xs border border-red-200 rounded-lg p-3 outline-none focus:ring-2 focus:ring-red-400 bg-white resize-none"
                      />
                      <div className="flex gap-2">
                        <button
                          onClick={handleReopen}
                          disabled={verifying || !reopenReason.trim()}
                          className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-bold py-2.5 rounded-lg text-xs flex items-center justify-center gap-2 transition"
                        >
                          <RotateCcw className="w-3.5 h-3.5" />
                          {verifying ? "Submitting..." : "Reopen Complaint"}
                        </button>
                        <button
                          onClick={() => { setShowReopenForm(false); setReopenReason(""); }}
                          className="px-4 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg text-xs transition"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )
                )}
              </div>
            </>
          )}
        </div>
      )}

      {/* Verified Closed State */}
      {ticket.status === "verified_closed" && !verifySuccess && (
        <div className="bg-emerald-50 border-2 border-emerald-300 rounded-xl p-5 flex items-center gap-3">
          <CheckCircle2 className="w-8 h-8 text-emerald-600 shrink-0" />
          <div>
            <p className="text-sm font-black text-emerald-900">Complaint Verified & Closed ✓</p>
            <p className="text-xs text-emerald-700 mt-0.5">This grievance has been confirmed as resolved by the citizen. Thank you for your participation!</p>
          </div>
        </div>
      )}

      {/* Activity & Verification Timeline */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            Ticket Activity &amp; Audit Trail (समयरेखा)
          </h2>
          <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200">
            Immutable SHA-256 Chained
          </span>
        </div>

        <div className="space-y-4 border-l-2 border-slate-200 pl-4 ml-2">
          {ticket.timeline?.map((ev: any) => {
            let label = ev.type.replace(/_/g, " ");
            let description = "";

            if (ev.type === "created") {
              label = "Grievance Reported";
              description = "Citizen reported the issue from field";
            } else if (ev.type === "assigned") {
              label = "Assigned to Field Officer";
              description = ev.payload?.officer_name ? `Assigned to ${ev.payload.officer_name}` : "Assigned to department engineer";
            } else if (ev.type === "cluster_joined") {
              label = "Collective Voice: Another Citizen Reported This";
              description = ev.payload?.affected_count ? `Confirmed by another nearby resident (${ev.payload.affected_count} citizens total)` : "Nearby resident reinforced this complaint";
            } else if (ev.type === "in_progress") {
              label = "Work In Progress";
              description = "Officer accepted and dispatched maintenance team";
            } else if (ev.type === "resolved_pending_verification") {
              label = "Repair Completed (Pending Verification)";
              description = "Officer submitted geotagged after-photo proof";
            } else if (ev.type === "verified_closed") {
              label = "Citizen Verified & Closed";
              const userNote = ev.payload?.comment || ev.payload?.feedback;
              description = userNote && userNote !== "satisfied" ? `Citizen confirmed: "${userNote}"` : "Citizen confirmed ground repair satisfaction";
            } else if (ev.type === "reopened") {
              label = "Reopened by Citizen";
              const userReason = ev.payload?.comment || ev.payload?.reason;
              description = userReason ? `Citizen flagged: "${userReason}"` : "Citizen flagged work as incomplete or unsatisfactory";
            }

            return (
              <div key={ev.id} className="relative group">
                <div className="w-3.5 h-3.5 bg-emerald-600 rounded-full absolute -left-[23px] top-1 border-2 border-white ring-2 ring-emerald-100" />
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                  <span className="text-xs font-bold text-slate-900">{label}</span>
                  <span className="text-[11px] text-slate-400">{ev.created_at ? new Date(ev.created_at).toLocaleString() : ""}</span>
                </div>
                {description && (
                  <p className="text-xs text-slate-600 mt-0.5">{description}</p>
                )}
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Action logged by: <span className="font-medium text-slate-600 capitalize">{ev.actor_type}</span>
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
