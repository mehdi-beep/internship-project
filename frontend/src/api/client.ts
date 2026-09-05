import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export const apiClient = axios.create({
  baseURL: API_URL,
  // Without this, axios's own default (no timeout) means a request to a
  // slow/unresponsive server hangs until the browser's own uncontrolled
  // OS-level TCP timeout gives up (observed live: tens of seconds, no
  // feedback the whole time) rather than failing fast with a clear error —
  // this looked exactly like "the page is stuck/not refreshing" on a flaky
  // connection, when the request was actually still (uselessly) in flight.
  // reportService.ts's downloadExport() explicitly overrides this per-call,
  // since a file export can legitimately take longer than a normal fetch.
  timeout: 15_000,
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("bims_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("bims_token");
      window.dispatchEvent(new Event("bims:unauthorized"));
    }
    return Promise.reject(error);
  },
);
