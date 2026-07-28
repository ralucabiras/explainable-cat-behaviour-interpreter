import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { InterpretationResult } from "../components/InterpretationResult";
import { VideoEvidence } from "../components/VideoEvidence";
import type { Observation, Pet } from "../types";

export function ObservationDetailPage() {
  const { observationId = "" } = useParams();
  const navigate = useNavigate();
  const [observation, setObservation] = useState<Observation | null>(null);
  const [pet, setPet] = useState<Pet | null>(null);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void api.getObservation(observationId).then(async (entry) => {
      setObservation(entry);
      try { setPet(await api.getPet(entry.pet_id)); } catch { setPet(null); }
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load this observation."));
  }, [observationId]);

  async function remove() {
    if (!observation) return;
    setBusy(true);
    try { await api.deleteObservation(observation.id); navigate(`/app/pets/${observation.pet_id}`); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete this observation."); setBusy(false); setConfirmDelete(false); }
  }

  if (!observation && !error) return <div className="app-loading inline-loading">Opening observation…</div>;
  if (!observation) return <div className="notice error">{error}</div>;
  const contextItems = [
    observation.context.location && `Location: ${observation.context.location}`,
    observation.context.time_of_day && `Time: ${observation.context.time_of_day}`,
    observation.context.feeding_status !== "unknown" && `Feeding: ${observation.context.feeding_status.replace("_", " ")}`,
    observation.context.recent_travel_or_relocation && "Recent travel or relocation",
    observation.context.recent_play && "Recent play",
    observation.context.routine_changes && `Routine changes: ${observation.context.routine_changes}`,
  ].filter(Boolean) as string[];

  return <section>
    <Link className="back-link" to={`/app/pets/${observation.pet_id}`}>← {pet ? `${pet.name}’s journal` : "Cat journal"}</Link>
    <div className="observation-detail-heading"><div><p className="eyebrow">Saved observation</p><h1>{pet ? `${pet.name}’s entry` : "Journal entry"}</h1><time>{new Intl.DateTimeFormat(undefined, { dateStyle: "long", timeStyle: "short" }).format(new Date(observation.created_at))}</time></div><button className="danger-link" onClick={() => setConfirmDelete(true)}>Delete observation</button></div>
    {error && <p className="error">{error}</p>}
    <article className="card original-observation"><h2>What was observed</h2><p>{observation.text_description}</p>{contextItems.length > 0 && <><h3>Context</h3><ul>{contextItems.map((item) => <li key={item}>{item}</li>)}</ul></>}</article>
    <InterpretationResult result={observation.analysis.fusion} />
    <VideoEvidence observation={observation} />
    {confirmDelete && <ConfirmDialog title="Delete this observation?" confirmLabel="Delete observation" busy={busy} onCancel={() => setConfirmDelete(false)} onConfirm={() => void remove()}><p>This permanently removes the journal entry and its saved interpretation. It cannot be undone.</p></ConfirmDialog>}
  </section>;
}
