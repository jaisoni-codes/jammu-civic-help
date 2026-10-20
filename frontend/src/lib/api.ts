const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchCityOverview() {
  const res = await fetch(`${API_BASE}/api/public/city`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load city data");
  return res.json();
}

export async function fetchWardDetails(wardId: string | number) {
  const res = await fetch(`${API_BASE}/api/public/wards/${wardId}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load ward data");
  return res.json();
}

export async function fetchTicketPublic(code: string) {
  const res = await fetch(`${API_BASE}/api/public/tickets/${code}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load ticket");
  return res.json();
}

export async function officerLogin(officerId: number, pin: string) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ officer_id: officerId, pin }),
  });
  if (!res.ok) throw new Error("Invalid Officer ID or PIN");
  return res.json();
}

export async function fetchOfficerTickets(token: string) {
  const res = await fetch(`${API_BASE}/api/officer/tickets`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to load officer inbox");
  return res.json();
}

export async function fetchAdminOverview(token: string) {
  const res = await fetch(`${API_BASE}/api/admin/overview`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to load admin overview");
  return res.json();
}

export async function fetchAdminHeatmap(token: string) {
  const res = await fetch(`${API_BASE}/api/admin/heatmap`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to load heatmap");
  return res.json();
}
