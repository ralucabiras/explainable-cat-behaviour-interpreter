import { Link } from "react-router-dom";
import { PublicHeader } from "../components/PublicHeader";

export function LandingPage() {
  return <div className="public-shell"><PublicHeader /><main className="landing-main">
    <section className="hero">
      <div><p className="eyebrow">Understand the signals</p><h1>A clearer view of your cat’s behaviour.</h1><p className="hero-copy">Turn everyday observations into careful, explainable interpretations—grounded in context and honest about uncertainty.</p><div className="hero-actions"><Link className="primary link-button" to="/signup">Start a behaviour journal</Link><Link className="quiet link-button" to="/login">I already have an account</Link></div></div>
      <div className="hero-visual" aria-label="Example interpretation"><div className="cat-mark">◌</div><p className="eyebrow">Possible interpretation</p><h2>Alert or curious</h2><p>Exploration and close watching may reflect interest in a changed environment.</p><div className="signal-row"><span>Text clues</span><span>Context</span><span>Alternatives</span></div></div>
    </section>
    <section className="feature-strip"><article><span>01</span><h2>Describe</h2><p>Record what your cat did in your own words.</p></article><article><span>02</span><h2>Add context</h2><p>Include routine, visitors, feeding, travel, and known triggers.</p></article><article><span>03</span><h2>Understand</h2><p>See evidence, alternatives, uncertainty, and safe next steps.</p></article></section>
    <section className="ethics-banner"><p className="eyebrow">Built for responsible interpretation</p><h2>Useful guidance without pretending behaviour is certain.</h2><p>Whiskerwise is not a veterinary diagnostic tool. Sudden or concerning changes should always be discussed with a veterinarian.</p></section>
  </main></div>;
}
