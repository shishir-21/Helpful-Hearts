import Link from "next/link";

const journeys = [
  { number: "01", title: "Find Doctors", description: "Explore doctor information and public profiles. External doctor discovery will be added once a reliable source is configured.", href: "/find-doctors", action: "Explore doctors", tone: "blue" },
  { number: "02", title: "Book Your Slot", description: "Browse doctors who have registered on Helpful Hearts. Appointment booking will become available as schedules are implemented.", href: "/doctors", action: "View registered doctors", tone: "green" },
];

export default function HomePage() {
  return (
    <main className="min-h-screen">
      <header className="site-header"><div className="container header-inner">
        <Link href="/" className="brand"><span className="brand-mark">♥</span> Helpful Hearts</Link>
        <nav className="header-nav"><Link href="/find-doctors">Find Doctors</Link><Link href="/doctors">Book Your Slot</Link><Link href="/auth">Login / Register</Link></nav>
      </div></header>
      <section className="home-hero"><div className="container">
        <p className="eyebrow">CARE STARTS WITH CLARITY</p>
        <h1>Healthcare discovery, made simpler.</h1>
        <p className="hero-copy">Explore doctor information or find registered doctors on Helpful Hearts. Choose the path that fits what you need.</p>
        <div className="journey-grid">{journeys.map((journey) => <article className={`journey-card journey-${journey.tone}`} key={journey.number}>
          <span className="journey-number">{journey.number}</span><h2>{journey.title}</h2><p>{journey.description}</p>
          <Link className="journey-link" href={journey.href}>{journey.action} <span aria-hidden="true">→</span></Link>
        </article>)}</div>
      </div></section>
      <footer className="site-footer"><div className="container">Helpful Hearts <span>·</span> Doctor information is for discovery, not medical advice.</div></footer>
    </main>
  );
}
