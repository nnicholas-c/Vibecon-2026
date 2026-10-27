import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { friendlyMessage, http } from "@/lib/api";

const FleetContext = createContext(null);

export function FleetProvider({ children }) {
  const [fleet, setFleet] = useState(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);
  const [phonesOpen, setPhonesOpen] = useState(false);
  const [live, setLive] = useState(null);
  const [reorderFx, setReorderFx] = useState(null);
  const [highlight, setHighlightState] = useState({ keys: [], until: 0 });
  const setHighlight = useCallback((keys, ms = 10000) => setHighlightState({ keys: keys || [], until: Date.now() + ms }), []);

  const reload = useCallback(async () => {
    try {
      const { data } = await http.get("/fleet");
      setFleet(data);
      setError("");
    } catch (err) {
      setError(friendlyMessage(err, "Couldn't load the fleet. Try again in a moment."));
    }
    setVersion((v) => v + 1);
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  // "Open the demo" resets the data: drop the old fleet so Fleet only renders numbers fetched after the reset.
  useEffect(() => {
    const onReset = () => { setFleet(null); reload(); };
    window.addEventListener("dp-demo-reset", onReset);
    return () => window.removeEventListener("dp-demo-reset", onReset);
  }, [reload]);

  return (
    <FleetContext.Provider value={{ fleet, error, version, reload, phonesOpen, setPhonesOpen, highlight, setHighlight, live, setLive, reorderFx, setReorderFx }}>
      {children}
    </FleetContext.Provider>
  );
}

export function useFleet() {
  return useContext(FleetContext);
}
