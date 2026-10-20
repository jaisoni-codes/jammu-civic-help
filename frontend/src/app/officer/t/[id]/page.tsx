"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, Camera, CheckCircle2, 
  AlertTriangle, RefreshCw, XCircle 
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function OfficerTicketActionPage() {
  const params = useParams();
  const router = useRouter();
  const ticketId = params.id as string;

  const [ticket, setTicket] = useState<any>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Resolve form
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [resolving, setResolving] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Block modal
  const [showBlock, setShowBlock] = useState(false);
  const [blockReason, setBlockReason] = useState("budget");

  useEffect(() => {
    const savedToken = localStorage.getItem("bharosa_officer_token");
    if (!savedToken) {
      router.push("/officer");
      return;
    }
    setToken(savedToken);
    loadDetail(savedToken);
    getCurrentLocation();
  }, [ticketId]);

  const loadDetail = async (authToken: string) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/officer/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (res.ok) setTicket(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLat(pos.coords.latitude);
          setLng(pos.coords.longitude);
        },
        () => {
          // Fallback to ticket coordinates if browser blocks location
          if (ticket) {
            setLat(ticket.lat);
            setLng(ticket.lng);
          }
        }
      );
    }
  };

  const handleAccept = async () => {
    if (!token) return;
    setAccepting(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE}/api/officer/tickets/${ticketId}/accept`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSuccessMsg("Work accepted and assigned! Status updated to In Progress.");
        loadDetail(token);
      } else {
        const data = await res.json().catch(() => ({}));
        setErrorMsg(data.detail || "Failed to accept ticket");
      }
    } catch (e: any) {
      setErrorMsg(e.message || "Network error while accepting work");
    } finally {
      setAccepting(false);
    }
  };

  const handleBlock = async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/officer/tickets/${ticketId}/block`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ reason_code: blockReason }),
      });
      if (res.ok) {
        setShowBlock(false);
        loadDetail(token);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !photoFile) {
      setErrorMsg("Please capture or select an after-repair photo");
      return;
    }
    setErrorMsg(null);
    setResolving(true);

    const formData = new FormData();
    formData.append("photo", photoFile);
    formData.append("lat", (lat || ticket.lat).toString());
    formData.append("lng", (lng || ticket.lng).toString());

    try {
      const res = await fetch(`${API_BASE}/api/officer/tickets/${ticketId}/resolve`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) {
        setErrorMsg(data.detail || "Resolution failed");
      } else {
        setSuccessMsg(data.message || "Resolved! Sent to citizen for confirmation.");
        loadDetail(token);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to resolve");
    } finally {
      setResolving(false);
    }
  };

  if (loading || !ticket) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-emerald-600 mb-3" />
        <p className="text-slate-600">Loading Ticket Action Console...</p>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-6 space-y-6">
      <Link href="/officer" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-900">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to Officer Inbox
      </Link>

      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-black text-slate-900">{ticket.code}</h1>
          <span className="text-xs uppercase font-extrabold px-2.5 py-1 bg-amber-100 text-amber-900 rounded-full">
            {ticket.status.replace(/_/g, " ")}
          </span>
        </div>
        <p className="text-xs text-slate-600 capitalize font-medium">
          {ticket.category.replace(/_/g, " ")} • {ticket.ward}
        </p>
        <p className="text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border">
          {ticket.reports?.[0]?.text || "Civic report received"}
        </p>

        {(ticket.status === "assigned" || ticket.status === "open") && (
          <div className="pt-2 flex gap-3">
            <button 
              onClick={handleAccept} 
              disabled={accepting}
              className="flex-1 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold p-2.5 rounded-lg text-xs shadow flex items-center justify-center gap-2 transition"
            >
              {accepting ? <RefreshCw className="w-4 h-4 animate-spin" /> : null}
              {accepting ? "Starting Work..." : "Accept & Start Work"}
            </button>
            <button onClick={() => setShowBlock(true)} className="px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold rounded-lg text-xs">
              Block / Delay Reason
            </button>
          </div>
        )}
      </div>

      {/* Block Modal */}
      {showBlock && (
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl space-y-3">
          <h3 className="text-xs font-bold text-amber-900">Choose Delay Reason (Publicly Visible to Citizens)</h3>
          <select 
            value={blockReason} 
            onChange={(e) => setBlockReason(e.target.value)}
            className="w-full text-xs p-2 border rounded-lg bg-white"
          >
            <option value="budget">Pending Budget Sanction</option>
            <option value="jurisdiction">Inter-Departmental / NHAI Coordination</option>
            <option value="material">Specialized Material Procurement Delay</option>
            <option value="safety">Monsoon / Site Safety Hazard</option>
          </select>
          <div className="flex gap-2">
            <button onClick={handleBlock} className="px-3 py-1.5 bg-amber-600 text-white rounded text-xs font-bold">
              Publish Reason
            </button>
            <button onClick={() => setShowBlock(false)} className="px-3 py-1.5 bg-slate-200 text-slate-700 rounded text-xs font-bold">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Verified Resolution Form */}
      {ticket.status !== "verified_closed" && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Camera className="w-5 h-5 text-emerald-600" />
            Verified Closure Proof (Geotag + Live Photo)
          </h2>

          {errorMsg && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {successMsg && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-lg flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleResolve} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">
                Upload After-Repair Photo (Camera or Gallery)
              </label>
              <input 
                type="file" 
                accept="image/*"
                onChange={(e) => setPhotoFile(e.target.files?.[0] || null)}
                className="w-full text-xs border rounded-lg p-2 bg-slate-50 file:mr-3 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700"
              />
            </div>

            <button 
              type="submit" 
              disabled={resolving}
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold p-3 rounded-lg text-sm shadow flex items-center justify-center gap-2"
            >
              {resolving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
              Submit Verified Resolution
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
