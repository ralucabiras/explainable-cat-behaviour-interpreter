import { FormEvent, useState } from "react";
import { api } from "../api";
import type { Pet, Sex } from "../types";

export function PetsPage({ pets, refresh }: { pets: Pet[]; refresh: () => Promise<void> }) {
  const [open, setOpen] = useState(pets.length === 0);
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    try {
      await api.createPet({
        name: String(form.get("name")),
        breed: String(form.get("breed")) || undefined,
        sex: String(form.get("sex")) as Sex,
        notes: String(form.get("notes")) || undefined,
      });
      event.currentTarget.reset();
      setOpen(false);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save the profile.");
    }
  }

  return (
    <section>
      <div className="page-heading">
        <div>
          <p className="eyebrow">Your companions</p>
          <h1>Cat profiles</h1>
          <p>Profiles provide the individual context behind each observation.</p>
        </div>
        <button className="primary" onClick={() => setOpen(!open)}>+ Add a cat</button>
      </div>

      {open && (
        <form className="card form-grid" onSubmit={submit}>
          <label>Name<input name="name" required maxLength={80} /></label>
          <label>Breed<input name="breed" maxLength={100} /></label>
          <label>Sex<select name="sex" defaultValue="unknown"><option value="unknown">Unknown</option><option value="female">Female</option><option value="male">Male</option></select></label>
          <label className="wide">Notes<textarea name="notes" rows={3} maxLength={1000} /></label>
          {error && <p className="error wide">{error}</p>}
          <div className="actions wide"><button type="button" className="quiet" onClick={() => setOpen(false)}>Cancel</button><button className="primary">Save profile</button></div>
        </form>
      )}

      <div className="pet-grid">
        {pets.map((pet) => (
          <article className="card pet-card" key={pet.id}>
            <div className="avatar" aria-hidden="true">{pet.name[0].toUpperCase()}</div>
            <div><h2>{pet.name}</h2><p>{pet.breed || "Cat"} · {pet.sex}</p>{pet.notes && <small>{pet.notes}</small>}</div>
          </article>
        ))}
        {!open && pets.length === 0 && <p>No profiles yet. Add your cat to begin.</p>}
      </div>
    </section>
  );
}

