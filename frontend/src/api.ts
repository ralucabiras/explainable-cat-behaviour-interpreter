import type { Observation, ObservationContext, Pet, Sex, User } from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("whiskerwise_token");
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "The request could not be completed.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  signUp: (payload: { display_name: string; email: string; password: string }) =>
    request<{ message: string; email: string; development_confirmation_url?: string }>(
      "/auth/signup",
      { method: "POST", body: JSON.stringify(payload) },
    ),
  confirmEmail: (token: string) =>
    request<{ message: string }>(`/auth/confirm-email?token=${encodeURIComponent(token)}`),
  resendConfirmation: (email: string) =>
    request<{ message: string }>("/auth/resend-confirmation", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>("/auth/me"),
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
