import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { InterpretationResult } from "../components/InterpretationResult";
import { VideoEvidence } from "../components/VideoEvidence";
import type { Observation, Pet } from "../types";

export function NewObservationPage({ pets }: { pets: Pet[] }) {
  const [searchParams] = useSearchParams();
  const requestedPetId = searchParams.get("petId");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<Observation | null>(null);
  const [video, setVideo] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(""); setError(""); setResult(null);
    const form = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const payload = {
        pet_id: String(form.get("pet_id")),
        text_description: String(form.get("description")),
        context: {
          location: String(form.get("location")) || undefined,
          time_of_day: String(form.get("time_of_day")) || undefined,
          feeding_status: String(form.get("feeding_status")) as "fed" | "due_soon" | "overdue" | "unknown",
          unfamiliar_people_present: form.has("unfamiliar_people"),
          unfamiliar_animals_present: form.has("unfamiliar_animals"),
          recent_travel_or_relocation: form.has("recent_travel"),
          recent_play: form.has("recent_play"),
          routine_changes: String(form.get("routine_changes")) || undefined,
          known_triggers: [],
        },
      };
      const saved = video
        ? await api.createObservationWithVideo(payload, video, consent, setProgress)
        : await api.createObservation(payload);
      setResult(saved);
      setMessage("Observation saved and interpreted.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the observation."); }
    finally { setBusy(false); }
  }

  if (pets.length === 0) return <section><h1>New observation</h1><div className="notice">Create a cat profile before recording an observation.</div></section>;

  return (
    <section className="observation-page">
      <div className="page-heading"><div><p className="eyebrow">Behaviour journal</p><h1>Record an observation</h1><p>Describe what you saw, then add the circumstances around it.</p></div></div>
      <form onSubmit={submit}>
        <fieldset className="card"><legend>1. What happened?</legend>
          <label>Cat<select name="pet_id" required defaultValue={pets.some((pet) => pet.id === requestedPetId) ? requestedPetId ?? undefined : undefined}>{pets.map((pet) => <option key={pet.id} value={pet.id}>{pet.name}</option>)}</select></label>
          <label>Description<textarea name="description" required minLength={1} maxLength={5000} rows={6} placeholder="For example: Luna paced by the door and meowed repeatedly after we arrived at the new apartment…" /></label>
        </fieldset>
        <fieldset className="card"><legend>2. Context</legend><div className="form-grid">
          <label>Location<input name="location" placeholder="Living room" /></label><label>Time of day<input name="time_of_day" placeholder="Early evening" /></label>
          <label>Feeding<select name="feeding_status" defaultValue="unknown"><option value="unknown">Unknown</option><option value="fed">Recently fed</option><option value="due_soon">Due soon</option><option value="overdue">Overdue</option></select></label>
          <label className="wide">Routine changes<textarea name="routine_changes" rows={2} /></label>
        </div><div className="checks"><label><input type="checkbox" name="unfamiliar_people" /> Unfamiliar people present</label><label><input type="checkbox" name="unfamiliar_animals" /> Unfamiliar animals present</label><label><input type="checkbox" name="recent_travel" /> Recent travel or relocation</label><label><input type="checkbox" name="recent_play" /> Recent play</label></div></fieldset>
        <fieldset className="card media-upload"><legend>3. Optional video</legend>
          <p>Add a short clip for private, explainable motion analysis. Video evidence does not yet change the final interpretation.</p>
          {!video ? <label className="video-picker">Choose video
            <input type="file" accept="video/mp4,video/webm,video/quicktime" onChange={(event) => {
              const selected = event.target.files?.[0];
              setError("");
              if (!selected) return;
              if (selected.size > 50 * 1024 * 1024) { setError("Video must be 50 MB or smaller."); event.target.value = ""; return; }
              setVideo(selected); setConsent(false); setProgress(0);
            }} />
            <small>MP4, WebM, or MOV · maximum 50 MB and 30 seconds</small>
          </label> : <div className="selected-video">
            <div><strong>{video.name}</strong><small>{(video.size / 1024 / 1024).toFixed(1)} MB</small></div>
            <button type="button" className="quiet" onClick={() => { setVideo(null); setConsent(false); setProgress(0); }}>Remove</button>
          </div>}
          {video && <label className="media-consent"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} required /> I confirm I have permission to upload this video, including from any identifiable people shown.</label>}
          {progress > 0 && progress < 100 && <div className="upload-progress" aria-live="polite"><progress value={progress} max={100} /> Uploading {progress}%</div>}
          {busy && video && progress >= 100 && <p className="notice" aria-live="polite">Upload complete. Extracting motion evidence…</p>}
        </fieldset>
        {message && <p className="success">{message}</p>}{error && <p className="error">{error}</p>}<button className="primary submit" disabled={busy || Boolean(video && !consent)}>{busy ? "Interpreting…" : "Save and interpret"}</button>
      </form>
      {result && <InterpretationResult result={result.analysis.fusion} />}
      {result && <VideoEvidence observation={result} />}
      {result && <div className="saved-result-link"><Link to={`/app/observations/${result.id}`}>Open the permanent journal entry →</Link></div>}
    </section>
  );
}
