import { useCallback, useEffect, useState } from "react";
import { http } from "@/lib/api";

// GET `path` now and every `ms` while the tab is visible.
export function usePoll(path, ms) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const load = useCallback(() => http.get(path).then(({ data: d }) => { setData(d); setError(""); })
    .catch(() => setError("Can't reach Drivepast right now. Retrying.")), [path]);
  useEffect(() => {
    let t = null;
    const sync = () => {
      clearInterval(t);
      t = null;
      if (document.visibilityState === "visible") { load(); t = setInterval(load, ms); }
    };
    sync();
    document.addEventListener("visibilitychange", sync);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", sync); };
  }, [load, ms]);
  return { data, error, load };
}
