// Expose selected Vite env vars to the app in a single place
export const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN || null;
export const API_BASE = import.meta.env.VITE_API_BASE || '/api';
