const EN_STOP = new Set([
  "the",
  "and",
  "that",
  "with",
  "this",
  "from",
  "have",
  "just",
  "your",
  "about",
  "what",
  "when",
  "where",
  "were",
  "dont",
  "cant",
  "im",
  "you",
  "for",
  "are",
  "was",
  "its",
  "too",
]);

export function classifyLanguage(text) {
  let cjk = 0;
  let latin = 0;
  for (const char of text || "") {
    if (/[\u4e00-\u9fff]/u.test(char)) cjk += 1;
    else if (/[A-Za-z]/.test(char)) latin += 1;
  }
  const total = cjk + latin;
  if (total === 0) return "mixed";
  const cjkShare = cjk / total;
  if (cjkShare > 0.6) return "zh";
  if (cjkShare < 0.4) return "en";
  return "mixed";
}

export function topWords(messages, limit = 5) {
  const counter = new Map();
  messages.forEach((msg) => {
    const normalized = (msg.text || "").toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, " ");
    normalized
      .split(/\s+/)
      .map((token) => token.trim())
      .filter((token) => token.length > 1 && !EN_STOP.has(token))
      .forEach((token) => {
        counter.set(token, (counter.get(token) || 0) + 1);
      });
  });

  return [...counter.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([word, count]) => ({ word, count }));
}

export function computeReplyStats(messages, people) {
  const byPerson = new Map(people.map((person) => [person.name, []]));
  for (let i = 1; i < messages.length; i += 1) {
    const prev = messages[i - 1];
    const current = messages[i];
    if (prev.sender === current.sender) continue;
    const gap = (current.timestampMs - prev.timestampMs) / 1000;
    if (gap <= 0 || gap > 86400) continue;
    if (!byPerson.has(current.sender)) continue;
    byPerson.get(current.sender).push(gap);
  }

  return people.map((person) => {
    const values = byPerson.get(person.name) || [];
    if (values.length === 0) {
      return { name: person.name, medianSec: 0, meanSec: 0, count: 0 };
    }
    const sorted = [...values].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    const medianSec = sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
    const meanSec = values.reduce((sum, value) => sum + value, 0) / values.length;
    return { name: person.name, medianSec, meanSec, count: values.length };
  });
}

export function formatDuration(seconds) {
  const safe = Math.max(0, Math.round(seconds || 0));
  const h = Math.floor(safe / 3600);
  const m = Math.floor((safe % 3600) / 60);
  const s = safe % 60;
  if (h) return `${h}h ${m}m`;
  if (m) return `${m}m ${s}s`;
  return `${s}s`;
}

export function computeDateRange(messages) {
  if (!messages.length) return { startDate: "", endDate: "", totalDays: 0 };
  const start = new Date(messages[0].timestampMs);
  const end = new Date(messages[messages.length - 1].timestampMs);
  const totalDays = Math.max(1, Math.floor((end - start) / 86400000) + 1);
  return {
    startDate: start.toISOString().slice(0, 10),
    endDate: end.toISOString().slice(0, 10),
    totalDays,
  };
}

export function computeActivity(messages) {
  const dayCounter = new Map();
  const hourCounter = new Array(24).fill(0);
  const langCounter = { zh: 0, en: 0, mixed: 0 };
  messages.forEach((msg) => {
    const d = new Date(msg.timestampMs);
    const dayKey = d.toISOString().slice(0, 10);
    dayCounter.set(dayKey, (dayCounter.get(dayKey) || 0) + 1);
    hourCounter[d.getHours()] += 1;
    langCounter[classifyLanguage(msg.text)] += 1;
  });

  const topDays = [...dayCounter.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([date, count]) => ({ date, count }));

  const busiestHour = hourCounter.reduce(
    (best, count, hour) => (count > best.count ? { hour, count } : best),
    { hour: 0, count: 0 }
  );

  const totalLang = langCounter.zh + langCounter.en + langCounter.mixed || 1;
  return {
    topDays,
    busiestHour,
    languageShare: {
      zh: (langCounter.zh / totalLang) * 100,
      en: (langCounter.en / totalLang) * 100,
      mixed: (langCounter.mixed / totalLang) * 100,
    },
  };
}
