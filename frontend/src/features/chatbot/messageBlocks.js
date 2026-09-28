// Replies are plain text from the knowledge base. Render them as paragraphs and lists —
// never as HTML — so nothing in a message can become markup.
const BULLET = /^[•\-*]\s+/;
const NUMBERED = /^\d+[.)]\s+/;

export function toBlocks(text) {
  const blocks = [];
  for (const raw of (text || "").split("\n")) {
    const line = raw.trim();
    if (!line) {
      blocks.push({ type: "gap" });
      continue;
    }
    const type = BULLET.test(line) ? "ul" : NUMBERED.test(line) ? "ol" : "p";
    const content = line.replace(type === "ul" ? BULLET : type === "ol" ? NUMBERED : "", "");
    const last = blocks[blocks.length - 1];
    if (type !== "p" && last?.type === type) last.items.push(content);
    else blocks.push(type === "p" ? { type, text: content } : { type, items: [content] });
  }
  // One gap between blocks at most, none at the start or end.
  const compact = blocks.filter((b, i) => b.type !== "gap" || blocks[i - 1]?.type !== "gap");
  while (compact[0]?.type === "gap") compact.shift();
  while (compact[compact.length - 1]?.type === "gap") compact.pop();
  return compact;
}
