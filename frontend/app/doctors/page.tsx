"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

type Doctor = {
  id: string;
  full_name: string;
  specialty: string;
  hospital_name: string | null;
  biography: string | null;
  years_experience: number | null;
  languages: string | null;
  is_demo: boolean;
  credentials: { id: string; degree: string; institution: string | null; verification_status: string }[];
};
type Results = { items: Doctor[]; total: number; page: number; page_size: number; pages: number };
const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");
const specialties = ["General Medicine", "Cardiology", "Dermatology", "Pediatrics", "Orthopedics", "Neurology"];

export default function DoctorsPage() {
  const [q, setQ] = useState("");
  const [specialty, setSpecialty] = useState("");
  const [location, setLocation] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Results | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const params = new URLSearchParams({ page: String(page), page_size: "9" });
    if (q.trim()) params.set("q", q.trim());
    if (specialty) params.set("specialty", specialty);
    if (location.trim()) params.set("location", location.trim());
    setLoading(true);
    setError("");
    fetch(`${API}/doctors?${params}`, { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Unable to load doctor profiles. Please try again.");
        return response.json() as Promise<Results>;
      })
      .then(setData)
      .catch((reason: unknown) => {
        if (reason instanceof Error && reason.name !== "AbortError") setError(reason.message);
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [q, specialty, location, page]);

  return (
    <main className="min-h-screen">
      <header className="site-header"><div className="container header-inner">
        <Link href="/" className="brand"><span className="brand-mark">♥</span> Helpful Hearts</Link>
        <nav className="header-nav"><Link href="/find-doctors">Find Doctors</Link><Link className="nav-active" href="/doctors">Book Your Slot</Link><Link href="/auth">Login / Register</Link></nav>
      </div></header>
      <section className="search-hero"><div className="container">
        <p className="eyebrow">YOUR HEALTH, YOUR CHOICE</p>
        <h1>Find care that feels right.</h1>
        <p className="hero-copy">Browse verified doctors registered on Helpful Hearts. Appointment booking will be enabled after doctor availability and booking are implemented.</p>
        <div className="search-panel">
          <label className="search-field"><span>Doctor or specialty</span><input value={q} onChange={(e) => { setQ(e.target.value); setPage(1); }} placeholder="e.g. Dr. Sharma, cardiology" /></label>
          <label className="search-field"><span>Specialty</span><select value={specialty} onChange={(e) => { setSpecialty(e.target.value); setPage(1); }}><option value="">All specialties</option>{specialties.map((s) => <option key={s}>{s}</option>)}</select></label>
          <label className="search-field"><span>Clinic / hospital</span><input value={location} onChange={(e) => { setLocation(e.target.value); setPage(1); }} placeholder="Enter clinic name" /></label>
          <button className="primary-button search-button" onClick={() => setPage(1)}>Search <span>→</span></button>
        </div>
      </div></section>
      <section className="container results-section">
        <div className="results-heading"><div><p className="eyebrow">BOOK YOUR SLOT</p><h2>Registered doctors</h2></div>{!loading && !error && <span className="result-count">{data?.total ?? 0} profiles</span>}</div>
        {loading && <div className="state-card" role="status"><span className="spinner" /> Loading doctor profiles…</div>}
        {error && <div className="state-card error-state" role="alert"><h3>Something went wrong</h3><p>{error}</p><button className="secondary-button" onClick={() => setPage((p) => p)}>Try again</button></div>}
        {!loading && !error && data?.items.length === 0 && <div className="state-card empty-state"><div className="empty-icon">⌕</div><h3>No verified profiles found</h3><p>Try another name or specialty. Only verified profiles appear here. External doctor discovery is separate.</p><button className="secondary-button" onClick={() => { setQ(""); setSpecialty(""); setLocation(""); setPage(1); }}>Clear filters</button></div>}
        {!loading && !error && !!data?.items.length && <>
          <div className="doctor-grid">{data.items.map((doctor) => <article className="doctor-card" key={doctor.id}>
            <div className="doctor-card-top"><div className="doctor-avatar">{doctor.full_name.replace(/^Dr\.?\s*/i, "").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</div><span className="verified-badge">✓ Verified profile</span></div>
            <h3>{doctor.full_name}</h3><p className="doctor-specialty">{doctor.specialty}</p>
            <div className="doctor-meta">{doctor.years_experience !== null && <span>◷ {doctor.years_experience} years experience</span>}{doctor.hospital_name && <span>⌖ {doctor.hospital_name}</span>}</div>
            {doctor.credentials.length > 0 && <p className="degree-line">{doctor.credentials.map((c) => c.degree).join(" · ")}</p>}
            {doctor.is_demo && <span className="demo-label">Demo profile</span>}
            <Link className="card-link" href={`/doctors/${doctor.id}`}>View profile <span>→</span></Link>
          </article>)}</div>
          {data.pages > 1 && <div className="pagination"><button className="secondary-button" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</button><span>Page {data.page} of {data.pages}</span><button className="secondary-button" disabled={page >= data.pages} onClick={() => setPage((p) => p + 1)}>Next</button></div>}
        </>}
      </section>
      <footer className="site-footer"><div className="container">Helpful Hearts <span>·</span> Doctor information is for discovery, not medical advice.</div></footer>
    </main>
  );
}
