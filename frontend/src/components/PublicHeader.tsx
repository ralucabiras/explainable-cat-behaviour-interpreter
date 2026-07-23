import { Link } from "react-router-dom";

export function PublicHeader() {
  return <header className="public-header">
    <Link className="brand brand-link" to="/"><span aria-hidden="true">◇</span><span>Whiskerwise</span></Link>
    <nav aria-label="Account navigation"><Link className="text-link" to="/about">About us</Link><Link className="text-link" to="/login">Log in</Link><Link className="primary link-button" to="/signup">Create account</Link></nav>
  </header>;
}
