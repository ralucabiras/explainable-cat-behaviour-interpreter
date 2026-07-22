import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import { Layout } from "./components/Layout";
import { NewObservationPage } from "./pages/NewObservationPage";
import { PetsPage } from "./pages/PetsPage";
import type { Pet } from "./types";

type Page = "pets" | "observe";

export default function App() {
  const [page, setPage] = useState<Page>("pets");
  const [pets, setPets] = useState<Pet[]>([]);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    try { setPets(await api.listPets()); setLoadError(""); }
    catch { setLoadError("The API is unavailable. Check that the backend and MongoDB are running."); }
  }, []);

  useEffect(() => {
    void api.listPets().then(setPets).catch(() => {
      setLoadError("The API is unavailable. Check that the backend and MongoDB are running.");
    });
  }, []);

  return (
    <Layout page={page} onNavigate={setPage}>
      {loadError && <div className="notice error">{loadError}</div>}
      {page === "pets" ? <PetsPage pets={pets} refresh={refresh} /> : <NewObservationPage pets={pets} />}
    </Layout>
  );
}
