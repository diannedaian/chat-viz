# Data Dictionary

## `metrics`

- `totalMessages`: number of non-system messages.
- `longestStreakDays`: longest consecutive-day run with at least one message.
- `avgMessagesPerDay`: rounded `totalMessages / totalDays`.
- `activeDays`: distinct message days.
- `totalDays`: inclusive day span from first to last message.
- `replyStats[]`: per person response-time aggregates in seconds.
- `topWords[]`: ranked lexical frequencies.
- `languageShare`: `{ zh, en, mixed }` percentages.
- `busiestHour`: hour (`0-23`) with max message count.
- `topDays[]`: highest-volume dates.
- `calls`: summarized call indicators.

## `customization`

- `relationshipType`: changes copy and icon set.
- `themePreset`: named palette (`blossom`, `midnight`, `forest`).
- `customTheme`: optional color overrides.
- `fontPreset`: typography pairing.
- `startDate` / `endDate`: displayed range and duration basis.
- `daysCountOverride`: optional manual override string.
