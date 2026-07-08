import { test, expect } from "@playwright/test";
// Only import types from the SPA, never code
import { type BuilderInput } from "../../spa/src/features/locnet/api-generated-client";
import { type LocNetModel } from "../../spa/src/features/locnet/model";
import { assertNever } from "./typescript";





test("can select technologies", async ({ page }) => {
  await page.goto("");
  await page.getByTestId("sel_country").selectOption("NZL");

  await expect(page.getByTestId("introduction")).toHaveText("Introduction");
});
