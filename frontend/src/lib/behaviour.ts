import type { BehaviourState } from "../types";

export const BEHAVIOUR_LABELS: Record<BehaviourState, string> = {
  relaxed: "Relaxed",
  playful: "Playful",
  alert_or_curious: "Alert or curious",
  attention_seeking: "Attention-seeking",
  fearful: "Fearful",
  stressed_or_frustrated: "Stressed or frustrated",
  defensive_or_aggressive: "Defensive or aggressive",
  potentially_unwell: "Potentially unwell",
  uncertain: "Uncertain",
};

export const BEHAVIOUR_OPTIONS = Object.entries(BEHAVIOUR_LABELS) as [
  BehaviourState,
  string,
][];
