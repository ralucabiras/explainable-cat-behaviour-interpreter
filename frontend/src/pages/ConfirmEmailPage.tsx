import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { PublicHeader } from "../components/PublicHeader";

export function ConfirmEmailPage() {
  const [params] = useSearchParams(); const token = params.get("token"); const [status, setStatus] = useState<"loading" | "success" | "error">(token ? "loading" : "error"); const [message, setMessage] = useState(token ? "Confirming your email…" : "This confirmation link is incomplete.");
  useEffect(() => { if (!token) return; void api.confirmEmail(token).then((response) => { setStatus("success"); setMessage(response.message); }).catch((reason) => { setStatus("error"); setMessage(reason instanceof Error ? reason.message : "The link could not be confirmed."); }); }, [token]);
  return <div className="public-shell"><PublicHeader /><main className="confirmation-main"><section className={`auth-card confirmation ${status}`}><div className="mail-icon">{status === "success" ? "✓" : status === "error" ? "!" : "…"}</div><h1>{status === "loading" ? "Confirming email" : status === "success" ? "Email confirmed" : "Link unavailable"}</h1><p>{message}</p>{status !== "loading" && <Link className="primary link-button" to={status === "success" ? "/login" : "/signup"}>{status === "success" ? "Continue to login" : "Create an account"}</Link>}</section></main></div>;
}
