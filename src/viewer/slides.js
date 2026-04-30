import { formatDuration } from "../shared/metrics.js";
import { getRelationshipCopy } from "../shared/relationshipCopy.js";
import { durationFromDates, hourLabel, percent, shortDate, withCommas } from "./formatters.js";

function slideFrame(title, content) {
  return `
    <section class="slide-card">
      <h2 class="slide-title">${title}</h2>
      <div class="slide-body">${content}</div>
    </section>
  `;
}

export function buildSlides(data, tweaks) {
  const copy = getRelationshipCopy(tweaks.relationshipType);
  const m = data.metrics;
  const people = data.people;
  const durationDays =
    tweaks.daysCountOverride ||
    durationFromDates(tweaks.startDate || data.customization.startDate, tweaks.endDate || data.customization.endDate);

  const topWords = (m.topWords || []).slice(0, 4);
  const topDays = (m.topDays || []).slice(0, 5);

  const slides = [
    slideFrame(
      tweaks.coverTitle || data.slides.cover.title,
      `
      <div class="hero-range">${data.slides.cover.startYear} - ${data.slides.cover.endYear}</div>
      <div class="hero-name">${people[0].name} x ${people[1].name}</div>
      <div class="hero-subtitle">${copy.subtitle}</div>
    `
    ),
    slideFrame(
      "Overview",
      `
      <div class="stat-grid">
        <div><span class="big">${withCommas(m.totalMessages)}</span><small>Total messages</small></div>
        <div><span class="big">${withCommas(m.longestStreakDays)}</span><small>Longest streak (days)</small></div>
        <div><span class="big">${withCommas(m.avgMessagesPerDay)}</span><small>Average per day</small></div>
      </div>
      <p class="muted-note">${withCommas(m.activeDays)} active days out of ${withCommas(m.totalDays)}</p>
    `
    ),
    slideFrame(
      "Reply Speed",
      `
      ${(m.replyStats || [])
        .map(
          (item) => `
        <div class="list-row">
          <strong>${item.name}</strong>
          <span>Median: ${formatDuration(item.medianSec)}</span>
          <span>Mean: ${formatDuration(item.meanSec)}</span>
          <span>${withCommas(item.count)} replies</span>
        </div>
      `
        )
        .join("")}
    `
    ),
    slideFrame(
      "Top Words",
      `
      ${
        topWords[0]
          ? `<div class="word-hero">${topWords[0].word}<small>${withCommas(topWords[0].count)} times</small></div>`
          : ""
      }
      <div class="word-list">
        ${topWords
          .slice(1)
          .map((item) => `<div>${item.word}<span>${withCommas(item.count)}</span></div>`)
          .join("")}
      </div>
    `
    ),
    slideFrame(
      "Night Owls",
      `
      <div class="centered-big">${hourLabel(m.busiestHour.hour)}</div>
      <p class="muted-note">Busiest hour with ${withCommas(m.busiestHour.count)} messages</p>
    `
    ),
    slideFrame(
      "Language Mix",
      `
      <div class="lang-bars">
        <label>Chinese <span>${percent(m.languageShare.zh)}</span></label>
        <progress max="100" value="${m.languageShare.zh}"></progress>
        <label>English <span>${percent(m.languageShare.en)}</span></label>
        <progress max="100" value="${m.languageShare.en}"></progress>
        <label>Mixed <span>${percent(m.languageShare.mixed)}</span></label>
        <progress max="100" value="${m.languageShare.mixed}"></progress>
      </div>
    `
    ),
    slideFrame(
      "Most Active Days",
      `
      <div class="day-list">
        ${topDays
          .map(
            (item) =>
              `<div><strong>${shortDate(item.date)}</strong><span>${withCommas(item.count)} msgs</span></div>`
          )
          .join("")}
      </div>
    `
    ),
    slideFrame(
      "Calls",
      `
      <div class="centered-big">${formatDuration(m.calls.totalSeconds)}</div>
      <p>${withCommas(m.calls.count)} total calls</p>
      <p>Longest: ${formatDuration(m.calls.longestSeconds)}</p>
      <p>Average: ${formatDuration(m.calls.averageSeconds)}</p>
    `
    ),
    slideFrame(
      "Seasons",
      `
      <div class="season-grid">
        <div>Spring <span>${percent(24)}</span></div>
        <div>Summer <span>${percent(19)}</span></div>
        <div>Fall <span>${percent(34)}</span></div>
        <div>Winter <span>${percent(23)}</span></div>
      </div>
    `
    ),
    slideFrame(
      "Forever",
      `
      <div class="hero-name">${people[0].name} x ${people[1].name}</div>
      <div class="hero-subtitle">${durationDays} days ${copy.endingTagline} ${copy.icon}</div>
      <p class="muted-note">${tweaks.startDate || data.customization.startDate} - ${
        tweaks.endDate || data.customization.endDate
      }</p>
      <button class="restart-btn" data-action="restart">Watch again</button>
    `
    ),
  ];

  return slides;
}
