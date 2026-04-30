import { DEFAULT_THEME } from "./schema.js";

export const THEME_PRESETS = {
  blossom: {
    background: "#F5EDD8",
    accent: "#E8748A",
    secondary: "#6BA3D6",
    text: "#2A2035",
    muted: "#8A8691",
  },
  midnight: {
    background: "#1A2744",
    accent: "#F2C84B",
    secondary: "#6BA3D6",
    text: "#F8F7FF",
    muted: "#B2B6C7",
  },
  forest: {
    background: "#EEF3E8",
    accent: "#5B8C5A",
    secondary: "#7BAA9D",
    text: "#1F2A1E",
    muted: "#6A756B",
  },
};

export const FONT_OPTIONS = [
  { id: "space-caveat", heading: "Caveat", body: "Space Grotesk", label: "Caveat + Space Grotesk" },
  { id: "inter-playfair", heading: "Playfair Display", body: "Inter", label: "Playfair + Inter" },
  { id: "nunito-poppins", heading: "Poppins", body: "Nunito Sans", label: "Poppins + Nunito" },
];

export function resolveTheme(presetId, customTheme) {
  const preset = THEME_PRESETS[presetId] || THEME_PRESETS.blossom;
  return { ...DEFAULT_THEME, ...preset, ...(customTheme || {}) };
}

export function resolveFontOption(fontId) {
  return FONT_OPTIONS.find((option) => option.id === fontId) || FONT_OPTIONS[0];
}
