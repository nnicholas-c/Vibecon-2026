import { useEffect } from "react";
import { C } from "./constants";

// The app's global theme is dark; the landing sits on the table color.
export function usePageColors() {
  useEffect(() => {
    const b = document.body.style.background;
    const s = document.documentElement.style.colorScheme;
    document.body.style.background = C.table;
    document.documentElement.style.colorScheme = "light";
    return () => {
      document.body.style.background = b;
      document.documentElement.style.colorScheme = s;
    };
  }, []);
}
