import { FormEvent, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../auth/AuthContext";
import { PublicHeader } from "../components/PublicHeader";

export function LoginPage() {
  const { user, login } = useAuth(); const navigate = useNavigate(); const [error, setError] = useState(""); const [unconfirmedEmail, setUnconfirmedEmail] = useState(""); const [resendMessage, setResendMessage] = useState("");
  if (user) return <Navigate to="/app" replace />;
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); const form = new FormData(event.currentTarget);
    const email = String(form.get("email"));
    try { await login(email, String(form.get("password"))); navigate("/app"); }
    catch (reason) { const message = reason instanceof Error ? reason.message : "Could not log in."; setError(message); setUnconfirmedEmail(message.toLowerCase().includes("confirm your email") ? email : ""); }
  }
  async function resend() { setResendMessage(""); try { const response = await api.resendConfirmation(unconfirmedEmail); setResendMessage(response.message); } catch (reason) { setResendMessage(reason instanceof Error ? reason.message : "Could not resend confirmation."); } }
  return <div className="public-shell"><PublicHeader /><main className="auth-main"><section className="auth-card"><p className="eyebrow">Welcome back</p><h1>Continue your cat’s story.</h1><p>Log in to access profiles and behaviour observations.</p><form className="auth-form" onSubmit={submit}><label>Email<input name="email" type="email" required autoComplete="email" /></label><label>Password<input name="password" type="password" required autoComplete="current-password" /></label>{error && <p className="error">{error}</p>}{unconfirmedEmail && <button type="button" className="quiet" onClick={() => void resend()}>Resend confirmation email</button>}{resendMessage && <p className="success">{resendMessage}</p>}<button className="primary auth-submit">Log in</button></form><p className="auth-switch">New here? <Link to="/signup">Create an account</Link></p></section><aside className="auth-aside login-art"><div className="moon">◇</div><h2>Notice patterns over time.</h2><p>A consistent journal makes behavioural changes easier to see and explain.</p></aside></main></div>;
}
