export type Sex = "female" | "male" | "unknown";
export type FeedingMethod = "free_fed" | "scheduled_once_daily" | "scheduled_twice_daily" | "scheduled_three_plus" | "mixed" | "other" | "unknown";
export type ActivityLevel = "low" | "moderate" | "high" | "unknown";
export type Sociability = "social" | "selective" | "shy" | "unknown";
export type RoutineSensitivity = "low" | "moderate" | "high" | "unknown";

export interface User {
  id: string;
  display_name: string;
  email: string;
  email_verified: boolean;
  created_at: string;
}

export interface Pet {
  id: string;
  name: string;
  species: "cat";
  breed?: string | null;
  sex: Sex;
  date_of_birth?: string | null;
  notes?: string | null;
  feeding_method: FeedingMethod;
  feeding_notes?: string | null;
  activity_level: ActivityLevel;
  sociability_with_people: Sociability;
  sociability_with_animals: Sociability;
  routine_sensitivity: RoutineSensitivity;
  known_triggers: string[];
  personality_notes?: string | null;
  created_at: string;
  updated_at: string;
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
  updated_at: string;
  analysis: AnalysisBundle;
}

export type BehaviourState = "relaxed" | "playful" | "alert_or_curious" | "attention_seeking" | "fearful" | "stressed_or_frustrated" | "defensive_or_aggressive" | "potentially_unwell" | "uncertain";

export interface EvidenceItem { key: string; observation: string; source: "text" | "context"; }

export interface ModalityResult {
  status: "pending" | "completed" | "failed";
  label?: BehaviourState;
  confidence?: number;
  detected_features: string[];
  evidence: EvidenceItem[];
  state_scores: { state: BehaviourState; score: number }[];
  alternatives: { state: BehaviourState; confidence: number }[];
  explanation?: string;
  recommendations: string[];
  safety_escalation: boolean;
  safety_message?: string;
}

export interface AnalysisBundle {
  text: ModalityResult;
  context: ModalityResult;
  video: ModalityResult;
  audio: ModalityResult;
  fusion: ModalityResult;
}

export interface ObservationFilters {
  pet_id?: string;
  state?: BehaviourState;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}
