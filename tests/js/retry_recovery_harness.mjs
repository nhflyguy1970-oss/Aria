/**
 * Behavioural harness for the Living Room Retry card (see tests/test_chat_retry_recovery.py).
 *
 * Loads the real chat_progress.js + chat_send.js in a vm context with a small DOM
 * stub and a scripted /api/chat, drives a failed turn and the Retry / Restart
 * Provider buttons, and counts user bubbles, requests and recovery cards.
 * Prints {"results": [{name, ok, detail}, ...]} as JSON.
 */
import vm from "node:vm";
import fs from "node:fs";
import path from "node:path";

const STATIC_DIR = path.resolve(process.argv[2]);
const settle = async (n = 20) => { for (let i = 0; i < n; i += 1) await new Promise((r) => setImmediate(r)); };

function makeEl(tag = "div") {
  const el = {
    tagName: tag.toUpperCase(), className: "", textContent: "", innerHTML: "", children: [],
    parent: null, style: {}, dataset: {}, disabled: false, hidden: false, _listeners: {},
    classList: { toggle() {}, add() {}, remove() {}, contains() { return false; } },
    appendChild(c) { c.parent = el; el.children.push(c); return c; },
    remove() {
      if (el.parent) el.parent.children = el.parent.children.filter((x) => x !== el);
      el.parent = null;
    },
    addEventListener(type, fn) { (el._listeners[type] ||= []).push(fn); },
    click() { (el._listeners.click || []).forEach((fn) => fn({ preventDefault() {} })); },
    setAttribute() {}, removeAttribute() {}, focus() { el.focused = true; },
    descendants() { return el.children.flatMap((c) => [c, ...c.descendants()]); },
    querySelector(sel) {
      if (sel === ".msg-body") return el._body || (el._body = makeEl());
      const cls = sel.startsWith(".") ? sel.slice(1) : null;
      return el.descendants().find((d) => cls && String(d.className).split(/\s+/).includes(cls)) || null;
    },
    querySelectorAll(sel) {
      if (sel === "button") return el.descendants().filter((d) => d.tagName === "BUTTON");
      return [];
    },
  };
  return el;
}

function sse(events) {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(ctrl) {
      for (const e of events) ctrl.enqueue(enc.encode(`data: ${JSON.stringify(e)}\n\n`));
      ctrl.close();
    },
  });
}

const FAIL = {
  type: "done", ok: false, message: "The model ran out of graphics memory.",
  error_category: "out_of_memory", request_id: "req-1", retryable: true,
};
const OK = { type: "done", ok: true, message: "", model: "gemma4:12b" };

function setup(script) {
  const messages = makeEl();
  const input = makeEl("textarea");
  const byId = { messages, messageInput: input, sendBtn: makeEl("button"), stopChatBtn: makeEl("button"),
    statusText: makeEl() };
  const log = { userBubbles: [], chatBodies: [], toasts: [], done: [], restarts: 0, errors: [] };
  const queue = [...script];
  const window = {
    jarvisChat: { useStreaming: true },
    jarvisAttach: {},
    addMessage(role, text) {
      if (role === "user") log.userBubbles.push(text);
      const row = makeEl(); row.className = `message ${role}`; row.textContent = text;
      messages.appendChild(row);
    },
    addTyping() { const t = makeEl(); t.className = "message assistant typing-msg"; messages.appendChild(t); return t; },
    handleDone(event, text) { log.done.push(text); window.addMessage("assistant", text); },
    finishSendUi() { window.hideProgress?.(); window.setChatBusy?.(false); },
    showAriaToast(msg) { log.toasts.push(msg); },
    showError(msg) { log.errors.push(msg); },
    formatMessage: (t) => t,
    escapeHtml: (t) => t,
    AriaChatOS: { noteUserPrompt() {} },
  };
  const document = {
    readyState: "complete",
    createElement: (tag) => makeEl(tag),
    getElementById: (id) => byId[id] || null,
    querySelector: () => null,
    addEventListener() {},
  };
  async function fetchStub(url, opts = {}) {
    if (url === "/api/provider/prefs") return { ok: false, json: async () => ({}) };
    if (url === "/api/provider/restart") {
      log.restarts += 1;
      return { ok: true, json: async () => ({ ok: true, message: "Provider restarted" }) };
    }
    if (url === "/api/chat") {
      log.chatBodies.push(opts.body?.get?.("message"));
      const step = queue.shift() || OK;
      const events = step === "ok" ? [{ type: "token", content: "Here is the plan." }, OK] : [FAIL];
      return { ok: true, status: 200, body: sse(events) };
    }
    throw new Error(`unexpected fetch ${url}`);
  }
  const ctx = {
    window, document, console, setTimeout, clearTimeout, setInterval, clearInterval, setImmediate, fetch: fetchStub,
    FormData, TextDecoder, TextEncoder, AbortController, ReadableStream, crypto: globalThis.crypto,
    localStorage: { getItem() { return null; }, setItem() {} },
  };
  window.window = window;
  window.document = document;
  window.fetch = fetchStub;
  vm.createContext(ctx);
  // Browser scripts resolve bare globals (sendMessage, document) against window.
  Object.setPrototypeOf(ctx, window);
  for (const f of ["chat_progress.js", "chat_send.js"]) {
    vm.runInContext(fs.readFileSync(path.join(STATIC_DIR, f), "utf8"), ctx, { filename: f });
  }
  const cards = () => messages.children.filter((r) => r.querySelector(".chat-recovery"));
  const button = (label) => cards().at(-1)?.descendants().find((d) => d.tagName === "BUTTON" && d.textContent === label);
  return { window, log, messages, cards, button, input };
}

