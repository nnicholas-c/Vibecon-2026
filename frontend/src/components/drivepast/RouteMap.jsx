import { useState } from "react";
import CityMap from "./CityMap";
import LeafletRouteMap from "./LeafletRouteMap";

function hasWebGL() {
  try {
    if (localStorage.getItem("dp-flat-map") === "1") return false;
    const c = document.createElement("canvas");
    return Boolean(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

const GL = hasWebGL();

export default function RouteMap(props) {
  const [flat, setFlat] = useState(!GL);
  return flat ? <LeafletRouteMap {...props} /> : <CityMap {...props} onFail={() => setFlat(true)} />;
}
