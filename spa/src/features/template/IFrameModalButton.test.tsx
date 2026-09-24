import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, test } from 'vitest';
import { IframeModalButton, isOutsideDialog } from './IFrameModalButton';

describe('IframeModalButton', () => {
  test('renders the dialog without a close button', () => {
    const html = renderToStaticMarkup(
      <IframeModalButton url="/documentation" dialogHeader="Documentation">
        Documentation
      </IframeModalButton>,
    );

    expect(html).not.toContain('<button');
    expect(html).toContain('aria-label="Documentation"');
    expect(html).toContain('src="/documentation?embedded=true"');
  });

  test('identifies clicks outside the dialog bounds', () => {
    const bounds = { top: 100, right: 300, bottom: 300, left: 100 };

    expect(isOutsideDialog(99, 200, bounds)).toBe(true);
    expect(isOutsideDialog(301, 200, bounds)).toBe(true);
    expect(isOutsideDialog(200, 99, bounds)).toBe(true);
    expect(isOutsideDialog(200, 301, bounds)).toBe(true);
    expect(isOutsideDialog(200, 200, bounds)).toBe(false);
  });
});
