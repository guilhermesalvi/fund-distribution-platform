// parse.mjs - reads a JSON array of {id, text} from stdin, runs mermaid.parse()
// on each block under jsdom and prints one JSON object per line to stdout:
//   {"id": ..., "ok": true, "type": "sequence"} or {"id": ..., "ok": false, "error": "..."}
// No rendering, no browser: mermaid.parse() only needs a DOM-like global.
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, "navigator", { value: dom.window.navigator, configurable: true });

const mermaid = (await import("mermaid")).default;
mermaid.initialize({ startOnLoad: false, logLevel: 5, suppressErrorRendering: true });

const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const blocks = JSON.parse(Buffer.concat(chunks).toString("utf8"));

for (const block of blocks) {
  try {
    const r = await mermaid.parse(block.text, { suppressErrors: false });
    process.stdout.write(JSON.stringify({ id: block.id, ok: true, type: r ? r.diagramType : null }) + "\n");
  } catch (e) {
    const msg = (e && e.message) ? e.message : String(e);
    process.stdout.write(JSON.stringify({ id: block.id, ok: false, error: msg }) + "\n");
  }
}
