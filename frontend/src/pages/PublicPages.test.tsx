import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { LandingPage } from "./LandingPage";
import { AboutPage } from "./AboutPage";
import { SignUpPage } from "./SignUpPage";

describe("public pages", () => {
  it("presents the landing page and account calls to action", () => {
    render(<MemoryRouter><LandingPage /></MemoryRouter>);
    expect(
      screen.getByRole("heading", { name: "A clearer view of your cat’s behaviour." }),
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Start a behaviour journal" }))
      .toHaveAttribute("href", "/signup");
    expect(screen.getByText(/not a veterinary diagnostic tool/i)).toBeInTheDocument();
  });

  it("shows the required account fields", () => {
    render(<MemoryRouter><SignUpPage /></MemoryRouter>);
    expect(screen.getByLabelText("Your name")).toBeRequired();
    expect(screen.getByLabelText("Email")).toBeRequired();
    expect(screen.getByLabelText(/^Password/, { selector: "input" })).toBeRequired();
    expect(screen.getByLabelText("Confirm password")).toBeRequired();
  });

  it("explains the project principles on the about page", () => {
    render(<MemoryRouter><AboutPage /></MemoryRouter>);
    expect(screen.getByRole("heading", {
      name: "Careful technology for a relationship built on observation.",
    })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Show the reasoning" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Know the boundary" })).toBeInTheDocument();
  });
});
