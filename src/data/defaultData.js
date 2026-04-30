import { CHAT_VIZ_SCHEMA_VERSION } from "../shared/schema.js";

export const DEFAULT_CHAT_VIZ_DATA = {
  meta: {
    schemaVersion: CHAT_VIZ_SCHEMA_VERSION,
    title: "Dianne x Yifan",
    generatedAt: new Date().toISOString(),
    source: "demo",
  },
  people: [
    { id: "p1", name: "Dianne" },
    { id: "p2", name: "Yifan" },
  ],
  metrics: {
    totalMessages: 178869,
    longestStreakDays: 636,
    avgMessagesPerDay: 275,
    activeDays: 649,
    totalDays: 725,
    replyStats: [
      { name: "Yifan", medianSec: 17, meanSec: 384, count: 37541 },
      { name: "Dianne", medianSec: 16, meanSec: 372, count: 37631 },
    ],
    topWords: [
      { word: "baby", count: 5893 },
      { word: "can", count: 3309 },
      { word: "feel", count: 2763 },
      { word: "then", count: 2536 },
    ],
    languageShare: { zh: 85.1, en: 14.9, mixed: 4.5 },
    busiestHour: { hour: 0, count: 11293 },
    topDays: [
      { date: "2025-12-24", count: 1212 },
      { date: "2026-02-04", count: 973 },
      { date: "2025-12-28", count: 917 },
      { date: "2026-01-29", count: 880 },
      { date: "2025-08-02", count: 878 },
    ],
    calls: {
      totalSeconds: 474960,
      count: 747,
      longestSeconds: 8220,
      averageSeconds: 1066,
    },
  },
  slides: {
    cover: { title: "REPORT", subtitle: "Dianne x Yifan.", startYear: 2024, endYear: 2026 },
    ending: { title: "Dianne x Yifan", startYear: 2024, endLabel: "present" },
  },
  customization: {
    relationshipType: "romantic",
    themePreset: "blossom",
    customTheme: {},
    fontPreset: "space-caveat",
    startDate: "2024-04-03",
    endDate: "2026-04-01",
    daysCountOverride: "",
  },
};
