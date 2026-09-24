import { expect, test } from "./fixtures";

test("renders responsive Quick Start images and closes from the backdrop", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Quick Start", exact: true }).click();

  const dialog = page.getByRole("dialog", { name: "Quick Start Guide" });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("button")).toHaveCount(0);

  const guide = page.frameLocator('iframe[title="Quick Start Guide"]');
  const image = guide.getByRole("img").first();
  await expect(image).toBeVisible();

  const imageWidth = await image.evaluate(
    (element) => element.getBoundingClientRect().width,
  );
  const documentWidth = await guide.locator(".markdown-document").evaluate(
    (element) => {
      const styles = getComputedStyle(element);
      return (
        element.getBoundingClientRect().width -
        Number.parseFloat(styles.paddingLeft) -
        Number.parseFloat(styles.paddingRight)
      );
    },
  );
  expect(imageWidth).toBeCloseTo(documentWidth, 0);

  await dialog.getByText("Quick Start Guide", { exact: true }).click();
  await expect(dialog).toBeVisible();

  await page.mouse.click(1, 1);
  await expect(dialog).not.toBeVisible();
});
