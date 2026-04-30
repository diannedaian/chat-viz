export function withCommas(value) {
  return Number(value || 0).toLocaleString();
}

export function percent(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

export function hourLabel(hour24) {
  const suffix = hour24 >= 12 ? "PM" : "AM";
  const normalized = hour24 % 12 || 12;
  return `${normalized}:00 ${suffix}`;
}

export function shortDate(isoDate) {
  if (!isoDate) return "";
  const d = new Date(`${isoDate}T00:00:00`);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export function durationFromDates(startDate, endDate) {
  if (!startDate || !endDate) return 0;
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  return Math.max(1, Math.floor((end - start) / 86400000) + 1);
}
