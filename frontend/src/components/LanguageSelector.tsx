"use client";

import React, { useEffect, useState } from "react";
import { Globe } from "lucide-react";

declare global {
  interface Window {
    google: any;
    googleTranslateElementInit?: () => void;
  }
}

export const SUPPORTED_LANGUAGES = [
  { code: "en", label: "English", native: "English" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "doi", label: "Dogri", native: "डोगरी" },
  { code: "ur", label: "Urdu", native: "اردو" },
  { code: "pa", label: "Punjabi", native: "ਪੰਜਾਬੀ" },
  { code: "ks", label: "Kashmiri", native: "کٲشُر" },
];

export default function LanguageSelector() {
  const [currentLang, setCurrentLang] = useState("en");
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    // Check if google translate script is already present
    if (document.getElementById("google-translate-script")) {
      setIsLoaded(true);
      return;
    }

    // Set callback
    window.googleTranslateElementInit = () => {
      new window.google.translate.TranslateElement(
        {
          pageLanguage: "en",
          includedLanguages: "en,hi,doi,ur,pa,ks",
          autoDisplay: false,
        },
        "google_translate_element"
      );
      setIsLoaded(true);
    };

    const script = document.createElement("script");
    script.id = "google-translate-script";
    script.src = "//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit";
    script.async = true;
    document.body.appendChild(script);

    // Read cookie if user previously picked a language
    const match = document.cookie.match(/(?:^|;\s*)googtrans=([^;]+)/);
    if (match) {
      const parts = match[1].split("/");
      const lang = parts[parts.length - 1];
      if (lang) setCurrentLang(lang);
    }
  }, []);

  const changeLanguage = (langCode: string) => {
    setCurrentLang(langCode);

    // Set googtrans cookie for domain & path
    const domain = window.location.hostname;
    document.cookie = `googtrans=/en/${langCode}; path=/;`;
    document.cookie = `googtrans=/en/${langCode}; path=/; domain=${domain};`;

    // Attempt triggering Google Translate combo or reload
    const selectElem = document.querySelector(".goog-te-combo") as HTMLSelectElement | null;
    if (selectElem) {
      selectElem.value = langCode;
      selectElem.dispatchEvent(new Event("change"));
    } else {
      window.location.reload();
    }
  };

  return (
    <div className="relative flex items-center">
      {/* Hidden container for Google Translate element */}
      <div id="google_translate_element" className="hidden" />

      <div className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-800 rounded-lg px-2 py-1 transition text-xs font-semibold">
        <Globe className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
        <select
          value={currentLang}
          onChange={(e) => changeLanguage(e.target.value)}
          aria-label="Select Language"
          className="bg-transparent text-xs font-bold text-slate-800 outline-none cursor-pointer pr-1"
        >
          {SUPPORTED_LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.native} ({l.label})
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
