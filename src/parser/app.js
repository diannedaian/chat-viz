import { buildChatVizData } from "./buildData.js";
import { parseWhatsAppTxt } from "./whatsapp.js";
import { validateChatVizData } from "../shared/schema.js";

const fileInput = document.querySelector("#chatUpload");
const runBtn = document.querySelector("#runParser");
const downloadBtn = document.querySelector("#downloadJson");
const openViewerBtn = document.querySelector("#openViewer");
const statsBox = document.querySelector("#parserStats");
const errorsBox = document.querySelector("#parserErrors");

let generatedData = null;

function formatSummary(data) {
  const p1 = data.people[0]?.name || "Person 1";
  const p2 = data.people[1]?.name || "Person 2";
  return `
    <div><strong>Pair:</strong> ${p1} x ${p2}</div>
    <div><strong>Total messages:</strong> ${data.metrics.totalMessages.toLocaleString()}</div>
    <div><strong>Active days:</strong> ${data.metrics.activeDays.toLocaleString()}</div>
    <div><strong>Date range:</strong> ${data.customization.startDate} - ${data.customization.endDate}</div>
    <div><strong>Top word:</strong> ${data.metrics.topWords[0]?.word || "n/a"}</div>
  `;
}

runBtn.addEventListener("click", async () => {
  const [file] = fileInput.files || [];
  if (!file) {
    errorsBox.textContent = "Please upload a WhatsApp .txt export first.";
    return;
  }
  try {
    const text = await file.text();
    const messages = parseWhatsAppTxt(text);
    generatedData = buildChatVizData(messages);
    const validation = validateChatVizData(generatedData);
    if (!validation.valid) {
      errorsBox.textContent = `Schema validation failed: ${validation.errors.join(" ")}`;
      generatedData = null;
      return;
    }
    errorsBox.textContent = "";
    statsBox.innerHTML = formatSummary(generatedData);
    downloadBtn.disabled = false;
    openViewerBtn.disabled = false;
  } catch (error) {
    errorsBox.textContent = `Parsing error: ${error.message}`;
  }
});

downloadBtn.addEventListener("click", () => {
  if (!generatedData) return;
  const blob = new Blob([JSON.stringify(generatedData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "my-chat-data.json";
  link.click();
  URL.revokeObjectURL(url);
});

openViewerBtn.addEventListener("click", () => {
  if (!generatedData) return;
  localStorage.setItem("chatviz:data", JSON.stringify(generatedData));
  window.location.href = "./viewer.html";
});
