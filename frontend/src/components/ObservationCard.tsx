import { Link } from "react-router-dom";
import { BEHAVIOUR_LABELS } from "../lib/behaviour";
import type { Observation, Pet } from "../types";

export function ObservationCard({
  observation,
  pet,
}: {
  observation: Observation;
  pet?: Pet;
}) {
  const result = observation.analysis.fusion;
  const label = result.label ? BEHAVIOUR_LABELS[result.label] : "Pending interpretation";
  return <Link className={`timeline-card${result.safety_escalation ? " urgent" : ""}`} to={`/app/observations/${observation.id}`}>
    <div className="timeline-meta">
      <time dateTime={observation.created_at}>
        {new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(observation.created_at))}
      </time>
      {pet && <span>{pet.name}</span>}
    </div>
    <div className="timeline-main">
      <div><h3>{result.safety_escalation ? "Veterinary guidance advised" : label}</h3><p>{observation.text_description}</p></div>
      {result.confidence !== undefined && <span className="confidence">{Math.round(result.confidence * 100)}%</span>}
    </div>
  </Link>;
}
