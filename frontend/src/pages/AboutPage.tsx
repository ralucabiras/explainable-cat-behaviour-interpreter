import { Link } from "react-router-dom";
import { PublicHeader } from "../components/PublicHeader";

export function AboutPage() {
  return <div className="public-shell">
    <PublicHeader />
    <main className="about-main">
      <section className="about-hero">
        <div>
          <p className="eyebrow">About Whiskerwise</p>
          <h1>Careful technology for a relationship built on observation.</h1>
        </div>
        <p className="about-intro">
          Whiskerwise is an explainable companion-cat behaviour interpreter. It helps owners
          organise what they observe, consider the surrounding context, and explore plausible
          interpretations without pretending an animal’s inner state can be known with certainty.
        </p>
      </section>

      <section className="about-story">
        <div className="about-number">01</div>
        <div>
          <p className="eyebrow">Why we’re building it</p>
          <h2>Behaviour rarely means just one thing.</h2>
          <p>
            Hiding may reflect fear, a need for quiet, environmental stress, or discomfort.
            Vocalising may be social, attention-seeking, or a response to a change in routine.
            Whiskerwise brings those possibilities together and shows the observations behind
            each result.
          </p>
          <p>
            The project begins with cats and combines written descriptions with situational
            context. Video and audio will be introduced only after the core interpretation and
            explanation system is stable.
          </p>
        </div>
      </section>

      <section className="principles-section">
        <p className="eyebrow">Our principles</p>
        <div className="principles-grid">
          <article><span>Evidence</span><h2>Show the reasoning</h2><p>Results identify the clues and context that influenced an interpretation.</p></article>
          <article><span>Uncertainty</span><h2>Leave room for alternatives</h2><p>Behaviour is ambiguous, so confidence and other possible explanations remain visible.</p></article>
          <article><span>Safety</span><h2>Know the boundary</h2><p>Potentially urgent signs lead to veterinary guidance, not an emotional label or diagnosis.</p></article>
          <article><span>Privacy</span><h2>Keep journals personal</h2><p>Accounts separate each owner’s cat profiles and observations from other users.</p></article>
        </div>
      </section>

      <section className="research-section">
        <div>
          <p className="eyebrow">The research direction</p>
          <h2>Can context and multiple signals make interpretation more useful?</h2>
        </div>
        <div>
          <p>
            This project investigates whether multimodal artificial intelligence can improve
            companion-cat behaviour interpretation and make its reasoning easier for people to
            understand.
          </p>
          <ul>
            <li>Compare text-only, context-only, and multimodal results.</li>
            <li>Measure accuracy, confidence calibration, and explanation quality.</li>
            <li>Study whether transparent uncertainty improves user trust.</li>
            <li>Explore individual baselines as observations accumulate over time.</li>
          </ul>
        </div>
      </section>

      <section className="about-cta">
        <p className="eyebrow">Start with an observation</p>
        <h2>Build a clearer picture of your cat’s everyday behaviour.</h2>
        <div className="hero-actions">
          <Link className="primary link-button" to="/signup">Create an account</Link>
          <Link className="quiet link-button" to="/">Return home</Link>
        </div>
      </section>
    </main>
  </div>;
}
