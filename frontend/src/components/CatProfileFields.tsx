import { useState } from "react";
import type { Pet } from "../types";

const CAT_BREEDS = [
  "Abyssinian",
  "American Bobtail",
  "American Curl",
  "American Shorthair",
  "American Wirehair",
  "Balinese",
  "Bengal",
  "Birman",
  "Bombay",
  "British Shorthair",
  "Burmese",
  "Burmilla",
  "Chartreux",
  "Cornish Rex",
  "Cymric",
  "Devon Rex",
  "Domestic Longhair",
  "Domestic Medium Hair",
  "Domestic Shorthair",
  "Egyptian Mau",
  "European Shorthair",
  "Exotic Shorthair",
  "Havana Brown",
  "Japanese Bobtail",
  "Korat",
  "LaPerm",
  "Maine Coon",
  "Manx",
  "Mixed breed",
  "Munchkin",
  "Nebelung",
  "Norwegian Forest Cat",
  "Ocicat",
  "Oriental Longhair",
  "Oriental Shorthair",
  "Persian",
  "Peterbald",
  "Pixiebob",
  "Ragamuffin",
  "Ragdoll",
  "Russian Blue",
  "Savannah",
  "Scottish Fold",
  "Selkirk Rex",
  "Siamese",
  "Siberian",
  "Singapura",
  "Snowshoe",
  "Somali",
  "Sphynx",
  "Thai",
  "Tonkinese",
  "Toyger",
  "Turkish Angora",
  "Turkish Van",
] as const;

const STANDARD_TRIGGERS = [
  "Doorbell",
  "Visitors",
  "Being alone",
  "Carrier",
  "Vacuum cleaner",
  "Loud noises",
  "Thunderstorms",
  "Fireworks",
  "Other animals",
  "Unfamiliar cats",
  "Car travel",
  "Veterinary visits",
  "Being handled",
  "Grooming",
  "Changes in routine",
  "Moving home",
] as const;

