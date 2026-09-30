import Link from "next/link";

export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-16 sm:px-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-16">
        <header className="flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold tracking-tight text-blue-700">Helpful Hearts</Link>
          <nav className="flex items-center gap-5 text-sm font-medium text-slate-600">
            <Link href="/doctors" className="hover:text-blue-700">Find a doctor</Link>
            <Link href="/auth" className="hover:text-blue-700">Login / Register</Link>
          </nav>
        </header>
        <section className="rounded-3xl border border-blue-100 bg-white px-8 py-14 shadow-sm sm:px-14">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">Care starts with clarity</p>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-6xl">Find the right care, with confidence.</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">Search for doctors, explore their profiles, and find the information you need to make an informed choice.</p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link href="/doctors" className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800">Find a doctor →</Link>
            <Link href="/auth" className="rounded-xl border border-slate-200 px-5 py-3 font-semibold text-slate-700 hover:border-blue-200 hover:text-blue-700">Get started</Link>
          </div>
        </section>
        <p className="text-center text-sm text-slate-500">Doctor discovery is available. Appointment booking is coming in a later phase.</p>
      </div>
    </main>
  );
}
