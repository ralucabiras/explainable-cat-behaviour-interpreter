import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { ObservationCard } from "../components/ObservationCard";
import type { Observation, Pet, Sex } from "../types";

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
    {open && <form className="card form-grid" onSubmit={submit}>
      <label>Name<input name="name" required maxLength={80} /></label>
      <label>Breed<input name="breed" maxLength={100} /></label>
      <label>Sex<select name="sex" defaultValue="unknown"><option value="unknown">Unknown</option><option value="female">Female</option><option value="male">Male</option></select></label>
      <label>Date of birth<input name="date_of_birth" type="date" /></label>
      <label className="wide">Notes<textarea name="notes" rows={3} maxLength={1000} /></label>
      {error && <p className="error wide">{error}</p>}
      <div className="actions wide"><button type="button" className="quiet" onClick={() => setOpen(false)}>Cancel</button><button className="primary">Save profile</button></div>
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
