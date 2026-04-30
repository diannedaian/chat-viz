import { DEFAULT_CHAT_VIZ_DATA } from "../data/defaultData.js";
import { validateChatVizData } from "../shared/schema.js";
import { FONT_OPTIONS, resolveFontOption, resolveTheme, THEME_PRESETS } from "../shared/themes.js";
import { buildSlides } from "./slides.js";

const STORAGE_KEYS = {
  data: "chatviz:data",
  tweaks: "chatviz:tweaks",
  slideIndex: "chatviz:slideIndex",
};

const root = document.querySelector("#app");
const fileInput = document.querySelector("#jsonUpload");
const errorBox = document.querySelector("#viewerErrors");

let state = {
  data: DEFAULT_CHAT_VIZ_DATA,
  tweaks: {
    ...DEFAULT_CHAT_VIZ_DATA.customization,
    coverTitle: DEFAULT_CHAT_VIZ_DATA.slides.cover.title,
    daysCountOverride: DEFAULT_CHAT_VIZ_DATA.customization.daysCountOverride || "",
  },
  currentSlide: 0,
};

function tryLoadFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const encoded = params.get("data");
  if (!encoded) return null;
  try {
    const decoded = atob(encoded);
    return JSON.parse(decoded);
  } catch (error) {
    return null;
  }
}

function tryLoadFromStorage() {
  try {
    const rawData = localStorage.getItem(STORAGE_KEYS.data);
    const rawTweaks = localStorage.getItem(STORAGE_KEYS.tweaks);
    const rawSlide = localStorage.getItem(STORAGE_KEYS.slideIndex);
    return {
      data: rawData ? JSON.parse(rawData) : null,
      tweaks: rawTweaks ? JSON.parse(rawTweaks) : null,
      currentSlide: rawSlide ? Number(rawSlide) : 0,
    };
  } catch (error) {
    return { data: null, tweaks: null, currentSlide: 0 };
  }
}

function saveState() {
  localStorage.setItem(STORAGE_KEYS.data, JSON.stringify(state.data));
  localStorage.setItem(STORAGE_KEYS.tweaks, JSON.stringify(state.tweaks));
  localStorage.setItem(STORAGE_KEYS.slideIndex, String(state.currentSlide));
}

function applyIncomingData(candidate) {
  const result = validateChatVizData(candidate);
  if (!result.valid) {
    errorBox.textContent = `JSON schema error: ${result.errors.join(" ")}`;
    return;
  }
  state.data = candidate;
  state.tweaks = {
    ...state.tweaks,
    ...candidate.customization,
    coverTitle: candidate.slides?.cover?.title || state.tweaks.coverTitle,
  };
  state.currentSlide = 0;
  errorBox.textContent = "";
  render();
}

function setThemeAndFonts() {
  const theme = resolveTheme(state.tweaks.themePreset, state.tweaks.customTheme);
  const font = resolveFontOption(state.tweaks.fontPreset);
  document.documentElement.style.setProperty("--bg", theme.background);
  document.documentElement.style.setProperty("--accent", theme.accent);
  document.documentElement.style.setProperty("--secondary", theme.secondary);
  document.documentElement.style.setProperty("--text", theme.text);
  document.documentElement.style.setProperty("--muted", theme.muted);
  document.documentElement.style.setProperty("--font-heading", `'${font.heading}', cursive`);
  document.documentElement.style.setProperty("--font-body", `'${font.body}', sans-serif`);
}

