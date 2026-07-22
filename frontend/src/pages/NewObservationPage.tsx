import { FormEvent, useState } from "react";
import { api } from "../api";
import type { Pet } from "../types";

export function NewObservationPage({ pets }: { pets: Pet[] }) {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage(""); setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api.createObservation({
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
          known_triggers: String(form.get("known_triggers")).split(",").map((v) => v.trim()).filter(Boolean),
        },
      });
      event.currentTarget.reset();
      setMessage("Observation saved. Text and context analysis will be added in the next stage.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save the observation."); }
  }

  if (pets.length === 0) return <section><h1>New observation</h1><div className="notice">Create a cat profile before recording an observation.</div></section>;

  return (
    <section className="observation-page">
      <div className="page-heading"><div><p className="eyebrow">Behaviour journal</p><h1>Record an observation</h1><p>Describe what you saw, then add the circumstances around it.</p></div></div>
      <form onSubmit={submit}>
        <fieldset className="card"><legend>1. What happened?</legend>
          <label>Cat<select name="pet_id" required>{pets.map((pet) => <option key={pet.id} value={pet.id}>{pet.name}</option>)}</select></label>
          <label>Description<textarea name="description" required minLength={1} maxLength={5000} rows={6} placeholder="For example: Luna paced by the door and meowed repeatedly after we arrived at the new apartment…" /></label>
        </fieldset>
        <fieldset className="card"><legend>2. Context</legend><div className="form-grid">
          <label>Location<input name="location" placeholder="Living room" /></label><label>Time of day<input name="time_of_day" placeholder="Early evening" /></label>
          <label>Feeding<select name="feeding_status" defaultValue="unknown"><option value="unknown">Unknown</option><option value="fed">Recently fed</option><option value="due_soon">Due soon</option><option value="overdue">Overdue</option></select></label>
          <label>Known triggers<input name="known_triggers" placeholder="Doorbell, carrier (comma separated)" /></label>
          <label className="wide">Routine changes<textarea name="routine_changes" rows={2} /></label>
        </div><div className="checks"><label><input type="checkbox" name="unfamiliar_people" /> Unfamiliar people present</label><label><input type="checkbox" name="unfamiliar_animals" /> Unfamiliar animals present</label><label><input type="checkbox" name="recent_travel" /> Recent travel or relocation</label><label><input type="checkbox" name="recent_play" /> Recent play</label></div></fieldset>
        <fieldset className="card disabled"><legend>3. Media (coming later)</legend><p>Video will be added after text and context are stable. Audio follows once the rest of the pipeline is reliable.</p></fieldset>
        {message && <p className="success">{message}</p>}{error && <p className="error">{error}</p>}<button className="primary submit">Save observation</button>
      </form>
    </section>
  );
}

