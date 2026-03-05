import { describe, expect, it } from "vitest";

import { API_BASE } from "./lib/api";

describe("admin config", () => {
  it("has api base", () => {
    expect(API_BASE).toBeTruthy();
  });
});
