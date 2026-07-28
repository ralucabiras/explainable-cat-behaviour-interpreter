import { FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { CatProfileFields } from "../components/CatProfileFields";
import { ObservationCard } from "../components/ObservationCard";
import { BEHAVIOUR_OPTIONS } from "../lib/behaviour";
import { formatCatAge } from "../lib/cat";
import type {
  ActivityLevel,
  BehaviourState,
  FeedingMethod,
  Observation,
  Pet,
  RoutineSensitivity,
  Sex,
  Sociability,
} from "../types";

const PAGE_SIZE = 10;

export function PetDetailPage({ onPetsChanged }: { onPetsChanged: () => Promise<void> }) {
  const { petId = "" } = useParams();
  const navigate = useNavigate();
  const [pet, setPet] = useState<Pet | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [filters, setFilters] = useState<{ state?: BehaviourState; date_from?: string; date_to?: string }>({});

  useEffect(() => {
    void Promise.all([
      api.getPet(petId),
      api.listObservations({ pet_id: petId, limit: PAGE_SIZE }),
    ]).then(([profile, entries]) => {
      setPet(profile); setObservations(entries); setHasMore(entries.length === PAGE_SIZE);
    }).catch((reason) => setError(reason instanceof Error ? reason.message : "Could not load this journal."));
  }, [petId]);

  async function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError("");
    const form = new FormData(event.currentTarget);
    const next = {
      state: String(form.get("state")) as BehaviourState || undefined,
      date_from: form.get("date_from") ? new Date(`${form.get("date_from")}T00:00:00`).toISOString() : undefined,
      date_to: form.get("date_to") ? new Date(`${form.get("date_to")}T23:59:59`).toISOString() : undefined,
    };
    try {
      const entries = await api.listObservations({ pet_id: petId, ...next, limit: PAGE_SIZE });
      setFilters(next); setObservations(entries); setHasMore(entries.length === PAGE_SIZE);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not filter observations."); }
  }

  async function loadMore() {
    try {
      const entries = await api.listObservations({ pet_id: petId, ...filters, skip: observations.length, limit: PAGE_SIZE });
      setObservations((current) => [...current, ...entries]);
      setHasMore(entries.length === PAGE_SIZE);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load more observations."); }
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); const form = new FormData(event.currentTarget);
    try {
      const updated = await api.updatePet(petId, {
        name: String(form.get("name")),
        breed: String(form.get("breed")) || null,
        sex: String(form.get("sex")) as Sex,
        date_of_birth: String(form.get("date_of_birth")) || null,
        notes: String(form.get("notes")) || null,
        feeding_method: String(form.get("feeding_method")) as FeedingMethod,
        feeding_notes: String(form.get("feeding_notes")) || null,
        activity_level: String(form.get("activity_level")) as ActivityLevel,
        sociability_with_people: String(form.get("sociability_with_people")) as Sociability,
        sociability_with_animals: String(form.get("sociability_with_animals")) as Sociability,
        routine_sensitivity: String(form.get("routine_sensitivity")) as RoutineSensitivity,
        known_triggers: form.getAll("known_triggers").map(String),
        personality_notes: String(form.get("personality_notes")) || null,
      });
      setPet(updated); setEditing(false); await onPetsChanged();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not update the profile."); }
  }

  async function deletePet() {
    setBusy(true); setError("");
    try { await api.deletePet(petId); await onPetsChanged(); navigate("/app"); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete the profile."); setBusy(false); setConfirmDelete(false); }
  }

  if (!pet && !error) return <div className="app-loading inline-loading">Opening journal…</div>;
  if (!pet) return <div className="notice error">{error}</div>;
  const age = formatCatAge(pet.date_of_birth);

  return <section>
    <Link className="back-link" to="/app">← All cats</Link>
    <div className="pet-detail-heading">
      <div className="profile-avatar">{pet.name.charAt(0).toUpperCase()}</div>
      <div><p className="eyebrow">Cat profile</p><h1>{pet.name}</h1><p>{pet.breed || "Cat"} · {pet.sex}{pet.date_of_birth ? ` · born ${new Date(`${pet.date_of_birth}T00:00:00`).toLocaleDateString()}` : ""}</p>{age && <span className="age-badge">{age}</span>}</div>
      <div className="detail-actions"><button className="quiet" onClick={() => setEditing(!editing)}>Edit profile</button><button className="danger-link" onClick={() => setConfirmDelete(true)}>Delete</button></div>
    </div>
    {!editing && <div className="profile-context-grid">
      <div><span>Feeding</span><strong>{pet.feeding_method.replaceAll("_", " ")}</strong>{pet.feeding_notes && <small>{pet.feeding_notes}</small>}</div>
      <div><span>Activity</span><strong>{pet.activity_level}</strong></div>
      <div><span>With people</span><strong>{pet.sociability_with_people}</strong></div>
      <div><span>With animals</span><strong>{pet.sociability_with_animals}</strong></div>
      <div><span>Routine sensitivity</span><strong>{pet.routine_sensitivity}</strong></div>
      <div><span>Known triggers</span><strong>{pet.known_triggers.length ? pet.known_triggers.join(", ") : "None recorded"}</strong></div>
    </div>}
    {pet.personality_notes && !editing && <p className="pet-notes"><strong>Personality:</strong> {pet.personality_notes}</p>}
    {pet.notes && !editing && <p className="pet-notes">{pet.notes}</p>}
    {editing && <form className="card cat-profile-form edit-profile-form" onSubmit={saveProfile}>
      <CatProfileFields pet={pet} />
      <div className="actions"><button type="button" className="quiet" onClick={() => setEditing(false)}>Cancel</button><button className="primary">Save changes</button></div>
    </form>}
    {error && <p className="error">{error}</p>}
    <section className="journal-section">
      <div className="section-heading"><div><p className="eyebrow">Behaviour journal</p><h2>Observation timeline</h2></div><Link className="primary link-button" to={`/app/observe?petId=${pet.id}`}>+ New observation</Link></div>
      <form className="history-filters" onSubmit={applyFilters}>
        <label>Interpretation<select name="state" defaultValue=""><option value="">All states</option>{BEHAVIOUR_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label>From<input name="date_from" type="date" /></label><label>To<input name="date_to" type="date" /></label>
        <button className="quiet">Apply filters</button>
      </form>
      {observations.length > 0 ? <div className="timeline-list">{observations.map((item) => <ObservationCard key={item.id} observation={item} />)}</div> : <div className="empty-journal"><p>No observations match this view.</p></div>}
      {hasMore && <button className="quiet load-more" onClick={() => void loadMore()}>Load more</button>}
    </section>
    {confirmDelete && <ConfirmDialog title={`Delete ${pet.name}’s profile?`} confirmLabel="Delete cat and observations" busy={busy} onCancel={() => setConfirmDelete(false)} onConfirm={() => void deletePet()}><p>This permanently deletes the profile and all {pet.name}’s saved observations. This cannot be undone.</p></ConfirmDialog>}
  </section>;
}
