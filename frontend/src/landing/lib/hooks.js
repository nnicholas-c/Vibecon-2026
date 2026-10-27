import { useCallback, useEffect, useState } from "react";
import { MOTION_KEY, isPhoneSize } from "./constants";

const BACKEND = process.env.REACT_APP_BACKEND_URL;

export function useViewportInfo() {
  const read = () => ({ w: window.innerWidth, h: window.innerHeight, phone: isPhoneSize(window.innerWidth, window.innerHeight) });
  const [vp, setVp] = useState(read);
  useEffect(() => {
    const on = () => setVp(read());
    window.addEventListener("resize", on);
    return () => window.removeEventListener("resize", on);
  }, []);
  return vp;
}

const deviceReduced = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

// Motion switch: the stored choice wins, otherwise it follows the device setting.
export function useMotion() {
  const [on, setOn] = useState(() => {
    const s = localStorage.getItem(MOTION_KEY);
    return s ? s === "on" : !deviceReduced();
  });
  const toggle = useCallback(() => {
    setOn((v) => {
      localStorage.setItem(MOTION_KEY, v ? "off" : "on");
      return !v;
    });
  }, []);
  return [on, toggle];
}

// Spec default numbers, used ONLY as a loading placeholder until the engine answers.
export const PRICE_PLACEHOLDER = {
  added_minutes: 4,
  added_miles: 0.6,
  time_cost: 1.28,
  mile_cost: 0.46,
  cost_with_markup: 3.48,
  floor: 11,
  usual: 14,
  offer: 11,
  wage_per_hour: 19.27,
  cost_per_mile: 0.76,
  markup_pct: 100,
};

export function useLandingPrice() {
  const [price, setPrice] = useState({ ...PRICE_PLACEHOLDER, placeholder: true });
  useEffect(() => {
    let alive = true;
    fetch(`${BACKEND}/api/landing/price`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((d) => alive && setPrice({ ...PRICE_PLACEHOLDER, ...d, placeholder: false }))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  return price;
}

export const money = (n) => `$${Number(n).toFixed(2)}`;
export const visit = (n) => (Number.isInteger(Number(n)) ? `$${Number(n)}` : `$${Number(n).toFixed(2)}`);
export const pct = (n) => `${Number.isInteger(Number(n)) ? Number(n) : Number(n).toFixed(1)}%`;
