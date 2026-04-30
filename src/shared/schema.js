export const RELATIONSHIP_TYPES = ["romantic", "friendship", "family"];

export const CHAT_VIZ_SCHEMA_VERSION = "1.0.0";

export const DEFAULT_THEME = {
  background: "#F5EDD8",
  accent: "#E8748A",
  secondary: "#6BA3D6",
  text: "#2A2035",
  muted: "#8A8691",
};

export const DEFAULT_FONTS = {
  heading: "Caveat",
  body: "Space Grotesk",
};

export function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function validateChatVizData(data) {
  const errors = [];

  if (!isObject(data)) {
    return { valid: false, errors: ["Root must be an object."] };
  }

  const requiredKeys = ["meta", "people", "metrics", "slides", "customization"];
  requiredKeys.forEach((key) => {
    if (!(key in data)) {
      errors.push(`Missing required key: ${key}`);
    }
  });

  if (!isObject(data.meta)) {
    errors.push("meta must be an object.");
  } else {
    if (typeof data.meta.title !== "string") errors.push("meta.title must be a string.");
    if (typeof data.meta.generatedAt !== "string") errors.push("meta.generatedAt must be a string.");
    if (typeof data.meta.schemaVersion !== "string") errors.push("meta.schemaVersion must be a string.");
  }

  if (!Array.isArray(data.people) || data.people.length < 2) {
    errors.push("people must be an array with at least 2 participants.");
  } else {
    data.people.forEach((person, index) => {
      if (!isObject(person)) {
        errors.push(`people[${index}] must be an object.`);
        return;
      }
      if (typeof person.id !== "string") errors.push(`people[${index}].id must be a string.`);
      if (typeof person.name !== "string") errors.push(`people[${index}].name must be a string.`);
    });
  }

  if (!isObject(data.metrics)) {
    errors.push("metrics must be an object.");
  }

  if (!isObject(data.slides)) {
    errors.push("slides must be an object.");
  }

  if (!isObject(data.customization)) {
    errors.push("customization must be an object.");
  } else {
    if (
      data.customization.relationshipType &&
      !RELATIONSHIP_TYPES.includes(data.customization.relationshipType)
    ) {
      errors.push("customization.relationshipType must be romantic, friendship, or family.");
    }
  }

  return { valid: errors.length === 0, errors };
}
