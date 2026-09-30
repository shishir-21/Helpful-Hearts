"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type Doctor = { id: string; full_name: string; specialty: string; hospital_name: string | null; is_demo: boolean; years_experience: number | null };
type Slot = { starts_at: string; ends_at: string; timezone: string };
type Appointment = { id: string; booking_reference: string; starts_at: string; status: string };
type DoctorResults = { items: Doctor[] };
const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export default function BookSlotPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorId, setDoctorId] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [selected, setSelected] = useState("");
  const [loading, setLoading] = useState(true);
  const [booking, setBooking] = useState(false);
  const [error, setError] = useState("");
  const [confirmation, setConfirmation] = useState<Appointment | null>(null);
  const [reason, setReason] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(sessionStorage.getItem("helpful_hearts_access_token") || "");
    const requestedDoctor = new URLSearchParams(window.location.search).get("doctor") || "";
    fetch(`${API}/doctors?page=1&page_size=100`)
      .then(async r => { if (!r.ok) throw new Error("Could not load registered doctors."); return r.json() as Promise<DoctorResults>; })
      .then(data => { setDoctors(data.items); setDoctorId(data.items.some(d => d.id === requestedDoctor) ? requestedDoctor : data.items[0]?.id || ""); })
      .catch(e => setError(e.message)).finally(() => setLoading(false));
  }, []);
  useEffect(() => {
    if (!doctorId) return;
    setSlots([]); setSelected(""); setConfirmation(null);
    fetch(`${API}/doctors/${doctorId}/availability?days=30`)
      .then(async r => { if (!r.ok) throw new Error("Could not load available slots."); return r.json() as Promise<Slot[]>; })
      .then(setSlots).catch(e => setError(e.message));
  }, [doctorId]);
  const chosenDoctor = doctors.find(d => d.id === doctorId);
  const grouped = useMemo(() => slots.reduce<Record<string, Slot[]>>((acc, slot) => {
    const day = new Date(slot.starts_at).toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric", timeZone: slot.timezone });
    (acc[day] ||= []).push(slot); return acc;
  }, {}), [slots]);
  async function submit() {
    if (!token) { setError("Please log in or register before booking."); return; }
    if (!selected) return;
    setBooking(true); setError("");
    try {
      const response = await fetch(`${API}/appointments`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ doctor_id: doctorId, starts_at: selected, reason: reason.trim() || null }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Booking failed. Please select another slot.");
      setConfirmation(data);
    } catch (e) { setError(e instanceof Error ? e.message : "Booking failed."); }
    finally { setBooking(false); }
  }
  return <main className="min-h-screen">
    <header className="site-header"><div className="container header-inner"><Link href="/" className="brand"><span className="brand-mark">♥</span> Helpful Hearts</Link><nav className="header-nav"><Link href="/find-doctors">Find Doctors</Link><Link className="nav-active" href="/book-slot">Book Your Slot</Link><Link href="/auth">Login / Register</Link><Link href="/appointments">My Appointments</Link></nav></div></header>
    <section className="container profile-section"><Link href="/" className="back-link">← Home</Link><div className="results-heading"><div><p className="eyebrow">BOOK YOUR SLOT</p><h1>Choose a doctor and time</h1><p className="hero-copy">Book with a registered doctor. Demo profiles are fictional and for testing only.</p></div></div>
      {loading && <div className="state-card" role="status">Loading doctors…</div>}
      {!loading && doctors.length > 0 && <div className="search-panel"><label className="search-field"><span>Doctor</span><select value={doctorId} onChange={e => setDoctorId(e.target.value)}>{doctors.map(d => <option key={d.id} value={d.id}>{d.full_name} — {d.specialty}{d.is_demo ? " (Demo)" : ""}</option>)}</select></label></div>}
      {chosenDoctor && <article className="doctor-card mt-6"><h2>{chosenDoctor.full_name}</h2><p className="doctor-specialty">{chosenDoctor.specialty}</p><p>{chosenDoctor.hospital_name || "Clinic not specified"}{chosenDoctor.years_experience !== null ? ` · ${chosenDoctor.years_experience} years experience` : ""}</p>{chosenDoctor.is_demo && <div className="demo-notice">Fictional demo doctor — do not use for real medical care.</div>}</article>}
      {!token && <div className="state-card mt-4">You need a patient account to confirm a booking. <Link className="card-link" href="/auth">Login / Register →</Link></div>}
      <section className="profile-block"><h2>Available slots</h2>{Object.keys(grouped).length === 0 ? <p>{doctorId ? "No future slots are configured. Run the demo seed command for the demo doctor." : "Choose a doctor to see availability."}</p> : Object.entries(grouped).map(([day, daySlots]) => <div key={day} className="mb-5"><h3 className="font-semibold mb-2">{day}</h3><div className="flex flex-wrap gap-2">{daySlots.map(slot => <button key={slot.starts_at} type="button" onClick={() => setSelected(slot.starts_at)} className={`rounded-xl border px-4 py-2 text-sm ${selected === slot.starts_at ? "bg-blue-700 text-white" : "bg-white"}`}>{new Date(slot.starts_at).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit", timeZone: slot.timezone })}</button>)}</div></div>)}</section>
      {selected && <div className="search-panel"><label className="search-field"><span>Reason (optional)</span><input value={reason} maxLength={2000} onChange={e => setReason(e.target.value)} placeholder="Brief appointment reason" /></label><button className="primary-button" disabled={booking || !token} onClick={submit}>{booking ? "Booking…" : "Confirm booking →"}</button></div>}
      {error && <div className="state-card error-state mt-4" role="alert">{error}</div>}
      {confirmation && <div className="state-card mt-4"><h2 className="text-xl font-bold">Booking confirmed</h2><p>Reference: <strong>{confirmation.booking_reference}</strong></p><p>Status: {confirmation.status}</p><p>{new Date(confirmation.starts_at).toLocaleString()}</p><Link className="card-link" href="/appointments">View my appointments →</Link></div>}
      {!loading && doctors.length===0 && !error && <div className="state-card">No verified doctors are available yet. Run the demo seed command locally.</div>}
    </section><footer className="site-footer"><div className="container">Helpful Hearts · Demo information is fictional.</div></footer>
  </main>;
}
