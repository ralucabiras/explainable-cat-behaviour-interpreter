import type { BehaviourState, ModalityResult } from "../types";

const LABELS: Record<BehaviourState, string> = {
  relaxed: "Relaxed", playful: "Playful", alert_or_curious: "Alert or curious",
  attention_seeking: "Attention-seeking", fearful: "Fearful",
  stressed_or_frustrated: "Stressed or frustrated",
  defensive_or_aggressive: "Defensive or aggressive",
  potentially_unwell: "Potentially unwell", uncertain: "Uncertain",
};

export function InterpretationResult({ result }: { result: ModalityResult }) {
  const textEvidence = result.evidence.filter((item) => item.source === "text");
  const contextEvidence = result.evidence.filter((item) => item.source === "context");

  if (result.safety_escalation) {
    return <section className="result-card urgent-result" aria-live="polite">
      <p className="eyebrow">Prompt veterinary guidance advised</p>
      <h2>{result.label ? LABELS[result.label] : "Potentially urgent sign"}</h2>
      <p>{result.explanation}</p><p className="safety-message">{result.safety_message}</p><Disclaimer />
    </section>;
  }

  return <section className="result-card" aria-live="polite">
    <p className="eyebrow">Possible interpretation</p>
    <div className="result-heading"><h2>{result.label ? LABELS[result.label] : "Analysis unavailable"}</h2><span className="confidence">Evidence strength: {Math.round((result.confidence ?? 0) * 100)}%</span></div>
    <p className="result-explanation">{result.explanation}</p>
    {(textEvidence.length > 0 || contextEvidence.length > 0) && <div className="evidence-grid"><EvidenceGroup title="From your description" items={textEvidence.map((item) => item.observation)} /><EvidenceGroup title="From the context" items={contextEvidence.map((item) => item.observation)} /></div>}
    {result.alternatives.length > 0 && <div className="result-section"><h3>Other possible interpretations</h3><ul>{result.alternatives.map((item) => <li key={item.state}>{LABELS[item.state]} ({Math.round(item.confidence * 100)}% relative support)</li>)}</ul></div>}
    {result.recommendations.length > 0 && <div className="result-section recommendation"><h3>What you can try</h3><ul>{result.recommendations.map((item) => <li key={item}>{item}</li>)}</ul></div>}
    <Disclaimer />
  </section>;
}

function EvidenceGroup({ title, items }: { title: string; items: string[] }) {
  if (items.length === 0) return null;
  return <div><h3>{title}</h3><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}

function Disclaimer() {
  return <p className="result-disclaimer">This is a possible behavioural interpretation, not a veterinary diagnosis. Animal behaviour can have several explanations.</p>;
}
