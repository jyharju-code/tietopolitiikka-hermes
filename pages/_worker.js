const SESSION_COOKIE = "tp_session";
const SESSION_SECONDS = 12 * 60 * 60;
const MEMBERSHIP_RECHECK_SECONDS = 15 * 60;
// Reject a Telegram login payload whose signed auth_date is older than this.
const AUTH_MAX_AGE_SECONDS = 24 * 60 * 60;
const WIDGET_SCRIPT = "https://telegram.org/js/telegram-widget.js?22";

const encoder = new TextEncoder();
const decoder = new TextDecoder();

function base64url(bytes) {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary).replaceAll("+", "-").replaceAll("/", "_").replaceAll("=", "");
}

function fromBase64url(value) {
  const padded = value.replaceAll("-", "+").replaceAll("_", "/") + "=".repeat((4 - (value.length % 4)) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, (character) => character.charCodeAt(0));
}

function hex(bytes) {
  let output = "";
  for (const byte of bytes) output += byte.toString(16).padStart(2, "0");
  return output;
}

async function hmac(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    encoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(value)));
}

function constantTimeEquals(a, b) {
  if (a.length !== b.length) return false;
  let difference = 0;
  for (let index = 0; index < a.length; index += 1) {
    difference |= a.charCodeAt(index) ^ b.charCodeAt(index);
  }
  return difference === 0;
}

async function seal(payload, secret) {
  const body = base64url(encoder.encode(JSON.stringify(payload)));
  return `${body}.${base64url(await hmac(body, secret))}`;
}

async function unseal(value, secret) {
  if (!value || !value.includes(".")) return null;
  const [body, signature] = value.split(".", 2);
  const expected = base64url(await hmac(body, secret));
  if (!constantTimeEquals(signature, expected)) return null;
  try {
    return JSON.parse(decoder.decode(fromBase64url(body)));
  } catch {
    return null;
  }
}

function cookies(request) {
  const result = {};
  for (const part of (request.headers.get("Cookie") || "").split(";")) {
    const index = part.indexOf("=");
    if (index > 0) result[part.slice(0, index).trim()] = part.slice(index + 1).trim();
  }
  return result;
}

function cookie(name, value, maxAge) {
  return `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}

function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
}

function html(body, status = 200, headers = {}) {
  return new Response(`<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tietopolitiikka Hermes</title><style>body{margin:0;background:#08111f;color:#eef4ff;font:17px system-ui,sans-serif;display:grid;min-height:100vh;place-items:center}.card{width:min(560px,calc(100% - 40px));padding:42px;border:1px solid #24344e;border-radius:24px;background:#101c2f;box-shadow:0 20px 70px #0008}h1{font-size:34px;margin:0 0 14px}p{color:#b9c6da;line-height:1.55}a.button{display:inline-block;margin-top:18px;padding:14px 20px;border-radius:12px;background:#2aabee;color:white;text-decoration:none;font-weight:700}.small{font-size:14px}.widget{margin-top:22px;min-height:48px}</style></head><body><main class="card">${body}</main></body></html>`, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", ...headers },
  });
}

function redirect(location, headers = {}) {
  return new Response(null, { status: 302, headers: { Location: location, "Cache-Control": "no-store", ...headers } });
}

function loginPage(request, env, status = 200) {
  const callback = new URL("/oauth/callback", request.url).toString();
  const widget = `<div class="widget"><script async src="${WIDGET_SCRIPT}" data-telegram-login="${escapeHtml(env.TELEGRAM_BOT_USERNAME)}" data-size="large" data-userpic="false" data-auth-url="${escapeHtml(callback)}"></script></div>`;
  return html(`<h1>Tietopolitiikka Hermes</h1><p>Ryhmän yhteinen agentti, keskustelumuisti ja aineistot yhdessä paikassa.</p>${widget}<p class="small">Käyttöoikeus tarkistetaan yksityisen Telegram-superryhmän jäsenyydestä.</p>`, status);
}

// Verify a classic Telegram Login Widget payload. The widget redirects to the
// callback with the signed fields as query parameters. The signature is an
// HMAC-SHA256 over the sorted data check string, keyed by SHA-256 of the bot
// token. See https://core.telegram.org/widgets/login-legacy.
async function verifyTelegramLogin(params, botToken) {
  const received = params.get("hash");
  if (!received) return null;
  const pairs = [];
  for (const [key, value] of params) {
    if (key !== "hash") pairs.push(`${key}=${value}`);
  }
  pairs.sort();
  const secretKey = new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(botToken)));
  const key = await crypto.subtle.importKey("raw", secretKey, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = new Uint8Array(await crypto.subtle.sign("HMAC", key, encoder.encode(pairs.join("\n"))));
  if (!constantTimeEquals(hex(mac), received.toLowerCase())) return null;
  const authDate = Number(params.get("auth_date") || "0");
  const now = Math.floor(Date.now() / 1000);
  if (!authDate || authDate > now + 60 || now - authDate > AUTH_MAX_AGE_SECONDS) return null;
  const id = params.get("id");
  if (!id) return null;
  return { id, name: params.get("first_name") || params.get("username") || "Telegram-jäsen" };
}

