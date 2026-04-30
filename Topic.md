## Concept

A animated interactive experience that transforms 1.5 years of WeChat message history between me and my boyfriend into a visual, scrollable portrait of our relationship. Inspired by the "end-of-year summary" trend popularized by Spotify Wrapped and apps like Beli Plated, this project packages personal messaging data into a shareable, celebratory narrative.

P.S. The bilingual dimension (Chinese ↔ English) adds a unique layer

## Experience

The final product will borrow key design patterns from Spotify Wrapped and similar year-in-review formats:

- **Card-based storytelling**: A sequence of full-screen "slides" the user taps or scrolls through, each revealing a single stat, insight, or moment
- **Bold typographic reveals**: Large numbers, punchy one-liners, and animated data that feel celebratory rather than detailed data/plots
- **Personalized highlights**: "Your longest conversation lasted 6 hours," "You sent 你好 more than hello," "Your busiest texting day was Valentine's Day."
- **Share ability**: Designed to feel like something you'd screenshot and send to friends.

## Cards Brainstorm

1. **The Big Numbers** — Total messages sent, total days covered, average messages per day, longest streak of consecutive texting days.
2. **The Timeline** — A scrollable volume chart showing texting density over 1.5 years, with annotated peaks and valleys (first date, trips, long-distance stretches, moving in together, quiet periods).
3. **Language Split** — Overall ratio of Chinese vs. English messages, plus how that ratio shifted over time. When did English creep in? When did Chinese dominate? What triggered the switches?
4. **Peak Hours** — A clock or heatmap showing when we text most (late-night conversations vs. morning check-ins).
5. **Top Words & Phrases** — Most-used words in each language, recurring inside jokes, pet names, emoji usage.
6. **Milestone Moments** — Manually annotated key dates overlaid on the timeline: first date, first trip, arguments, celebrations.
7. **Response Patterns** — Average response time, who double-texts more, who sends longer messages.

## Template Vision (Future Goal)

The ultimate goal is to make this a **reusable template**: any couple could export their own WeChat chat history, upload it, and receive their own personalized experience. For this phase, the template will still be tailored to my data and my relationship's key moments.

## Current Status & Next Steps

| Status | Item |
| --- | --- |
| Done | Concept direction chosen, reference research (Spotify Wrapped, Beli Plated) |
| Done | Story arc and visualization inventory defined |
| In Progress | WeChat chat history export (currently troubleshooting export issues) |
| ⬜ Next | Data preprocessing: parse timestamps, tag languages, clean dataset |
| ⬜ Next | Build stat computation pipeline |
| ⬜ Next | Design card layouts and interaction flow |
| ⬜ Next | Develop interactive prototype (HTML/JS or React) |
| ⬜ Next | Manual annotation of milestone moments |
| ⬜ Future | Generalize into uploadable template |

### On the Data Export Issue

WeChat chat history export sucks cuz it doesn't offer a native CSV export, so third-party tools or backup-based extraction methods are needed. Once the export is resolved and data is available, preprocessing and visualization development can move quickly.

## Technical Approach

- **Frontend**: React-based single-page app (Framer Motion or GSAP) for the card reveal
- **Visualization**: D3.js or Recharts for the timeline, heatmaps, and charts; custom SVG/CSS for the typographic stat cards.
- **Design language**: Bold, colorful, high-contrast? pink and cute? contrast the 2 people but also bring unison

## Source & Inspiration

- **Spotify Wrapped** (https://newsroom.spotify.com/?s=wrapped)
- **Beli Plated** ([https://beliapp.com](https://beliapp.com/))
- **Strava Year in Sport** (https://www.strava.com/year-in-sport)
- **Duolingo Year in Review** (https://blog.duolingo.com/year-in-review-behind-the-scenes/)
- **ChatGPT "Your Year with ChatGPT"** ([https://openai.com](https://openai.com/))

![3da4fcdec258af3cffc76032e573a8d5.jpg](attachment:2b2244b3-1492-45e3-98f8-c2b115a7ac2b:3da4fcdec258af3cffc76032e573a8d5.jpg)

![7145181724127c70719a96f9f536b05a.jpg](attachment:fee67f69-9f95-4100-8228-658bba4f9496:7145181724127c70719a96f9f536b05a.jpg)

![8204f97dfb87494c8b1375559a40e2a8.jpg](attachment:bc302810-55eb-4a34-8ebe-255063180abd:8204f97dfb87494c8b1375559a40e2a8.jpg)

![image.png](attachment:1df0e2ef-26a2-49af-9de1-8423c52354b4:image.png)

![image.png](attachment:6444cdf8-b63f-4837-8c83-83369dbd36d4:image.png)

![image.png](attachment:0897280d-d0d9-4867-89ba-3a91c573f8f4:image.png)

![image.png](attachment:dc356657-2f08-4a9e-b2a3-10ae58f459e1:image.png)

![image.png](attachment:313649d3-ffd5-41e9-a51d-ac57ff8bda90:image.png)

![image.png](attachment:94ffa2c2-481d-4496-a2ce-85d012859865:image.png)

![image.png](attachment:4a612c9a-6ff3-4d7a-93a0-f7b5b7d1e468:image.png)

![image.png](attachment:9e25e17a-cd78-4be0-8f2c-847d9e542c32:image.png)

![image.png](attachment:1f5a6b85-3d75-4bc2-bbea-efa7dee536e9:image.png)

![image.png](attachment:667bdc6b-bf9e-4494-908a-850a4e591605:image.png)
