"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Appointment = {
  id: string;
  doctor_id: string;
  starts_at: string;
  ends_at: string;
  status: string;
  booking_reference: string;
  reason: string | null;
};
type Slot = { starts_at: string; ends_at: string; timezone: string };
type History = {
  id: string;
  previous_status: string | null;
  new_status: string;
  event: string;
  note: string | null;
  created_at: string;
};
const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
const ACTIVE = new Set(["confirmed", "pending"]);
const CUTOFF_MS = 12 * 60 * 60 * 1000;

export default function AppointmentsPage() {
  const [items, setItems] = useState<Appointment[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState("");
  const [busyId, setBusyId] = useState("");
  const [cancelReasons, setCancelReasons] = useState<Record<string, string>>({});
  const [rescheduleId, setRescheduleId] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [historyById, setHistoryById] = useState<Record<string, History[]>>({});
  const [historyOpen, setHistoryOpen] = useState("");

  async function loadAppointments(authToken: string) {
    const response = await fetch(`${API}/appointments`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });
    if (!response.ok) throw new Error("Unable to load appointments. Please sign in again.");
    setItems(await response.json() as Appointment[]);
  }

  useEffect(() => {
    const authToken = sessionStorage.getItem("helpful_hearts_access_token") || "";
    setToken(authToken);
    if (!authToken) {
      setError("Please log in to view your appointments.");
      setLoading(false);
      return;
    }
    loadAppointments(authToken)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Unable to load appointments."))
      .finally(() => setLoading(false));
  }, []);

  async function cancel(appointment: Appointment) {
    if (!token) return;
    setBusyId(appointment.id);
    setError("");
    setNotice("");
    try {
      const response = await fetch(`${API}/appointments/${appointment.id}/cancel`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ reason: cancelReasons[appointment.id]?.trim() || null }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Cancellation failed.");
      await loadAppointments(token);
      setNotice("Appointment cancelled. Its slot is now available again.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Cancellation failed.");
    } finally {
      setBusyId("");
    }
  }

  async function startReschedule(appointment: Appointment) {
    setError("");
    setNotice("");
    setSelectedSlot("");
    setSlots([]);
    setRescheduleId(appointment.id);
    try {
      const response = await fetch(`${API}/doctors/${appointment.doctor_id}/availability?days=30`);
      if (!response.ok) throw new Error("Unable to load available slots.");
      const available = await response.json() as Slot[];
      setSlots(available.filter(slot => new Date(slot.starts_at).getTime() !== new Date(appointment.starts_at).getTime()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load available slots.");
    }
  }

  async function reschedule(appointment: Appointment) {
    if (!token || !selectedSlot) return;
    setBusyId(appointment.id);
    setError("");
    setNotice("");
    try {
      const response = await fetch(`${API}/appointments/${appointment.id}/reschedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ starts_at: selectedSlot }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Rescheduling failed.");
      await loadAppointments(token);
      setRescheduleId("");
      setSelectedSlot("");
      setNotice("Appointment rescheduled successfully.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Rescheduling failed.");
    } finally {
      setBusyId("");
    }
  }

  async function toggleHistory(appointmentId: string) {
    if (historyOpen === appointmentId) {
      setHistoryOpen("");
      return;
    }
    setHistoryOpen(appointmentId);
    if (historyById[appointmentId] || !token) return;
    try {
      const response = await fetch(`${API}/appointments/${appointmentId}/history`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error("Unable to load appointment history.");
      setHistoryById(previous => ({ ...previous, [appointmentId]: await response.json() as History[] }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to load history.");
    }
  }

  const now = Date.now();
  return (
    <main className="min-h-screen">
      <header className="site-header">
        <div className="container header-inner">
          <Link href="/" className="brand"><span className="brand-mark">♥</span> Helpful Hearts</Link>
          <nav className="header-nav">
            <Link href="/find-doctors">Find Doctors</Link>
            <Link href="/book-slot">Book Your Slot</Link>
            <Link href="/auth">Login / Register</Link>
            <Link href="/appointments">My Appointments</Link>
          </nav>
        </div>
      </header>
      <section className="container profile-section">
        <p className="eyebrow">PATIENT DASHBOARD</p>
        <h1 className="text-3xl font-bold mb-6">My appointments</h1>
        <p className="hero-copy mb-6">You can cancel or reschedule an appointment at least 12 hours before its start time.</p>
        {loading && <div className="state-card" role="status">Loading appointments…</div>}
        {!loading && error && <div className="state-card error-state" role="alert">{error} <Link href="/auth" className="card-link">Login →</Link></div>}
        {notice && <div className="state-card mt-4" role="status">{notice}</div>}
        {!loading && !error && items.length === 0 && <div className="state-card">No appointments yet. <Link href="/book-slot" className="card-link">Book a slot →</Link></div>}
        {items.map(appointment => {
          const canManage = ACTIVE.has(appointment.status) && new Date(appointment.starts_at).getTime() - now >= CUTOFF_MS;
          return (
            <article key={appointment.id} className="doctor-card mb-4">
              <span className="verified-badge">{appointment.status}</span>
              <h2 className="text-xl font-semibold mt-3">Appointment</h2>
              <p>{new Date(appointment.starts_at).toLocaleString()}</p>
              <p>Reference: {appointment.booking_reference}</p>
              {appointment.reason && <p>Reason: {appointment.reason}</p>}
              {ACTIVE.has(appointment.status) && !canManage && <p className="mt-3">Cancellation and rescheduling close 12 hours before the appointment.</p>}
              {canManage && (
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  <label className="search-field">
                    <span>Cancellation reason (optional)</span>
                    <input
                      value={cancelReasons[appointment.id] || ""}
                      maxLength={1000}
                      onChange={event => setCancelReasons(previous => ({ ...previous, [appointment.id]: event.target.value }))}
                      placeholder="Reason for cancellation"
                    />
                  </label>
                  <button className="primary-button" disabled={busyId === appointment.id} onClick={() => cancel(appointment)}>Cancel appointment</button>
                  <button className="secondary-button" disabled={busyId === appointment.id} onClick={() => startReschedule(appointment)}>Reschedule</button>
                </div>
              )}
              {rescheduleId === appointment.id && (
                <div className="search-panel mt-4">
                  <label className="search-field">
                    <span>Choose a new slot</span>
                    <select value={selectedSlot} onChange={event => setSelectedSlot(event.target.value)}>
                      <option value="">Select an available slot</option>
                      {slots.map(slot => <option key={slot.starts_at} value={slot.starts_at}>{new Date(slot.starts_at).toLocaleString(undefined, { timeZone: slot.timezone })}</option>)}
                    </select>
                  </label>
                  <div className="flex gap-2 mt-3">
                    <button className="primary-button" disabled={!selectedSlot || busyId === appointment.id} onClick={() => reschedule(appointment)}>Confirm reschedule</button>
                    <button className="secondary-button" onClick={() => setRescheduleId("")}>Keep current slot</button>
                  </div>
                </div>
              )}
              <button className="card-link mt-4" onClick={() => toggleHistory(appointment.id)}> {historyOpen === appointment.id ? "Hide history" : "View status history"} </button>
              {historyOpen === appointment.id && (
                <div className="mt-3">
                  {(historyById[appointment.id] || []).length === 0
                    ? <p>No history recorded yet.</p>
                    : historyById[appointment.id].map(event => (
                      <p key={event.id} className="mb-2">
                        <strong>{event.event}</strong> · {new Date(event.created_at).toLocaleString()}
                        {event.note ? ` — ${event.note}` : ""}
                      </p>
                    ))}
                </div>
              )}
            </article>
          );
        })}
      </section>
    </main>
  );
}