export function CatProfileFields({ pet }: { pet?: Pet }) {
  const standardKeys = new Set(STANDARD_TRIGGERS.map((trigger) => trigger.toLocaleLowerCase()));
  const [customTriggers, setCustomTriggers] = useState(
    pet?.known_triggers.filter((trigger) => !standardKeys.has(trigger.toLocaleLowerCase())) ?? [],
  );
  const [showOther, setShowOther] = useState(false);
  const [otherTrigger, setOtherTrigger] = useState("");
  const existingBreedIsCustom = Boolean(pet?.breed && !CAT_BREEDS.includes(pet.breed as never));

  function addOtherTrigger() {
    const trigger = otherTrigger.trim();
    if (!trigger) return;
    if (![...STANDARD_TRIGGERS, ...customTriggers].some(
      (item) => item.toLocaleLowerCase() === trigger.toLocaleLowerCase(),
    )) {
      setCustomTriggers((current) => [...current, trigger]);
    }
    setOtherTrigger("");
  }

  return <>
    <details className="form-section" open>
      <summary>Basic details</summary>
      <div className="form-grid">
        <label>Name<input name="name" required maxLength={80} defaultValue={pet?.name ?? ""} /></label>
        <label>Breed
          <select name="breed" defaultValue={pet?.breed ?? ""}>
            <option value="">Unknown / not sure</option>
            {existingBreedIsCustom && <option value={pet?.breed ?? ""}>{pet?.breed}</option>}
            {CAT_BREEDS.map((breed) => <option key={breed} value={breed}>{breed}</option>)}
          </select>
        </label>
        <label>Sex<select name="sex" defaultValue={pet?.sex ?? "unknown"}><option value="unknown">Unknown</option><option value="female">Female</option><option value="male">Male</option></select></label>
        <label>Date of birth<input name="date_of_birth" type="date" max={new Date().toISOString().slice(0, 10)} defaultValue={pet?.date_of_birth ?? ""} /></label>
      </div>
    </details>
    <details className="form-section">
      <summary>Feeding and daily routine</summary>
      <div className="form-grid">
        <label>Feeding method<select name="feeding_method" defaultValue={pet?.feeding_method ?? "unknown"}><option value="unknown">Not specified</option><option value="free_fed">Free-fed</option><option value="scheduled_once_daily">Scheduled once daily</option><option value="scheduled_twice_daily">Scheduled twice daily</option><option value="scheduled_three_plus">Scheduled 3+ times daily</option><option value="mixed">Mixed</option><option value="other">Other</option></select></label>
        <label>Feeding details<input name="feeding_notes" defaultValue={pet?.feeding_notes ?? ""} placeholder="Food type, times, special habits" /></label>
        <label>Activity level<select name="activity_level" defaultValue={pet?.activity_level ?? "unknown"}><option value="unknown">Not specified</option><option value="low">Low</option><option value="moderate">Moderate</option><option value="high">High</option></select></label>
        <label>Routine sensitivity<select name="routine_sensitivity" defaultValue={pet?.routine_sensitivity ?? "unknown"}><option value="unknown">Not specified</option><option value="low">Low</option><option value="moderate">Moderate</option><option value="high">High</option></select></label>
      </div>
    </details>
    <details className="form-section">
      <summary>Personality and known triggers</summary>
      <div className="form-grid">
        <label>With people<select name="sociability_with_people" defaultValue={pet?.sociability_with_people ?? "unknown"}><option value="unknown">Not specified</option><option value="social">Social</option><option value="selective">Selective</option><option value="shy">Shy</option></select></label>
        <label>With other animals<select name="sociability_with_animals" defaultValue={pet?.sociability_with_animals ?? "unknown"}><option value="unknown">Not specified</option><option value="social">Social</option><option value="selective">Selective</option><option value="shy">Shy</option></select></label>
        <fieldset className="wide trigger-fieldset">
          <legend>Known triggers <small>Select all that apply</small></legend>
          <div className="trigger-options">
            {STANDARD_TRIGGERS.map((trigger) => <label className="trigger-option" key={trigger}>
              <input
                type="checkbox"
                name="known_triggers"
                value={trigger}
                defaultChecked={pet?.known_triggers.some(
                  (saved) => saved.toLocaleLowerCase() === trigger.toLocaleLowerCase(),
                )}
              />
              <span>{trigger}</span>
            </label>)}
          </div>
          <div className="custom-triggers">
            {customTriggers.map((trigger) => <span className="trigger-chip" key={trigger}>
              {trigger}
              <input type="hidden" name="known_triggers" value={trigger} />
              <button type="button" aria-label={`Remove ${trigger}`} onClick={() =>
                setCustomTriggers((current) => current.filter((item) => item !== trigger))
              }>×</button>
            </span>)}
          </div>
          {!showOther
            ? <button type="button" className="quiet other-trigger-button" onClick={() => setShowOther(true)}>+ Other trigger</button>
            : <div className="other-trigger-entry">
              <label>Other trigger<input value={otherTrigger} maxLength={100} onChange={(event) => setOtherTrigger(event.target.value)} onKeyDown={(event) => {
                if (event.key === "Enter") { event.preventDefault(); addOtherTrigger(); }
              }} placeholder="Type another trigger" /></label>
              <button type="button" className="quiet" onClick={addOtherTrigger}>Add trigger</button>
            </div>}
        </fieldset>
        <label className="wide">Personality notes<textarea name="personality_notes" rows={3} maxLength={1500} defaultValue={pet?.personality_notes ?? ""} placeholder="Typical temperament, favourite activities, normal hiding or vocalisation habits…" /></label>
        <label className="wide">Other care notes<textarea name="notes" rows={3} maxLength={1000} defaultValue={pet?.notes ?? ""} /></label>
      </div>
    </details>
  </>;
}
