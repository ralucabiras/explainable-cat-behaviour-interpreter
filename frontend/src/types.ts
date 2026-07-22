export type Sex = "female" | "male" | "unknown";

export interface Pet {
  id: string;
  name: string;
  species: "cat";
  breed?: string;
  sex: Sex;
  date_of_birth?: string;
  notes?: string;
}

export interface ObservationContext {
  location?: string;
  time_of_day?: string;
  feeding_status: "fed" | "due_soon" | "overdue" | "unknown";
  unfamiliar_people_present: boolean;
  unfamiliar_animals_present: boolean;
  recent_travel_or_relocation: boolean;
  recent_play: boolean;
  routine_changes?: string;
  known_triggers: string[];
}

export interface Observation {
  id: string;
  pet_id: string;
  text_description: string;
  context: ObservationContext;
  created_at: string;
}

