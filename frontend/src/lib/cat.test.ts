import { describe, expect, it } from "vitest";
import { formatCatAge } from "./cat";

describe("formatCatAge", () => {
  it("shows years and remaining months", () => {
    expect(formatCatAge("2023-01-10", new Date("2026-07-24T12:00:00")))
      .toBe("3 years, 6 months old");
  });

  it("shows months for kittens and handles missing dates", () => {
    expect(formatCatAge("2026-03-24", new Date("2026-07-24T12:00:00")))
      .toBe("4 months old");
    expect(formatCatAge()).toBeNull();
  });
});
