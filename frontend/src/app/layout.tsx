import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "CivicHelp Jammu | Civic Trust Engine",
  description: "A verifiable civic trust engine for Jammu Smart City Hackathon",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} min-h-screen bg-slate-50 text-slate-900 flex flex-col`}>
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t bg-white py-6 text-center text-xs text-slate-500">
          <div className="max-w-7xl mx-auto px-4 space-y-1">
            <p className="font-semibold text-slate-800">
              CivicHelp Jammu — Jammu Municipal Corporation (JMC) Citizen Services
            </p>
            <p className="text-slate-400">
              An open civic accountability initiative for verified municipal closures across all 75 wards of Jammu.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
