import Link from "next/link";

export default function FindDoctorsPage() {
  return (
    <main className="min-h-screen">
      <header className="site-header"><div className="container header-inner">
        <Link href="/" className="brand"><span className="brand-mark">♥</span> Helpful Hearts</Link>
        <nav className="header-nav"><Link className="nav-active" href="/find-doctors">Find Doctors</Link><Link href="/doctors">Book Your Slot</Link><Link href="/auth">Login / Register</Link></nav>
      </div></header>
      <section className="search-hero"><div className="container">
        <p className="eyebrow">DOCTOR DISCOVERY</p><h1>Find doctors beyond Helpful Hearts.</h1>
        <p className="hero-copy">Explore public doctor information and professional profiles from external sources.</p>
        <div className="state-card discovery-notice"><div className="empty-icon" aria-hidden="true">⌕</div>
          <h2>External doctor search is coming soon</h2>
          <p>We’re preparing a source-backed search so profiles can show where information came from. Education, experience, awards, and career history will only appear when supported by a source.</p>
          <p>Doctors found here won’t automatically be available for appointments on Helpful Hearts.</p>
          <Link className="primary-button" href="/doctors">Browse registered doctors <span aria-hidden="true">→</span></Link>
        </div>
      </div></section>
      <footer className="site-footer"><div className="container">Helpful Hearts <span>·</span> Public information may be incomplete and should be verified with the provider.</div></footer>
    </main>
  );
}