async function groupMember(userId, env) {
  const endpoint = `https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/getChatMember`;
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_GROUP_ID, user_id: Number(userId) }),
  });
  if (!response.ok) return false;
  const payload = await response.json();
  if (!payload.ok || !payload.result) return false;
  const member = payload.result;
  return ["creator", "administrator", "member"].includes(member.status) || (member.status === "restricted" && member.is_member === true);
}

async function finishLogin(request, env) {
  const url = new URL(request.url);
  const user = await verifyTelegramLogin(url.searchParams, env.TELEGRAM_BOT_TOKEN);
  if (!user) return html("<h1>Kirjautuminen epäonnistui</h1><p>Telegram-allekirjoitusta ei voitu vahvistaa tai se oli vanhentunut. Yritä uudelleen.</p><a class=\"button\" href=\"/login\">Yritä uudelleen</a>", 401);
  if (!(await groupMember(user.id, env))) return html("<h1>Ei käyttöoikeutta</h1><p>Dashboard on vain Tietopolitiikka Hermes -superryhmän nykyisille jäsenille.</p>", 403);
  const now = Math.floor(Date.now() / 1000);
  const session = await seal({ sub: String(user.id), name: user.name, checked: now, exp: now + SESSION_SECONDS }, env.SESSION_SECRET);
  return redirect("/", { "Set-Cookie": cookie(SESSION_COOKIE, session, SESSION_SECONDS) });
}

async function loadSession(request, env) {
  const session = await unseal(cookies(request)[SESSION_COOKIE], env.SESSION_SECRET);
  const now = Math.floor(Date.now() / 1000);
  if (!session || !session.sub || session.exp <= now) return { session: null, refreshed: null };
  if (now - session.checked < MEMBERSHIP_RECHECK_SECONDS) return { session, refreshed: null };
  if (!(await groupMember(session.sub, env))) return { session: null, refreshed: cookie(SESSION_COOKIE, "", 0) };
  session.checked = now;
  return { session, refreshed: cookie(SESSION_COOKIE, await seal(session, env.SESSION_SECRET), session.exp - now) };
}

async function originFetch(request, env, method, bodyBuffer, cookieHeader) {
  const incoming = new URL(request.url);
  const origin = new URL(env.HERMES_ORIGIN);
  origin.pathname = incoming.pathname;
  origin.search = incoming.search;
  const headers = new Headers(request.headers);
  headers.delete("Cookie");
  if (cookieHeader) headers.set("Cookie", cookieHeader);
  headers.set("X-Forwarded-Host", incoming.host);
  headers.set("X-Forwarded-Proto", incoming.protocol.slice(0, -1));
  headers.delete("CF-Access-Client-Id");
  headers.delete("CF-Access-Client-Secret");
  if (env.CF_ACCESS_CLIENT_ID) headers.set("CF-Access-Client-Id", env.CF_ACCESS_CLIENT_ID);
  if (env.CF_ACCESS_CLIENT_SECRET) headers.set("CF-Access-Client-Secret", env.CF_ACCESS_CLIENT_SECRET);
  return fetch(new Request(origin.toString(), {
    method,
    headers,
    body: ["GET", "HEAD"].includes(method) ? undefined : bodyBuffer,
    redirect: "manual",
  }));
}

function unauthenticatedOrigin(response) {
  if (response.status === 401) return true;
  if (response.status === 302) {
    const location = response.headers.get("Location") || "";
    return location.includes("/login") || location.includes("/auth/");
  }
  return false;
}

// The upstream dashboard has its own session login at /auth/password-login. The
// worker signs in once with the shared credential and hands the resulting
// session cookies to the already Telegram-authorized member, so the dashboard
// login never appears to the browser. Returns { cookieHeader, setCookies }.
async function mintDashboardSession(env) {
  const login = new URL("/auth/password-login", env.HERMES_ORIGIN);
  const headers = { "Content-Type": "application/json" };
  if (env.CF_ACCESS_CLIENT_ID) headers["CF-Access-Client-Id"] = env.CF_ACCESS_CLIENT_ID;
  if (env.CF_ACCESS_CLIENT_SECRET) headers["CF-Access-Client-Secret"] = env.CF_ACCESS_CLIENT_SECRET;
  const response = await fetch(login.toString(), {
    method: "POST",
    headers,
    body: JSON.stringify({ provider: "basic", username: env.ORIGIN_BASIC_AUTH_USERNAME, password: env.ORIGIN_BASIC_AUTH_PASSWORD, next: "/app" }),
    redirect: "manual",
  });
  if (response.status !== 200) return null;
  const setCookies = response.headers.getSetCookie ? response.headers.getSetCookie() : [];
  if (!setCookies.length) return null;
  const pairs = setCookies.map((line) => line.split(";", 1)[0]).filter(Boolean);
  const secured = setCookies.map((line) => (/;\s*secure/i.test(line) ? line : `${line}; Secure`));
  return { cookieHeader: pairs.join("; "), setCookies: secured };
}

