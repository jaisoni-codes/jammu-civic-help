import Link from "next/link";
import { ShieldCheck, MessageSquare, UserCheck, BarChart3, Sliders, Zap } from "lucide-react";
import LanguageSelector from "./LanguageSelector";

export default function Navbar() {
  return (
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

        <nav className="flex items-center gap-2 sm:gap-3 text-sm font-semibold">
          <Link href="/" className="text-slate-700 hover:text-emerald-700 px-2 py-1 flex items-center gap-1.5 text-xs sm:text-sm">
            <BarChart3 className="w-4 h-4" /> <span className="hidden sm:inline">City Trust</span>
          </Link>
          <Link href="/officer" className="text-slate-700 hover:text-emerald-700 px-2 py-1 flex items-center gap-1.5 text-xs sm:text-sm">
            <UserCheck className="w-4 h-4" /> <span className="hidden sm:inline">Officer Portal</span>
          </Link>
          <Link href="/admin" className="text-slate-700 hover:text-emerald-700 px-2 py-1 flex items-center gap-1.5 hidden md:flex text-xs sm:text-sm">
            <ShieldCheck className="w-4 h-4" /> <span>Admin HQ</span>
          </Link>
          <Link href="/report" className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-xs font-bold shadow flex items-center gap-1.5 shrink-0">
            <Zap className="w-3.5 h-3.5" /> <span>Report Issue</span>
          </Link>
          
          {/* Regional Multi-Language Switcher */}
          <div className="ml-1 shrink-0">
            <LanguageSelector />
          </div>
        </nav>
      </div>
    </header>
  );
}
