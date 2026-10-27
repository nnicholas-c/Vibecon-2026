// The procedural 3D van (PROMPT.md section 4). Meters, faces +x at yaw 0, origin at footprint center.
// Plain triangle list with per-vertex colors and no normals, so deck.gl flat-shades it.
const WHITE = [1, 1, 1];
const GLASS = [0.11, 0.12, 0.14];
const TRIM = [0.2, 0.2, 0.21];
const TIRE = [0.07, 0.07, 0.08];
const PROFILE = [
  [-3.0, 0.38],
  [2.95, 0.38],
  [3.0, 0.98],
  [2.55, 1.28],
  [1.55, 2.36],
  [1.2, 2.6],
  [-3.0, 2.6],
];
const HALF = 1.05;

export function buildVanMesh() {
  const pos = [];
  const col = [];
  const tri = (a, b, c, color) => {
    pos.push(...a, ...b, ...c);
    col.push(...color, ...color, ...color);
  };
  const quad = (a, b, c, d, color) => {
    tri(a, b, c, color);
    tri(a, c, d, color);
  };
  const P = ([x, z], y) => [x, y, z];

  // Body sides, fan-triangulated
  for (const y of [-HALF, HALF]) {
    for (let i = 1; i < PROFILE.length - 1; i++) tri(P(PROFILE[0], y), P(PROFILE[i], y), P(PROFILE[i + 1], y), WHITE);
  }
  // One quad per profile edge: 0 bottom and 1 front bumper are trim, 3 is the windshield
  const edgeColor = (i) => (i === 3 ? GLASS : i <= 1 ? TRIM : WHITE);
  for (let i = 0; i < PROFILE.length; i++) {
    const a = PROFILE[i];
    const b = PROFILE[(i + 1) % PROFILE.length];
    quad(P(a, -HALF), P(b, -HALF), P(b, HALF), P(a, HALF), edgeColor(i));
  }
  // Side windows, 1.5cm outside the body
  const win = [
    [1.3, 1.42],
    [2.42, 1.42],
    [1.68, 2.22],
    [1.3, 2.22],
  ];
  for (const y of [-(HALF + 0.015), HALF + 0.015]) quad(...win.map((p) => P(p, y)), GLASS);
  // Sliding door seam
  for (const y of [-(HALF + 0.01), HALF + 0.01]) {
    quad(P([-2.0, 0.62], y), P([-1.95, 0.62], y), P([-1.95, 2.44], y), P([-2.0, 2.44], y), TRIM);
  }
  // Wheels: 10-sided cylinders along y
  for (const cx of [2.05, -2.0]) {
    for (const cy of [0.86, -0.86]) wheel(tri, quad, cx, cy);
  }
  return {
    positions: { value: new Float32Array(pos), size: 3 },
    colors: { value: new Float32Array(col), size: 3 },
  };
}

function wheel(tri, quad, cx, cy) {
  const r = 0.38;
  const hw = 0.16;
  const cz = 0.38;
  const n = 10;
  const pt = (i, y) => {
    const a = (i / n) * Math.PI * 2;
    return [cx + r * Math.cos(a), y, cz + r * Math.sin(a)];
  };
  for (let i = 0; i < n; i++) {
    quad(pt(i, cy - hw), pt(i + 1, cy - hw), pt(i + 1, cy + hw), pt(i, cy + hw), TIRE);
    tri([cx, cy - hw, cz], pt(i, cy - hw), pt(i + 1, cy - hw), TIRE);
    tri([cx, cy + hw, cz], pt(i + 1, cy + hw), pt(i, cy + hw), TIRE);
  }
}
