"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

type Credential = { id: string; degree: string; institution: string | null; year_awarded: number | null; verification_status: string };
type Doctor = { id: string; full_name: string; specialty: string; hospital_name: string | null; biography: string | null; years_experience: number | null; languages: string | null; public_phone: string | null; public_email: string | null; booking_instructions: string | null; is_demo: boolean; credentials: Credential[] };
const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/\/$/, "");

export default function DoctorProfilePage() {
  const params = useParams<{ id: string }>();
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    fetch(`${API}/doctors/${encodeURIComponent(params.id)}`, { signal: controller.signal })
      .then(async (response) => {
        if (response.status === 404) throw new Error("This doctor profile is unavailable or has not been verified.");
        if (!response.ok) throw new Error("Unable to load this profile. Please try again.");
        return response.json() as Promise<Doctor>;
      })
      .then(setDoctor)
      .catch((reason: unknown) => { if (reason instanceof Error && reason.name !== "AbortError") setError(reason.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [params.id]);

  return <main className="min-h-screen">
    <header className="site-header"><div className="container header-inner"><Link href="/" className="brand"><span className="brand-mark">♥</span> Helpful Hearts</Link><nav className="header-nav"><Link href="/doctors">Find a doctor</Link><Link href="/auth">Login / Register</Link></nav></div></header>
    <section className="container profile-section">
      <Link href="/doctors" className="back-link">← Back to doctor search</Link>
      {loading && <div className="state-card" role="status"><span className="spinner" /> Loading profile…</div>}
      {error && <div className="state-card error-state" role="alert"><h2>Profile unavailable</h2><p>{error}</p><Link className="primary-button inline-button" href="/doctors">Browse doctors</Link></div>}
      {doctor && <div className="profile-layout">
        <article className="profile-main">
          <div className="profile-heading"><div className="doctor-avatar profile-avatar">{doctor.full_name.replace(/^Dr\.?\s*/i, "").split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase()}</div><div><span className="verified-badge">✓ Verified profile</span><h1>{doctor.full_name}</h1><p className="doctor-specialty">{doctor.specialty}</p></div></div>
          {doctor.is_demo && <div className="demo-notice">Demo profile — this is fictional information for testing.</div>}
          <section className="profile-block"><h2>About</h2><p>{doctor.biography || "No biography has been provided for this profile."}</p></section>
          <section className="profile-block"><h2>Qualifications</h2>{doctor.credentials.length ? <ul className="credential-list">{doctor.credentials.map((credential) => <li key={credential.id}><strong>{credential.degree}</strong>{credential.institution && <span>{credential.institution}</span>}{credential.year_awarded && <span>{credential.year_awarded}</span>}<small>{credential.verification_status === "verified" ? "Verified credential" : "Credential status: " + credential.verification_status}</small></li>)}</ul> : <p>No qualifications have been added.</p>}</section>
        </article>
        <aside className="profile-sidebar"><h2>Profile details</h2><dl>
          {doctor.years_experience !== null && <><dt>Experience</dt><dd>{doctor.years_experience} years</dd></>}
          {doctor.hospital_name && <><dt>Clinic / hospital</dt><dd>{doctor.hospital_name}</dd></>}
          {doctor.languages && <><dt>Languages</dt><dd>{doctor.languages}</dd></>}
          {doctor.public_phone && <><dt>Phone</dt><dd><a href={`tel:${doctor.public_phone}`}>{doctor.public_phone}</a></dd></>}
          {doctor.public_email && <><dt>Email</dt><dd><a href={`mailto:${doctor.public_email}`}>{doctor.public_email}</a></dd></>}
        </dl><div className="booking-note"><strong>Appointments</strong><p>{doctor.booking_instructions || "Appointment booking is not available yet."}</p></div></aside>
      </div>}
    </section>
    <footer className="site-footer"><div className="container">Helpful Hearts <span>·</span> Information is for discovery and does not replace professional medical advice.</div></footer>
  </main>;
}