const results = [];
const check = (name, ok, detail) => results.push({ name, ok: Boolean(ok), detail });
const PROMPT = "What should we work on?";

{
  const t = setup(["fail", "ok"]);
  await t.window.sendMessage(PROMPT);
  await settle();
  check("failure shows one recovery card", t.cards().length === 1, { cards: t.cards().length });
  check("failed message stays visible", t.log.userBubbles.length === 1, t.log.userBubbles);
  check("busy state reset after failure", t.window.jarvisChat.chatRequestActive === false, t.window.jarvisChat.chatRequestActive);
  t.button("Retry").click();
  await settle(60);
  check("retry sends the same request text", t.log.chatBodies.length === 2 && t.log.chatBodies[1] === PROMPT, t.log.chatBodies);
  check("retry draws no second user bubble", t.log.userBubbles.length === 1, t.log.userBubbles);
  check("retry removes its recovery card", t.cards().length === 0, { cards: t.cards().length });
  check("successful retry renders the reply once", t.log.done.length === 1 && t.log.done[0] === "Here is the plan.", t.log.done);
  check("busy state reset after retry", t.window.jarvisChat.chatRequestActive === false, t.window.jarvisChat.chatRequestActive);
  const users = t.messages.children.filter((r) => r.className === "message user").length;
  check("transcript holds exactly one user message", users === 1, { users });
}

{
  const t = setup(["fail", "ok"]);
  await t.window.sendMessage(PROMPT);
  await settle();
  const retry = t.button("Retry");
  retry.click();
  retry.click();
  retry.click();
  await settle(60);
  check("repeated Retry clicks send once", t.log.chatBodies.length === 2, t.log.chatBodies);
  check("repeated Retry clicks add no bubbles", t.log.userBubbles.length === 1, t.log.userBubbles);
}

{
  const t = setup(["fail", "fail", "fail", "ok"]);
  await t.window.sendMessage(PROMPT);
  await settle();
  for (let i = 0; i < 3; i += 1) {
    t.button("Retry").click();
    await settle(60);
  }
  check("chained retries keep one user bubble", t.log.userBubbles.length === 1, t.log.userBubbles);
  check("chained retries leave no stale cards", t.cards().length === 0, { cards: t.cards().length });
  check("chained retries end in one reply", t.log.done.length === 1, t.log.done);
  check("chained retries send four requests", t.log.chatBodies.length === 4, t.log.chatBodies.length);
}

{
  const t = setup(["fail", "ok"]);
  await t.window.sendMessage(PROMPT);
  await settle();
  t.window.jarvisChat.chatRequestActive = true;
  t.button("Retry").click();
  await settle(20);
  check("retry while a reply is running does not start a turn", t.log.chatBodies.length === 1, t.log.chatBodies);
  check("retry while busy explains why", t.log.toasts.some((m) => /Wait for the current reply/.test(m)), t.log.toasts);
  t.window.jarvisChat.chatRequestActive = false;
  t.button("Retry").click();
  await settle(60);
  check("retry works once the chat is free", t.log.chatBodies.length === 2 && t.log.userBubbles.length === 1,
    { requests: t.log.chatBodies.length, bubbles: t.log.userBubbles.length });
}

{
  const t = setup(["fail", "ok"]);
  await t.window.sendMessage(PROMPT);
  await settle();
  t.button("Restart Provider").click();
  await settle(60);
  check("restart provider then retries without a new bubble",
    t.log.restarts === 1 && t.log.chatBodies.length === 2 && t.log.userBubbles.length === 1 && t.cards().length === 0,
    { restarts: t.log.restarts, requests: t.log.chatBodies.length, bubbles: t.log.userBubbles.length });
}

{
  const t = setup([]);
  t.window.showProviderRecovery("Conversation too long", { retryText: "", reason: "context_overflow" });
  t.button("Retry").click();
  await settle();
  check("non-retryable failure focuses the composer instead of resending",
    t.log.chatBodies.length === 0 && t.input.focused === true, { requests: t.log.chatBodies.length });
}

console.log(JSON.stringify({ results }));
