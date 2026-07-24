import type { Pet } from "../types";

export function CatProfileFields({ pet }: { pet?: Pet }) {
  return <>
    <details className="form-section" open>
      <summary>Basic details</summary>
      <div className="form-grid">
        <label>Name<input name="name" required maxLength={80} defaultValue={pet?.name ?? ""} /></label>
        <label>Breed<input name="breed" maxLength={100} defaultValue={pet?.breed ?? ""} /></label>
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
        <label className="wide">Known triggers<input name="known_triggers" list="common-trigger-options" defaultValue={pet?.known_triggers.join(", ") ?? ""} placeholder="Choose or type triggers, separated by commas" /><datalist id="common-trigger-options"><option value="Doorbell" /><option value="Visitors" /><option value="Carrier" /><option value="Vacuum cleaner" /><option value="Loud noises" /><option value="Other animals" /><option value="Car travel" /><option value="Veterinary visits" /></datalist></label>
        <label className="wide">Personality notes<textarea name="personality_notes" rows={3} maxLength={1500} defaultValue={pet?.personality_notes ?? ""} placeholder="Typical temperament, favourite activities, normal hiding or vocalisation habits…" /></label>
        <label className="wide">Other care notes<textarea name="notes" rows={3} maxLength={1000} defaultValue={pet?.notes ?? ""} /></label>
      </div>
    </details>
  </>;
}
