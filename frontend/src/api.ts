import type {
  Observation,
  ObservationContext,
  ObservationFilters,
  Pet,
  FeedingMethod,
  ActivityLevel,
  RoutineSensitivity,
  Sociability,
  Sex,
  User,
} from "./types";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = localStorage.getItem("whiskerwise_token");
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(!(options?.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  });
  if (response.status === 401 && token) {
    localStorage.removeItem("whiskerwise_token");
    window.location.replace("/");
    throw new Error("Your session expired. Please log in again.");
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "The request could not be completed.");
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

function queryString(values: Record<string, string | number | undefined>) {
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== "") params.set(key, String(value));
  });
  const query = params.toString();
  return query ? `?${query}` : "";
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
  getPet: (petId: string) => request<Pet>(`/pets/${petId}`),
  createPet: (payload: {
    name: string;
    breed?: string;
    sex: Sex;
    date_of_birth?: string;
    notes?: string;
    feeding_method: FeedingMethod;
    feeding_notes?: string;
    activity_level: ActivityLevel;
    sociability_with_people: Sociability;
    sociability_with_animals: Sociability;
    routine_sensitivity: RoutineSensitivity;
    known_triggers: string[];
    personality_notes?: string;
  }) =>
    request<Pet>("/pets", {
      method: "POST",
      body: JSON.stringify({ ...payload, species: "cat" }),
    }),
  updatePet: (
    petId: string,
    payload: Partial<Pick<Pet,
      | "name" | "breed" | "sex" | "date_of_birth" | "notes"
      | "feeding_method" | "feeding_notes" | "activity_level"
      | "sociability_with_people" | "sociability_with_animals"
      | "routine_sensitivity" | "known_triggers" | "personality_notes"
    >>,
  ) => request<Pet>(`/pets/${petId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deletePet: (petId: string) =>
    request<{ message: string; deleted_observations: number }>(`/pets/${petId}`, {
      method: "DELETE",
    }),
  listObservations: (filters: ObservationFilters = {}) =>
    request<Observation[]>(`/observations${queryString({ ...filters })}`),
  getObservation: (observationId: string) =>
    request<Observation>(`/observations/${observationId}`),
  deleteObservation: (observationId: string) =>
    request<void>(`/observations/${observationId}`, { method: "DELETE" }),
  createObservation: (payload: {
    pet_id: string;
    text_description: string;
    context: ObservationContext;
  }) => request<Observation>("/observations", { method: "POST", body: JSON.stringify(payload) }),
  createObservationWithVideo: (
    payload: { pet_id: string; text_description: string; context: ObservationContext },
    video: File,
    consent: boolean,
    onProgress: (progress: number) => void,
  ) => uploadObservation(payload, video, consent, onProgress),
  getMediaBlob: (path: string) => requestBlob(path),
};

function uploadObservation(
  payload: { pet_id: string; text_description: string; context: ObservationContext },
  video: File,
  consent: boolean,
  onProgress: (progress: number) => void,
): Promise<Observation> {
  return new Promise((resolve, reject) => {
    const token = localStorage.getItem("whiskerwise_token");
    const body = new FormData();
    body.set("payload", JSON.stringify(payload));
    body.set("video", video);
    body.set("media_consent_confirmed", String(consent));
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/observations/with-video`);
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    };
    xhr.onload = () => {
      if (xhr.status === 401 && token) {
        localStorage.removeItem("whiskerwise_token");
        window.location.replace("/");
        reject(new Error("Your session expired. Please log in again."));
      } else if (xhr.status < 200 || xhr.status >= 300) {
        try { reject(new Error(JSON.parse(xhr.responseText).detail)); }
        catch { reject(new Error("The video observation could not be saved.")); }
      } else {
        resolve(JSON.parse(xhr.responseText) as Observation);
      }
    };
    xhr.onerror = () => reject(new Error("The video upload failed."));
    xhr.send(body);
  });
}

async function requestBlob(path: string): Promise<Blob> {
  const token = localStorage.getItem("whiskerwise_token");
  const response = await fetch(`${API_URL}${path}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) throw new Error("Private media could not be loaded.");
  return response.blob();
}
