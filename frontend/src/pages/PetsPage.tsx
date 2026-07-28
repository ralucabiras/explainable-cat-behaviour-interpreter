import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { CatProfileFields } from "../components/CatProfileFields";
import { ObservationCard } from "../components/ObservationCard";
import type {
  ActivityLevel,
  FeedingMethod,
  Observation,
  Pet,
  RoutineSensitivity,
  Sex,
  Sociability,
} from "../types";

export function PetsPage({ pets, refresh }: { pets: Pet[]; refresh: () => Promise<void> }) {
  const [open, setOpen] = useState(pets.length === 0);
  const [error, setError] = useState("");
  const [recent, setRecent] = useState<Observation[]>([]);

  useEffect(() => {
    void api.listObservations({ limit: 5 }).then(setRecent).catch(() => setRecent([]));
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      await api.createPet({
        name: String(form.get("name")),
        breed: String(form.get("breed")) || undefined,
        sex: String(form.get("sex")) as Sex,
        date_of_birth: String(form.get("date_of_birth")) || undefined,
        notes: String(form.get("notes")) || undefined,
        feeding_method: String(form.get("feeding_method")) as FeedingMethod,
        feeding_notes: String(form.get("feeding_notes")) || undefined,
        activity_level: String(form.get("activity_level")) as ActivityLevel,
        sociability_with_people: String(form.get("sociability_with_people")) as Sociability,
        sociability_with_animals: String(form.get("sociability_with_animals")) as Sociability,
        routine_sensitivity: String(form.get("routine_sensitivity")) as RoutineSensitivity,
        known_triggers: form.getAll("known_triggers").map(String),
        personality_notes: String(form.get("personality_notes")) || undefined,
      });
      formElement.reset();
      setOpen(false);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save the profile.");
    }
  }

  return <section>
    <div className="page-heading">
      <div><p className="eyebrow">Your companions</p><h1>Cat profiles</h1><p>Profiles provide the individual context behind each observation.</p></div>
      <button className="primary" onClick={() => setOpen(!open)}>+ Add a cat</button>
    </div>
    {open && <form className="card cat-profile-form" onSubmit={submit}>
      <CatProfileFields />
      {error && <p className="error">{error}</p>}
      <div className="actions"><button type="button" className="quiet" onClick={() => setOpen(false)}>Cancel</button><button className="primary">Save profile</button></div>
    </form>}
    <div className="pet-grid">
      {pets.map((pet) => <Link className="card pet-card pet-card-link" to={`/app/pets/${pet.id}`} key={pet.id}>
        <div className="avatar" aria-hidden="true">{pet.name[0].toUpperCase()}</div>
        <div><h2>{pet.name}</h2><p>{pet.breed || "Cat"} · {pet.sex}</p>{pet.notes && <small>{pet.notes}</small>}</div>
      </Link>)}
      {!open && pets.length === 0 && <p>No profiles yet. Add your cat to begin.</p>}
    </div>
    <section className="recent-section">
      <div className="section-heading"><div><p className="eyebrow">Across all cats</p><h2>Recent observations</h2></div></div>
      {recent.length > 0
        ? <div className="timeline-list">{recent.map((item) => <ObservationCard key={item.id} observation={item} pet={pets.find((pet) => pet.id === item.pet_id)} />)}</div>
        : <div className="empty-journal"><p>No saved observations yet.</p><Link to="/app/observe">Record the first observation</Link></div>}
    </section>
  </section>;
}
