"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Camera, MapPin, Send, CheckCircle2, AlertTriangle, 
  ShieldCheck, Sparkles, RefreshCw, ArrowRight, Zap, Info
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Pre-configured Jammu Landmarks for quick testing if device GPS is blocked
const JAMMU_LOCALITIES = [
  { name: "Ward 7 - Raghunath Bazaar (Old City)", lat: 32.7252, lng: 74.8605 },
  { name: "Ward 1 - Purani Mandi / Heritage City", lat: 32.7285, lng: 74.8631 },
  { name: "Ward 12 - Gandhi Nagar South", lat: 32.7056, lng: 74.8622 },
  { name: "Ward 18 - Shastri Nagar", lat: 32.7001, lng: 74.8580 },
  { name: "Ward 21 - Talab Tillo Central", lat: 32.7230, lng: 74.8250 },
  { name: "Ward 30 - Janipur Main", lat: 32.7560, lng: 74.8460 },
];

export default function QuickReportPage() {
  const [coords, setCoords] = useState<{ lat: number; lng: number } | null>(null);
  const [gpsLoading, setGpsLoading] = useState(false);
  const [locationName, setLocationName] = useState<string>("Auto-detecting GPS...");
  const [text, setText] = useState("");
  const [photo, setPhoto] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  
  const [submitting, setSubmitting] = useState(false);
  const [rejectionError, setRejectionError] = useState<{ message: string; detected?: string } | null>(null);
  const [successResult, setSuccessResult] = useState<any | null>(null);

  // Auto-acquire browser geolocation
  const detectLocation = () => {
    setGpsLoading(true);
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude });
          setLocationName(`Live Device GPS (${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)})`);
          setGpsLoading(false);
        },
        () => {
          // Default to Ward 7 Raghunath Bazaar if permission denied
          setCoords({ lat: 32.7252, lng: 74.8605 });
          setLocationName("Raghunath Bazaar, Ward 7 (Centroid Fallback)");
          setGpsLoading(false);
        },
        { enableHighAccuracy: true, timeout: 6000 }
      );
    } else {
      setCoords({ lat: 32.7252, lng: 74.8605 });
      setLocationName("Raghunath Bazaar, Ward 7 (Centroid Fallback)");
      setGpsLoading(false);
    }
  };

  useEffect(() => {
    detectLocation();
  }, []);

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const f = e.target.files[0];
      setPhoto(f);
      setPreviewUrl(URL.createObjectURL(f));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setSubmitting(true);
    setRejectionError(null);

    const formData = new FormData();
    formData.append("text", text);
    formData.append("lat", (coords?.lat || 32.7252).toString());
    formData.append("lng", (coords?.lng || 74.8605).toString());
    if (photo) {
      formData.append("photo", photo);
    }

    try {
      const res = await fetch(`${API_BASE}/api/public/quick-report`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setRejectionError({
          message: data.detail?.message || "Report could not be accepted.",
          detected: data.detail?.detected,
        });
      } else {
        setSuccessResult(data);
      }
    } catch (err: any) {
      setRejectionError({ message: "Network connection failed. Please retry." });
    } finally {
      setSubmitting(false);
    }
  };

  if (successResult) {
    return (
      <div className="max-w-md mx-auto px-4 py-10 space-y-6">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xl text-center space-y-4">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <h1 className="text-xl font-black text-slate-900">
            {successResult.is_new ? "Grievance Registered!" : "Joined Collective Voice!"}
          </h1>

          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
            <span className="text-xs text-slate-400 font-bold block">TICKET TRACKING CODE</span>
            <span className="text-3xl font-black text-slate-900 tracking-wider font-mono">
              {successResult.ticket_code}
            </span>
            <span className="text-xs text-emerald-700 font-semibold block mt-1">
              📍 {successResult.ward_name} · Priority: {successResult.priority_score}
            </span>
          </div>

          <p className="text-xs text-slate-600 leading-relaxed">
            {successResult.message}
          </p>

          <div className="space-y-2 pt-2">
            <Link
              href={`/t/${successResult.ticket_code}`}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 px-4 rounded-xl text-xs flex items-center justify-center gap-2 shadow"
            >
              Track Audit Chain & Proof <ArrowRight className="w-4 h-4" />
            </Link>

            <button
              onClick={() => {
                setSuccessResult(null);
                setText("");
                setPhoto(null);
                setPreviewUrl(null);
              }}
              className="w-full bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold py-2.5 px-4 rounded-xl text-xs transition"
            >
              Report Another Issue
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto px-4 py-6 space-y-5">
      {/* Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center font-black">
            <Zap className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-extrabold text-slate-900 leading-tight">
              CivicHelp Quick-Report
            </h1>
            <p className="text-[11px] text-slate-500">
              CivicHelp Jammu · Zero Login · Instant GPS · AI Verified
            </p>
          </div>
        </div>

        {/* AI Guard Banner */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-xl flex items-start gap-2 text-xs text-blue-900">
          <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
          <p className="leading-snug">
            <b>Anti-Spam AI Active:</b> Reports are verified in real time. Spam, memes, and non-civic messages are rejected automatically.
          </p>
        </div>
      </div>

      {/* Rejection Alert */}
      {rejectionError && (
        <div className="bg-red-50 border border-red-300 rounded-2xl p-4 shadow-sm flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h2 className="text-xs font-black text-red-900 uppercase">
              AI Verification Failed {rejectionError.detected && `(${rejectionError.detected})`}
            </h2>
            <p className="text-xs text-red-700 leading-relaxed font-medium">
              {rejectionError.message}
            </p>
          </div>
        </div>
      )}

      {/* Reporting Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
        
        {/* GPS Location Bar */}
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1">
            📍 Current Location (Auto-Locked)
          </label>
          <div className="flex items-center gap-2 p-2.5 bg-slate-50 border rounded-xl text-xs">
            <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
            <span className="flex-1 font-medium text-slate-800 truncate">
              {gpsLoading ? "Detecting high-accuracy GPS..." : locationName}
            </span>
            <button
              type="button"
              onClick={detectLocation}
              className="p-1.5 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-200"
              title="Refresh GPS"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${gpsLoading ? "animate-spin" : ""}`} />
            </button>
          </div>

          {/* Quick Locality Selector fallback */}
          <div className="mt-1.5 flex items-center gap-1.5">
            <span className="text-[10px] text-slate-400">Or pick ward:</span>
            <select
              onChange={(e) => {
                const idx = Number(e.target.value);
                const loc = JAMMU_LOCALITIES[idx];
                setCoords({ lat: loc.lat, lng: loc.lng });
                setLocationName(loc.name);
              }}
              className="text-[10px] bg-slate-100 border border-slate-200 rounded px-1.5 py-0.5 font-medium text-slate-700 outline-none flex-1"
            >
              {JAMMU_LOCALITIES.map((l, i) => (
                <option key={l.name} value={i}>{l.name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Live Photo Capture (Camera Only) */}
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1">
            📸 Live Camera Photo Proof <span className="text-red-500 font-black">* (Mandatory)</span>
          </label>
          
          <label className="border-2 border-dashed border-slate-300 hover:border-emerald-500 bg-slate-50/50 rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition">
            <input
              type="file"
              accept="image/*"
              capture="environment" // Direct back camera
              required
              onChange={handlePhotoSelect}
              className="hidden"
            />
            {previewUrl ? (
              <div className="space-y-2 text-center">
                <img src={previewUrl} alt="Live Proof" className="max-h-40 rounded-lg object-cover mx-auto border" />
                <span className="text-[10px] text-emerald-700 font-bold block">✓ Live Camera Photo Captured (Click to retake)</span>
              </div>
            ) : (
              <div className="text-center space-y-1">
                <Camera className="w-6 h-6 text-slate-400 mx-auto" />
                <span className="text-xs font-bold text-slate-700 block">Tap to Capture Live Photo</span>
                <span className="text-[10px] text-red-500 font-semibold block">⚠️ Live camera photo is strictly mandatory to prevent fake reports</span>
              </div>
            )}
          </label>
        </div>

        {/* Description Text */}
        <div>
          <label className="text-xs font-bold text-slate-700 block mb-1">
            📝 Describe the Grievance (Hindi or English)
          </label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            required
            placeholder="e.g. Main road par bada gaddha hai, ya 3 din se garbage nahi utha..."
            className="w-full text-xs p-3 border rounded-xl outline-none focus:ring-2 focus:ring-emerald-500 bg-slate-50 focus:bg-white resize-none"
          />
        </div>

        {/* Quick Sample Prompts */}
        <div className="flex gap-1.5 flex-wrap">
          {[
            "Deep pothole causing traffic jam",
            "Streetlight pole wire sparking",
            "Garbage piled up near main gate",
            "Drainage water overflowing"
          ].map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => setText(prompt)}
              className="text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 px-2 py-1 rounded-full font-medium"
            >
              + {prompt}
            </button>
          ))}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={submitting || !text.trim()}
          className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-black py-3 px-4 rounded-xl text-xs flex items-center justify-center gap-2 shadow-lg transition"
        >
          {submitting ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              Verifying with AI & Dispatching...
            </>
          ) : (
            <>
              <Send className="w-4 h-4" />
              Submit Grievance Now
            </>
          )}
        </button>
      </form>
    </div>
  );
}
