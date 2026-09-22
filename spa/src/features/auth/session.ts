import { getDomJson } from '../form/domJson';

export type CurrentUser = {
  email: string;
  is_admin: boolean;
  api_access_enabled: boolean;
};

export const getCurrentUser = (): CurrentUser | null =>
  getDomJson('current_user') as CurrentUser | null;

export const getCsrfToken = (): string => getDomJson('csrf_token') as string;

export const authenticatedHeaders = (): Record<string, string> => ({
  'X-CSRF-Token': getCsrfToken(),
});
