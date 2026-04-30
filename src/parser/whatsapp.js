const LINE_RE = /^\[(\d{4})\/(\d{1,2})\/(\d{1,2}) (\d{1,2}):(\d{2})(?::(\d{2}))?\] (.+?): (.*)$/;

function toTimestampMs(year, month, day, hour, minute, second = 0) {
  return new Date(year, month - 1, day, hour, minute, second).getTime();
}

export function parseWhatsAppTxt(rawText) {
  const lines = (rawText || "").split(/\r?\n/);
  const messages = [];
  let current = null;

  lines.forEach((line) => {
    const match = line.match(LINE_RE);
    if (match) {
      const [, y, mo, d, h, mi, s, sender, text] = match;
      current = {
        timestampMs: toTimestampMs(Number(y), Number(mo), Number(d), Number(h), Number(mi), Number(s || 0)),
        sender: sender.trim(),
        text: text.trim(),
        type: text.includes("端到端加密") ? "system" : "message",
      };
      messages.push(current);
      return;
    }

    if (current) {
      current.text += `\n${line}`;
    }
  });

  return messages.sort((a, b) => a.timestampMs - b.timestampMs);
}
