/**
 * Major Tasmanian energy infrastructure locations.
 * Sources: Hydro Tasmania public asset list, TasNetworks substation register,
 *          AusGeo open data.
 *
 * Types:
 *   hydro       — Hydro Tasmania generation stations
 *   wind        — Wind farms
 *   substation  — Major transmission substations (TasNetworks)
 *   interconnect — Basslink HVDC interconnector terminal
 */

export const INFRASTRUCTURE = [
  // ── Hydro generation ──────────────────────────────────────────────
  {
    id: "gordon",
    name: "Gordon Power Station",
    type: "hydro",
    capacity_mw: 432,
    coords: [146.048, -42.755],
    description: "Tasmania's largest hydro station. 432 MW, Gordon Dam.",
  },
  {
    id: "poatina",
    name: "Poatina Power Station",
    type: "hydro",
    capacity_mw: 300,
    coords: [146.913, -41.773],
    description: "300 MW underground station, Great Lake catchment.",
  },
  {
    id: "john_butters",
    name: "John Butters Power Station",
    type: "hydro",
    capacity_mw: 225,
    coords: [145.836, -42.613],
    description: "225 MW, Pieman River scheme.",
  },
  {
    id: "trevallyn",
    name: "Trevallyn Power Station",
    type: "hydro",
    capacity_mw: 93,
    coords: [147.107, -41.452],
    description: "93 MW run-of-river station, South Esk River, Launceston.",
  },
  {
    id: "tungatinah",
    name: "Tungatinah Power Station",
    type: "hydro",
    capacity_mw: 125,
    coords: [146.497, -42.292],
    description: "125 MW, Central Highlands scheme.",
  },
  {
    id: "liapootah",
    name: "Liapootah Power Station",
    type: "hydro",
    capacity_mw: 90,
    coords: [146.409, -42.384],
    description: "90 MW, Derwent River scheme.",
  },
  {
    id: "catagunya",
    name: "Catagunya Power Station",
    type: "hydro",
    capacity_mw: 55,
    coords: [146.588, -42.286],
    description: "55 MW, Derwent River scheme.",
  },
  {
    id: "repulse",
    name: "Repulse Power Station",
    type: "hydro",
    capacity_mw: 57,
    coords: [146.676, -42.323],
    description: "57 MW, Derwent River scheme.",
  },

  // ── Wind generation ───────────────────────────────────────────────
  {
    id: "musselroe",
    name: "Musselroe Wind Farm",
    type: "wind",
    capacity_mw: 168,
    coords: [148.165, -40.842],
    description: "168 MW, 56 turbines. Tasmania's largest wind farm.",
  },
  {
    id: "woolnorth",
    name: "Woolnorth Wind Farm",
    type: "wind",
    capacity_mw: 140,
    coords: [144.741, -40.717],
    description: "140 MW, Cape Grim. One of Australia's windiest sites.",
  },
  {
    id: "bluff_point",
    name: "Bluff Point Wind Farm",
    type: "wind",
    capacity_mw: 33,
    coords: [145.437, -41.063],
    description: "33 MW, Heemskirk coastal region.",
  },

  // ── Major substations (TasNetworks 220kV/110kV) ───────────────────
  {
    id: "george_town",
    name: "George Town Substation",
    type: "substation",
    capacity_mw: null,
    coords: [146.833, -41.100],
    description: "220 kV. Basslink terminal substation, northern TAS.",
  },
  {
    id: "campbell_town",
    name: "Campbell Town Substation",
    type: "substation",
    capacity_mw: null,
    coords: [147.490, -41.923],
    description: "110 kV, Midlands transmission corridor.",
  },
  {
    id: "hobart_substation",
    name: "Hobart (Risdon) Substation",
    type: "substation",
    capacity_mw: null,
    coords: [147.358, -42.807],
    description: "220 kV. Primary supply for greater Hobart.",
  },

  // ── Interconnector ────────────────────────────────────────────────
  {
    id: "basslink",
    name: "Basslink Terminal (Loy Yang end: VIC)",
    type: "interconnect",
    capacity_mw: 500,
    coords: [146.854, -41.081],
    description: "500 MW HVDC undersea cable to Victoria (Loy Yang). ~290 km.",
  },
];

/**
 * SVG icon paths per infrastructure type.
 * All icons are designed on a 20×20 viewBox, centred.
 */
export const TYPE_STYLE = {
  hydro: {
    color: "#4f8ef7",
    // Water drop
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C6 9 4 13 4 16a8 8 0 0 0 16 0c0-3-2-7-8-14z"/></svg>`,
  },
  wind: {
    color: "#34d399",
    // Wind turbine (three blades + pole)
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 12L8 4"/><path d="M12 12L4 16"/><path d="M12 12l8 0"/><circle cx="12" cy="12" r="2"/><line x1="12" y1="14" x2="12" y2="22"/></svg>`,
  },
  substation: {
    color: "#a78bfa",
    // Lightning bolt
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`,
  },
  interconnect: {
    color: "#fbbf24",
    // Share/network node
    svg: `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>`,
  },
};
