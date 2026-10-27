export const C = {
  table: "#D6D3CA",
  paper: "#F4F2EC",
  ink: "#141414",
  body: "#2B2A27",
  muted: "#5C5A54",
  hair: "#CFCBC2",
  accent: "#FF5B1F",
  sign: "#0E5A43",
};

export const RGB = {
  base: [232, 230, 223],
  ground: [226, 224, 218],
  building: [247, 246, 242],
  water: [194, 202, 205],
  roads: [
    [178, 175, 168],
    [190, 187, 180],
    [199, 196, 190],
    [208, 206, 201],
    [186, 183, 176],
  ],
  roadWidths: [20, 15, 12, 8, 3.5],
  shadow: [70, 62, 50, 60],
  trail: [30, 30, 30],
  van: [44, 44, 44],
  accent: [255, 91, 31],
  ink: [20, 20, 20],
  paper: [244, 242, 236],
};

export const MODEL_CENTER = [-122.3228, 37.8314];
export const DEMO_KEY = "dp-demo-open";
export const MOTION_KEY = "dp-landing-motion";

export const isPhoneSize = (w, h) => w < 640 || w / h < 0.85;

// Chapter buttons glide targets (5.7)
export const CHAPTERS = [
  { n: "01", name: "Fleet", p: 1 },
  { n: "02", name: "Request", p: 2 },
  { n: "03", name: "Time", p: 3 },
  { n: "04", name: "Price", p: 4.5 },
  { n: "05", name: "Send", p: 5.6 },
];

export const CREDIT_LONG =
  "Map data © OpenStreetMap contributors. Tiles OpenFreeMap © OpenMapTiles. Routes by OSRM. Shadows set for 1:45pm on Oct 24.";
export const CREDIT_SHORT = "© OpenStreetMap contributors, OpenMapTiles, OSRM";
