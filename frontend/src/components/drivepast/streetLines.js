import { useEffect, useMemo, useState } from "react";
import { http } from "@/lib/api";
import { useFleet } from "@/context/FleetContext";

export const NO_LINES = "Street lines unavailable, showing straight lines.";

export function useStreetLines(routes) {
  const { version } = useFleet();
  const [lines, setLines] = useState({});
  const [failed, setFailed] = useState(false);
  const sig = (routes || []).map((r) => `${r.unit_key}:${r.stops.map((s) => `${s.lat},${s.lon}`).join("|")}`).join(";");
  useEffect(() => {
    let live = true;
    setFailed(false);
    (routes || []).forEach((r) => {
      http.get(`/map/geometry/${r.unit_key}`)
        .then(({ data }) => {
          if (!live) return;
          if (data.ok) setLines((m) => ({ ...m, [r.unit_key]: { sig, coords: data.coords } }));
          else setFailed(true);
        })
        .catch(() => live && setFailed(true));
    });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sig, version]);
  const merged = useMemo(() => (routes || []).map((r) => (lines[r.unit_key]?.sig === sig ? { ...r, geometry: lines[r.unit_key].coords } : r)), [routes, lines, sig]);
  return { routes: merged, note: failed ? NO_LINES : "" };
}
