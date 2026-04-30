import { DEFAULT_CHAT_VIZ_DATA } from "../data/defaultData.js";
import { computeActivity, computeDateRange, computeReplyStats, topWords } from "../shared/metrics.js";

function computeLongestStreak(activeDayKeys) {
  if (!activeDayKeys.length) return 0;
  const days = activeDayKeys
    .map((day) => new Date(`${day}T00:00:00`))
    .sort((a, b) => a - b);
  let best = 1;
  let cur = 1;
  for (let i = 1; i < days.length; i += 1) {
    const delta = (days[i] - days[i - 1]) / 86400000;
    if (delta === 1) cur += 1;
    else cur = 1;
    if (cur > best) best = cur;
  }
  return best;
}

export function buildChatVizData(messages) {
  if (!messages.length) {
    return structuredClone(DEFAULT_CHAT_VIZ_DATA);
  }

  const participants = [...new Set(messages.filter((m) => m.type !== "system").map((msg) => msg.sender))].slice(0, 2);
  while (participants.length < 2) participants.push(`Person ${participants.length + 1}`);

  const nonSystem = messages.filter((msg) => msg.type !== "system");
  const totalMessages = nonSystem.length;

  const activeDayCounter = new Map();
  nonSystem.forEach((msg) => {
    const day = new Date(msg.timestampMs).toISOString().slice(0, 10);
    activeDayCounter.set(day, (activeDayCounter.get(day) || 0) + 1);
  });

  const dateRange = computeDateRange(nonSystem);
  const longestStreakDays = computeLongestStreak([...activeDayCounter.keys()]);
  const avgMessagesPerDay = Math.round(totalMessages / Math.max(dateRange.totalDays, 1));
  const replyStats = computeReplyStats(nonSystem, participants.map((name, idx) => ({ id: `p${idx + 1}`, name })));
  const activity = computeActivity(nonSystem);
  const words = topWords(nonSystem, 5);

  const maybeCalls = nonSystem.filter((msg) => /\b(call|video|voice)\b/i.test(msg.text));
  const estimatedAverageCallSeconds = maybeCalls.length ? 8 * 60 : 0;
  const estimatedLongestCallSeconds = maybeCalls.length ? 35 * 60 : 0;
  const estimatedTotalSeconds = maybeCalls.length * estimatedAverageCallSeconds;

  const result = structuredClone(DEFAULT_CHAT_VIZ_DATA);
  result.meta.generatedAt = new Date().toISOString();
  result.meta.source = "whatsapp_txt";
  result.meta.title = `${participants[0]} x ${participants[1]}`;
  result.people = participants.map((name, idx) => ({ id: `p${idx + 1}`, name }));
  result.metrics.totalMessages = totalMessages;
  result.metrics.longestStreakDays = longestStreakDays;
  result.metrics.avgMessagesPerDay = avgMessagesPerDay;
  result.metrics.activeDays = activeDayCounter.size;
  result.metrics.totalDays = dateRange.totalDays;
  result.metrics.replyStats = replyStats;
  result.metrics.topWords = words;
  result.metrics.languageShare = activity.languageShare;
  result.metrics.busiestHour = activity.busiestHour;
  result.metrics.topDays = activity.topDays;
  result.metrics.calls = {
    totalSeconds: estimatedTotalSeconds,
    count: maybeCalls.length,
    longestSeconds: estimatedLongestCallSeconds,
    averageSeconds: estimatedAverageCallSeconds,
  };
  result.customization.startDate = dateRange.startDate;
  result.customization.endDate = dateRange.endDate;
  result.slides.cover.subtitle = `${participants[0]} x ${participants[1]}.`;
  result.slides.ending.title = `${participants[0]} x ${participants[1]}`;

  return result;
}
