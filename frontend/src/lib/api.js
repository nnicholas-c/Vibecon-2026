import axios from "axios";

export const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
export const http = axios.create({ baseURL: API, timeout: 15000, withCredentials: true });
export const OFFLINE_MSG = "Can't reach Drivepast right now. Try again in a moment.";

export function isOffline(err) {
  const res = err?.response;
  if (!res) return true;
  const hasDetail = typeof res.data?.detail?.message === "string";
  return [502, 503, 504].includes(res.status) && !hasDetail;
}

export function friendlyMessage(err, fallback) {
  if (isOffline(err)) return OFFLINE_MSG;
  const msg = err?.response?.data?.detail?.message;
  return typeof msg === "string" && msg ? msg : fallback;
}
