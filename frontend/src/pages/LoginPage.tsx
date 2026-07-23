import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { PublicHeader } from "../components/PublicHeader";

export function LoginPage() {
  const { user, login } = useAuth(); const navigate = useNavigate(); const [error, setError] = useState("");
  if (user) return <Navigate to="/app" replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); const form = new FormData(event.currentTarget);
    try { await login(String(form.get("email")), String(form.get("password"))); navigate("/app"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not log in."); }
  }
  return <div className="public-shell"><PublicHeader /><main className="auth-main"><section className="auth-card"><p className="eyebrow">Welcome back</p><h1>Continue your cat’s story.</h1><p>Log in to access profiles and behaviour observations.</p><form className="auth-form" onSubmit={submit}><label>Email<input name="email" type="email" required autoComplete="email" /></label><label>Password<input name="password" type="password" required autoComplete="current-password" /></label>{error && <p className="error">{error}</p>}<button className="primary auth-submit">Log in</button></form><p className="auth-switch">New here? <Link to="/signup">Create an account</Link></p></section><aside className="auth-aside login-art"><div className="moon">◇</div><h2>Notice patterns over time.</h2><p>A consistent journal makes behavioural changes easier to see and explain.</p></aside></main></div>;
}
