import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { PublicHeader } from "../components/PublicHeader";

export function SignUpPage() {
  const [error, setError] = useState("");
  const [sentTo, setSentTo] = useState("");
  const [developmentUrl, setDevelopmentUrl] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password"));
    if (password !== String(form.get("confirm_password"))) { setError("Passwords do not match."); return; }
    try {
      const response = await api.signUp({ display_name: String(form.get("display_name")), email: String(form.get("email")), password });
      setSentTo(response.email); setDevelopmentUrl(response.development_confirmation_url ?? "");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not create the account."); }
  }
  return <AuthPage>{sentTo ? <div className="auth-success"><div className="mail-icon">✉</div><p className="eyebrow">One more step</p><h1>Check your email</h1><p>We sent a confirmation link to <strong>{sentTo}</strong>. Confirm it before logging in.</p>{developmentUrl && <a className="primary link-button" href={developmentUrl}>Open development confirmation link</a>}<Link to="/login">Return to login</Link></div> : <><p className="eyebrow">Create your profile</p><h1>Start understanding the small signals.</h1><p>One account keeps each cat’s profile and observations together.</p><form className="auth-form" onSubmit={submit}><label>Your name<input name="display_name" required minLength={2} autoComplete="name" /></label><label>Email<input name="email" type="email" required autoComplete="email" /></label><label>Password<input name="password" type="password" required minLength={8} autoComplete="new-password" /><small>At least 8 characters</small></label><label>Confirm password<input name="confirm_password" type="password" required minLength={8} autoComplete="new-password" /></label>{error && <p className="error">{error}</p>}<button className="primary auth-submit">Create account</button></form><p className="auth-switch">Already registered? <Link to="/login">Log in</Link></p></>}</AuthPage>;
}

function AuthPage({ children }: { children: React.ReactNode }) {
  return <div className="public-shell"><PublicHeader /><main className="auth-main"><section className="auth-card">{children}</section><aside className="auth-aside"><p className="eyebrow">Your private journal</p><blockquote>“Context changes the meaning of behaviour. Keep the details together, one observation at a time.”</blockquote></aside></main></div>;
}