// The dashboard opens a WebSocket for live updates. A Worker only proxies an
// upgrade when the request is forwarded untouched, so this path must not read
// the body or rewrite the response.
function isWebSocketUpgrade(request) {
  return (request.headers.get("Upgrade") || "").toLowerCase() === "websocket";
}

function proxyWebSocket(request, env) {
  const incoming = new URL(request.url);
  const origin = new URL(env.HERMES_ORIGIN);
  origin.pathname = incoming.pathname;
  origin.search = incoming.search;
  const headers = new Headers(request.headers);
  headers.set("X-Forwarded-Host", incoming.host);
  headers.set("X-Forwarded-Proto", incoming.protocol.slice(0, -1));
  headers.delete("CF-Access-Client-Id");
  headers.delete("CF-Access-Client-Secret");
  if (env.CF_ACCESS_CLIENT_ID) headers.set("CF-Access-Client-Id", env.CF_ACCESS_CLIENT_ID);
  if (env.CF_ACCESS_CLIENT_SECRET) headers.set("CF-Access-Client-Secret", env.CF_ACCESS_CLIENT_SECRET);
  return fetch(origin.toString(), { method: request.method, headers });
}

async function proxyDashboard(request, env, refreshed) {
  if (isWebSocketUpgrade(request)) return proxyWebSocket(request, env);
  const method = request.method;
  const bodyBuffer = ["GET", "HEAD"].includes(method) ? undefined : await request.arrayBuffer();
  let mintedCookies = null;
  let upstream = await originFetch(request, env, method, bodyBuffer, request.headers.get("Cookie"));
  if (unauthenticatedOrigin(upstream)) {
    const minted = await mintDashboardSession(env);
    if (minted) {
      mintedCookies = minted.setCookies;
      upstream = await originFetch(request, env, method, bodyBuffer, minted.cookieHeader);
    }
  }
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("WWW-Authenticate");
  responseHeaders.set("Cache-Control", "no-store");
  if (refreshed) responseHeaders.append("Set-Cookie", refreshed);
  if (mintedCookies) for (const line of mintedCookies) responseHeaders.append("Set-Cookie", line);
  return new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers: responseHeaders });
}

function authConfigured(env) {
  return ["SESSION_SECRET", "TELEGRAM_BOT_USERNAME", "TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID"].every((key) => env[key]);
}

function proxyConfigured(env) {
  return ["HERMES_ORIGIN", "ORIGIN_BASIC_AUTH_USERNAME", "ORIGIN_BASIC_AUTH_PASSWORD"].every((key) => env[key]);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      if (!authConfigured(env)) return new Response("configuration incomplete", { status: 503 });
      return new Response(proxyConfigured(env) ? "ok" : "ok, dashboard proxy pending", { status: 200 });
    }
    if (!authConfigured(env)) return html("<h1>Tietopolitiikka Hermes</h1><p>Dashboardin turvallinen käyttöönotto on vielä kesken.</p>", 503);
    // An already authorized member must never be bounced back to the Telegram
    // widget, otherwise a dashboard redirect to /login becomes a login loop.
    if (url.pathname === "/login") {
      const existing = await loadSession(request, env);
      if (existing.session) return redirect("/", existing.refreshed ? { "Set-Cookie": existing.refreshed } : {});
      return loginPage(request, env);
    }
    if (url.pathname === "/oauth/callback") return finishLogin(request, env);
    if (url.pathname === "/logout") return redirect("/", { "Set-Cookie": cookie(SESSION_COOKIE, "", 0) });

    const auth = await loadSession(request, env);
    if (!auth.session) {
      return loginPage(request, env);
    }
    // Namespaced so it cannot shadow the dashboard's own /api/auth/me, which
    // the dashboard frontend needs in order to consider itself signed in.
    if (url.pathname === "/_tp/me") return Response.json({ id: auth.session.sub, name: auth.session.name, member: true }, { headers: auth.refreshed ? { "Set-Cookie": auth.refreshed } : {} });
    if (!proxyConfigured(env)) {
      return html(`<h1>Tervetuloa, ${escapeHtml(auth.session.name)}</h1><p>Kirjautuminen ja jäsenyystarkistus toimivat. Dashboard-yhteys otetaan käyttöön seuraavassa vaiheessa.</p><a class="button" href="/logout">Kirjaudu ulos</a>`, 200, auth.refreshed ? { "Set-Cookie": auth.refreshed } : {});
    }
    return proxyDashboard(request, env, auth.refreshed);
  },
};