function renderTweaksPanel() {
  const presetOptions = Object.keys(THEME_PRESETS)
    .map((id) => `<option value="${id}" ${state.tweaks.themePreset === id ? "selected" : ""}>${id}</option>`)
    .join("");
  const fontOptions = FONT_OPTIONS.map(
    (option) =>
      `<option value="${option.id}" ${state.tweaks.fontPreset === option.id ? "selected" : ""}>${option.label}</option>`
  ).join("");

  return `
    <aside class="tweak-panel">
      <h3>Tweaks</h3>
      <label>Person 1 <input data-tweak="name1" value="${state.data.people[0]?.name || ""}" /></label>
      <label>Person 2 <input data-tweak="name2" value="${state.data.people[1]?.name || ""}" /></label>
      <label>Relationship
        <select data-tweak="relationshipType">
          <option value="romantic" ${state.tweaks.relationshipType === "romantic" ? "selected" : ""}>romantic</option>
          <option value="friendship" ${state.tweaks.relationshipType === "friendship" ? "selected" : ""}>friendship</option>
          <option value="family" ${state.tweaks.relationshipType === "family" ? "selected" : ""}>family</option>
        </select>
      </label>
      <label>Theme
        <select data-tweak="themePreset">${presetOptions}</select>
      </label>
      <label>Heading + body font
        <select data-tweak="fontPreset">${fontOptions}</select>
      </label>
      <label>Start date <input type="date" data-tweak="startDate" value="${state.tweaks.startDate || ""}" /></label>
      <label>End date <input type="date" data-tweak="endDate" value="${state.tweaks.endDate || ""}" /></label>
      <label>Duration override <input data-tweak="daysCountOverride" value="${state.tweaks.daysCountOverride || ""}" /></label>
      <label>Cover title <input data-tweak="coverTitle" value="${state.tweaks.coverTitle || ""}" /></label>
      <div class="custom-colors">
        <label>Accent <input type="color" data-tweak="accent" value="${state.tweaks.customTheme?.accent || "#E8748A"}" /></label>
        <label>Secondary <input type="color" data-tweak="secondary" value="${
          state.tweaks.customTheme?.secondary || "#6BA3D6"
        }" /></label>
      </div>
    </aside>
  `;
}

function renderSlides() {
  const slides = buildSlides(state.data, state.tweaks);
  return slides
    .map(
      (slide, idx) => `
    <article class="slide ${idx === state.currentSlide ? "active" : ""}">
      ${slide}
    </article>
  `
    )
    .join("");
}

function render() {
  setThemeAndFonts();
  root.innerHTML = `
    <main class="viewer-shell">
      <section class="phone">
        <div class="slide-stack">${renderSlides()}</div>
        <footer class="nav">
          <button data-action="prev">Prev</button>
          <span>${state.currentSlide + 1} / ${buildSlides(state.data, state.tweaks).length}</span>
          <button data-action="next">Next</button>
        </footer>
      </section>
      ${renderTweaksPanel()}
    </main>
  `;
  bindInteractions();
  saveState();
}

function bindInteractions() {
  root.querySelectorAll("[data-action]").forEach((element) => {
    element.addEventListener("click", () => {
      const action = element.getAttribute("data-action");
      const total = buildSlides(state.data, state.tweaks).length;
      if (action === "prev") state.currentSlide = Math.max(0, state.currentSlide - 1);
      if (action === "next") state.currentSlide = Math.min(total - 1, state.currentSlide + 1);
      if (action === "restart") state.currentSlide = 0;
      render();
    });
  });

  root.querySelectorAll("[data-tweak]").forEach((field) => {
    field.addEventListener("input", (event) => {
      const key = field.getAttribute("data-tweak");
      const value = event.target.value;
      if (key === "name1") state.data.people[0].name = value;
      else if (key === "name2") state.data.people[1].name = value;
      else if (key === "accent") state.tweaks.customTheme = { ...(state.tweaks.customTheme || {}), accent: value };
      else if (key === "secondary")
        state.tweaks.customTheme = { ...(state.tweaks.customTheme || {}), secondary: value };
      else state.tweaks[key] = value;
      window.parent.postMessage({ type: "__edit_mode_set_keys", edits: state.tweaks }, "*");
      render();
    });
  });
}

fileInput.addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  if (!file) return;
  try {
    const parsed = JSON.parse(await file.text());
    applyIncomingData(parsed);
  } catch (error) {
    errorBox.textContent = `Failed to parse JSON: ${error.message}`;
  }
});

window.addEventListener("message", (event) => {
  if (event.data?.type === "__activate_edit_mode") document.body.classList.add("force-show-tweaks");
  if (event.data?.type === "__deactivate_edit_mode") document.body.classList.remove("force-show-tweaks");
});

window.parent.postMessage({ type: "__edit_mode_available" }, "*");

const queryData = tryLoadFromQuery();
if (queryData) {
  applyIncomingData(queryData);
} else {
  const stored = tryLoadFromStorage();
  if (stored.data) {
    state.data = stored.data;
    state.tweaks = { ...state.tweaks, ...(stored.tweaks || {}) };
    state.currentSlide = stored.currentSlide || 0;
  }
}

render();
