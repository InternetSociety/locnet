import { test, expect } from 'vitest';
import { locNetForm, type EditableLocNetForm } from './formData';

test('Form data exists', async () => {
  // This shouldn't error as the Editable type should be same but broader
  const editableForm: EditableLocNetForm = {
    nodes: locNetForm.nodes,
    set() {},
    api: {
      characteristics: undefined,
      bounds: undefined,
      modelerAPIOutput: undefined
    },
  };
  expect(editableForm).toBeTruthy();

  // Verify editing works correctly
  const editingTest: EditableLocNetForm = {
    ...locNetForm,
    set() {},
  };

  // this is a trivial test, and the real test is the TypeScript
  expect(editingTest).toBeTruthy();
});

test('starts with the introduction followed by country selection', () => {
  expect(locNetForm.nodes[0]).toMatchObject({
    type: 'Disclosure',
    labelIntlId: 'introduction',
    children: [{ type: 'HTML', intlId: 'welcome' }],
  });
  expect(locNetForm.nodes[1]).toMatchObject({
    type: 'CountriesDropdown',
    labelIntlId: 'sel_country',
  });
});
