import type { ReactNode } from "react";

type Page = "pets" | "observe";

export function Layout({
  children,
  page,
  onNavigate,
}: {
  children: ReactNode;
  page: Page;
  onNavigate: (page: Page) => void;
}) {
  return (
    <div className="shell">
      <header>
        <button className="brand" onClick={() => onNavigate("pets")}>
          <span aria-hidden="true">◇</span>
          <span>Whiskerwise</span>
        </button>
        <nav aria-label="Main navigation">
          <button className={page === "pets" ? "active" : ""} onClick={() => onNavigate("pets")}>
            Cat profiles
          </button>
          <button className={page === "observe" ? "active" : ""} onClick={() => onNavigate("observe")}>
            New observation
          </button>
        </nav>
      </header>
      <main>{children}</main>
      <footer>
        This tool offers possible behavioural interpretations, not veterinary diagnoses. Sudden or
        concerning changes should be discussed with a veterinarian.
      </footer>
    </div>
  );
}

