"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

type AuthResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
  };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export default function AuthPage() {
  const [mode, setMode] = useState<"login" | "register">("register");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          mode === "register"
            ? { full_name: fullName, email, password }
            : { email, password },
        ),
      });
      const data = (await response.json()) as AuthResponse | { detail?: string };

      if (!response.ok) {
        setMessage("detail" in data ? data.detail ?? "Something went wrong." : "Something went wrong.");
        return;
      }

      const result = data as AuthResponse;
      sessionStorage.setItem("helpful_hearts_access_token", result.access_token);
      setMessage(`Welcome, ${result.user.full_name}! You are signed in.`);
    } catch {
      setMessage("Could not connect to the server. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen px-6 py-12 sm:px-10">
      <div className="mx-auto max-w-5xl">
        <header className="flex items-center justify-between">
          <Link href="/" className="text-2xl font-bold tracking-tight text-blue-700">
            Helpful Hearts
          </Link>
          <Link href="/" className="text-sm font-medium text-slate-600 hover:text-blue-700">
            Back to home
          </Link>
        </header>

        <section className="mx-auto mt-16 max-w-md rounded-3xl border border-blue-100 bg-white p-8 shadow-sm sm:p-10">
          <p className="text-sm font-semibold uppercase tracking-[0.18em] text-blue-700">
            Your care account
          </p>
          <h1 className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            {mode === "register" ? "Create your account" : "Welcome back"}
          </h1>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            {mode === "register"
              ? "Register as a patient to get started."
              : "Sign in to continue to Helpful Hearts."}
          </p>

          <div className="mt-6 grid grid-cols-2 rounded-xl bg-slate-100 p-1 text-sm font-semibold">
            <button
              type="button"
              onClick={() => { setMode("register"); setMessage(""); }}
              className={`rounded-lg px-3 py-2 ${mode === "register" ? "bg-white text-blue-700 shadow-sm" : "text-slate-600"}`}
            >
              Register
            </button>
            <button
              type="button"
              onClick={() => { setMode("login"); setMessage(""); }}
              className={`rounded-lg px-3 py-2 ${mode === "login" ? "bg-white text-blue-700 shadow-sm" : "text-slate-600"}`}
            >
              Login
            </button>
          </div>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {mode === "register" && (
              <label className="block text-sm font-medium text-slate-700">
                Full name
                <input
                  required
                  minLength={2}
                  maxLength={120}
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  autoComplete="name"
                  className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  placeholder="Your full name"
                />
              </label>
            )}
            <label className="block text-sm font-medium text-slate-700">
              Email address
              <input
                required
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                autoComplete="email"
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                placeholder="you@example.com"
              />
            </label>
            <label className="block text-sm font-medium text-slate-700">
              Password
              <input
                required
                type="password"
                minLength={mode === "register" ? 8 : 1}
                maxLength={128}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete={mode === "register" ? "new-password" : "current-password"}
                className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                placeholder={mode === "register" ? "At least 8 characters" : "Your password"}
              />
            </label>
            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-blue-700 px-5 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Please wait..." : mode === "register" ? "Create account" : "Sign in"}
            </button>
          </form>

          {message && (
            <p role="status" className="mt-4 rounded-xl bg-blue-50 px-4 py-3 text-sm text-blue-800">
              {message}
            </p>
          )}
          <p className="mt-6 text-xs leading-5 text-slate-500">
            Registration creates a patient account. Doctor and admin access is assigned separately.
          </p>
        </section>
      </div>
    </main>
  );
}
