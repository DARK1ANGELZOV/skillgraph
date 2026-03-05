import { describe, expect, it } from "vitest";

import { api } from "./lib/api";

describe("web api helper", () => {
  it("is a function", () => {
    expect(typeof api).toBe("function");
  });
});
