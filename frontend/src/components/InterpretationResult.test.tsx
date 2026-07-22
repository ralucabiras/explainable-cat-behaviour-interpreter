import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ModalityResult } from "../types";
import { InterpretationResult } from "./InterpretationResult";

function result(overrides: Partial<ModalityResult> = {}): ModalityResult {
  return {
    status: "completed",
    label: "stressed_or_frustrated",
    confidence: 0.74,
    detected_features: ["pacing", "recent_relocation"],
    evidence: [
      { key: "pacing", observation: "repetitive pacing", source: "text" },
      { key: "recent_relocation", observation: "recent travel or relocation", source: "context" },
    ],
    state_scores: [{ state: "stressed_or_frustrated", score: 2 }],
    alternatives: [{ state: "alert_or_curious", confidence: 0.2 }],
    explanation: "The cat may be experiencing stress.",
    recommendations: ["Provide a quiet hiding place."],
    safety_escalation: false,
    ...overrides,
  };
}

describe("InterpretationResult", () => {
  it("shows a normal interpretation, evidence, alternatives, and advice", () => {
    render(<InterpretationResult result={result()} />);
    expect(screen.getByRole("heading", { name: "Stressed or frustrated" })).toBeInTheDocument();
    expect(screen.getByText("Evidence strength: 74%")).toBeInTheDocument();
    expect(screen.getByText("repetitive pacing")).toBeInTheDocument();
    expect(screen.getByText(/Alert or curious/)).toBeInTheDocument();
    expect(screen.getByText("Provide a quiet hiding place.")).toBeInTheDocument();
  });

  it("communicates an uncertain result without inventing alternatives", () => {
    render(<InterpretationResult result={result({ label: "uncertain", alternatives: [], evidence: [] })} />);
    expect(screen.getByRole("heading", { name: "Uncertain" })).toBeInTheDocument();
    expect(screen.queryByText("Other possible interpretations")).not.toBeInTheDocument();
  });

  it("prioritises urgent guidance and suppresses routine recommendations", () => {
    render(<InterpretationResult result={result({ safety_escalation: true, label: "potentially_unwell", safety_message: "Contact an emergency veterinarian.", recommendations: [] })} />);
    expect(screen.getByText("Prompt veterinary guidance advised")).toBeInTheDocument();
    expect(screen.getByText("Contact an emergency veterinarian.")).toBeInTheDocument();
    expect(screen.queryByText("What you can try")).not.toBeInTheDocument();
  });
});
