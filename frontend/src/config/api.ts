/**
 * VisionGuard API Configuration.
 * Dynamically resolves the API base URL based on the current browser host,
 * preventing localhost IPv4/IPv6 mismatches and CORS connection failures.
 */

export const getApiBase = (): string => {
  // If running in development with Vite (port 5173), target port 8000 on the same host
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname || '127.0.0.1';
    const port = window.location.port;
    if (port === '5173' || port === '3000') {
      return `http://${hostname}:8000`;
    }
    // If served from the FastAPI backend directly, use relative URLs
    return '';
  }
  return 'http://127.0.0.1:8000';
};

export const API_BASE = getApiBase();
