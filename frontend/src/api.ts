import type { Observation, ObservationContext, Pet, Sex } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "The request could not be completed.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  listPets: () => request<Pet[]>("/pets"),
  createPet: (payload: { name: string; breed?: string; sex: Sex; notes?: string }) =>
    request<Pet>("/pets", {
      method: "POST",
      body: JSON.stringify({ ...payload, species: "cat" }),
    }),
  createObservation: (payload: {
    pet_id: string;
    text_description: string;
    context: ObservationContext;
  }) => request<Observation>("/observations", { method: "POST", body: JSON.stringify(payload) }),
};

