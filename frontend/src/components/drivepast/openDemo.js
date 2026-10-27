import { http } from "@/lib/api";

export const DEMO_KEY = "dp-demo-open";

// Every "Open the demo" button: Reset demo data first, then /dispatch, so each run starts clean.
export async function openDemo(navigate) {
  localStorage.setItem(DEMO_KEY, "1");
  try { await http.post("/demo/reset", {}, { timeout: 90000 }); } catch { /* Fleet still opens and shows its own error */ }
  window.dispatchEvent(new Event("dp-demo-reset"));
  navigate("/dispatch");
}
