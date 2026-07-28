import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import type { ModalityResult, Observation, Pet } from "../types";
import { ObservationDetailPage } from "./ObservationDetailPage";
import { PetDetailPage } from "./PetDetailPage";
import { PetsPage } from "./PetsPage";

vi.mock("../api", () => ({
  api: {
    getPet: vi.fn(),
    listObservations: vi.fn(),
    updatePet: vi.fn(),
    deletePet: vi.fn(),
    getObservation: vi.fn(),
    deleteObservation: vi.fn(),
    createPet: vi.fn(),
  },
}));

const result: ModalityResult = {
  status: "completed",
  label: "fearful",
  confidence: 0.72,
  detected_features: ["hiding"],
  evidence: [{ key: "hiding", observation: "hiding or withdrawal", source: "text" }],
  state_scores: [{ state: "fearful", score: 2 }],
  alternatives: [],
  explanation: "The cat may be fearful.",
  recommendations: ["Provide a quiet hiding place."],
  safety_escalation: false,
};

const pet: Pet = {
  id: "pet-1",
  name: "Miso",
  species: "cat",
  sex: "female",
  breed: "Domestic shorthair",
  date_of_birth: "2023-01-10",
  feeding_method: "scheduled_twice_daily",
  activity_level: "moderate",
  sociability_with_people: "selective",
  sociability_with_animals: "shy",
  routine_sensitivity: "moderate",
  known_triggers: ["doorbell"],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const observation: Observation = {
  id: "observation-1",
  pet_id: pet.id,
  text_description: "Miso was hiding under the bed.",
  context: {
    feeding_status: "fed",
    unfamiliar_people_present: false,
    unfamiliar_animals_present: false,
    recent_travel_or_relocation: false,
    recent_play: false,
    known_triggers: [],
  },
  created_at: "2026-01-02T12:00:00Z",
  updated_at: "2026-01-02T12:00:00Z",
  analysis: { text: result, context: result, fusion: result, video: result, audio: result },
};

describe("journal pages", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getPet).mockResolvedValue(pet);
    vi.mocked(api.listObservations).mockResolvedValue([observation]);
    vi.mocked(api.updatePet).mockResolvedValue({ ...pet, name: "Miso Moon" });
    vi.mocked(api.deletePet).mockResolvedValue({
      message: "deleted",
      deleted_observations: 1,
    });
    vi.mocked(api.getObservation).mockResolvedValue(observation);
    vi.mocked(api.deleteObservation).mockResolvedValue(undefined);
    vi.mocked(api.createPet).mockResolvedValue(pet);
  });

  it("loads a per-cat timeline and applies a state filter", async () => {
    renderPetPage();
    expect(await screen.findByRole("heading", { name: "Miso" })).toBeInTheDocument();
    expect(screen.getByText(/years.*old/)).toBeInTheDocument();
    expect(screen.getByText("Miso was hiding under the bed.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Interpretation"), {
      target: { value: "fearful" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));
    await waitFor(() => expect(api.listObservations).toHaveBeenLastCalledWith(
      expect.objectContaining({ pet_id: "pet-1", state: "fearful", limit: 10 }),
    ));
  });

  it("edits a pet profile and confirms cascade deletion", async () => {
    const onPetsChanged = vi.fn().mockResolvedValue(undefined);
    renderPetPage(onPetsChanged);
    await screen.findByRole("heading", { name: "Miso" });
    fireEvent.click(screen.getByRole("button", { name: "Edit profile" }));
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Miso Moon" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByRole("heading", { name: "Miso Moon" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    expect(screen.getByRole("dialog")).toHaveTextContent("all Miso Moon’s saved observations");
    fireEvent.click(screen.getByRole("button", { name: "Delete cat and observations" }));
    await waitFor(() => expect(api.deletePet).toHaveBeenCalledWith("pet-1"));
  });

  it("keeps the edit form open and reports update errors", async () => {
    vi.mocked(api.updatePet).mockRejectedValue(new Error("Profile update failed"));
    renderPetPage();
    await screen.findByRole("heading", { name: "Miso" });
    fireEvent.click(screen.getByRole("button", { name: "Edit profile" }));
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));
    expect(await screen.findByText("Profile update failed")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
  });

  it("renders and deletes a permanent saved interpretation", async () => {
    render(<MemoryRouter initialEntries={["/app/observations/observation-1"]}>
      <Routes>
        <Route path="/app/observations/:observationId" element={<ObservationDetailPage />} />
        <Route path="/app/pets/:petId" element={<p>Cat journal</p>} />
      </Routes>
    </MemoryRouter>);
    expect(await screen.findByText("The cat may be fearful.")).toBeInTheDocument();
    expect(screen.getByText("Miso was hiding under the bed.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Delete observation" }));
    const dialog = screen.getByRole("dialog");
    expect(dialog).toBeInTheDocument();
    fireEvent.click(within(dialog).getByRole("button", { name: "Delete observation" }));
    await waitFor(() =>
      expect(api.deleteObservation).toHaveBeenCalledWith("observation-1"),
    );
  });

  it("creates a cat and resets the form after the asynchronous request", async () => {
    const refresh = vi.fn().mockResolvedValue(undefined);
    render(<MemoryRouter><PetsPage pets={[]} refresh={refresh} /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Miso" } });
    fireEvent.click(screen.getByRole("button", { name: "Save profile" }));
    await waitFor(() => expect(api.createPet).toHaveBeenCalled());
    await waitFor(() => expect(refresh).toHaveBeenCalled());
    expect(screen.queryByText(/Cannot read properties/)).not.toBeInTheDocument();
  });

  it("submits a selected breed, multiple standard triggers, and a custom trigger", async () => {
    render(<MemoryRouter><PetsPage pets={[]} refresh={vi.fn().mockResolvedValue(undefined)} /></MemoryRouter>);
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Nova" } });
    fireEvent.change(screen.getByLabelText("Breed"), { target: { value: "Bengal" } });
    fireEvent.click(screen.getByText("Personality and known triggers"));
    fireEvent.click(screen.getByLabelText("Vacuum cleaner"));
    fireEvent.click(screen.getByLabelText("Fireworks"));
    fireEvent.click(screen.getByRole("button", { name: "+ Other trigger" }));
    fireEvent.change(screen.getByLabelText("Other trigger"), { target: { value: "Robot toy" } });
    fireEvent.click(screen.getByRole("button", { name: "Add trigger" }));
    fireEvent.click(screen.getByRole("button", { name: "Save profile" }));

    await waitFor(() => expect(api.createPet).toHaveBeenCalledWith(
      expect.objectContaining({
        breed: "Bengal",
        known_triggers: ["Vacuum cleaner", "Fireworks", "Robot toy"],
      }),
    ));
  });
});

function renderPetPage(onPetsChanged = vi.fn().mockResolvedValue(undefined)) {
  return render(<MemoryRouter initialEntries={["/app/pets/pet-1"]}>
    <Routes>
      <Route
        path="/app/pets/:petId"
        element={<PetDetailPage onPetsChanged={onPetsChanged} />}
      />
      <Route path="/app" element={<p>Dashboard</p>} />
    </Routes>
  </MemoryRouter>);
}
