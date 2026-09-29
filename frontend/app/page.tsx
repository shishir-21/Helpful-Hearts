export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-16 sm:px-10">
      <div className="mx-auto flex max-w-5xl flex-col gap-16">
        <header className="flex items-center justify-between">
          <a href="/" className="text-2xl font-bold tracking-tight text-blue-700">
            Helpful Hearts
          </a>
          <span className="rounded-full border border-blue-100 bg-white px-4 py-2 text-sm text-slate-600">
            Project preview
          </span>
        </header>

        <section className="rounded-3xl border border-blue-100 bg-white px-8 py-14 shadow-sm sm:px-14">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-700">
            Care starts with clarity
          </p>
          <h1 className="max-w-3xl text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            Find the right care, with confidence.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600">
            Search for doctors, explore their profiles, and book appointments.
            Helpful Hearts is being built one feature at a time.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <span className="rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white">
              Find Doctors — coming soon
            </span>
            <span className="rounded-xl border border-slate-200 px-5 py-3 font-semibold text-slate-700">
              AI Health Assistant — planned
            </span>
          </div>
        </section>

        <p className="text-center text-sm text-slate-500">
          Development scaffold · No medical advice or booking is available yet.
        </p>
      </div>
    </main>
  );
}
