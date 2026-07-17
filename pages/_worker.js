const OIDC_ISSUER = "https://oauth.telegram.org";
const OIDC_AUTH = `${OIDC_ISSUER}/auth`;
const OIDC_TOKEN = `${OIDC_ISSUER}/token`;
const OIDC_JWKS = `${OIDC_ISSUER}/.well-known/jwks.json`;
const SESSION_COOKIE = "tp_session";
const FLOW_COOKIE = "tp_oidc";
const SESSION_SECONDS = 12 * 60 * 60;
const MEMBERSHIP_RECHECK_SECONDS = 15 * 60;

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

function randomValue(bytes = 32) {
  const value = new Uint8Array(bytes);
  crypto.getRandomValues(value);
  return base64url(value);
}

async function sha256(value) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", encoder.encode(value)));
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

async function seal(payload, secret) {
  const body = base64url(encoder.encode(JSON.stringify(payload)));
  return `${body}.${base64url(await hmac(body, secret))}`;
}

async function unseal(value, secret) {
  if (!value || !value.includes(".")) return null;
  const [body, signature] = value.split(".", 2);
  const expected = base64url(await hmac(body, secret));
  if (signature.length !== expected.length) return null;
  let difference = 0;
  for (let index = 0; index < signature.length; index += 1) {
    difference |= signature.charCodeAt(index) ^ expected.charCodeAt(index);
  }
  if (difference !== 0) return null;
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

function html(body, status = 200, headers = {}) {
  return new Response(`<!doctype html><html lang="fi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Tietopolitiikka Hermes</title><style>body{margin:0;background:#08111f;color:#eef4ff;font:17px system-ui,sans-serif;display:grid;min-height:100vh;place-items:center}.card{width:min(560px,calc(100% - 40px));padding:42px;border:1px solid #24344e;border-radius:24px;background:#101c2f;box-shadow:0 20px 70px #0008}h1{font-size:34px;margin:0 0 14px}p{color:#b9c6da;line-height:1.55}a.button{display:inline-block;margin-top:18px;padding:14px 20px;border-radius:12px;background:#2aabee;color:white;text-decoration:none;font-weight:700}.small{font-size:14px}</style></head><body><main class="card">${body}</main></body></html>`, {
    status,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", ...headers },
  });
}

function redirect(location, headers = {}) {
  return new Response(null, { status: 302, headers: { Location: location, "Cache-Control": "no-store", ...headers } });
}

function callbackUrl(request) {
  const url = new URL(request.url);
  return `${url.protocol}//${url.host}/oauth/callback`;
}

async function beginLogin(request, env) {
  const state = randomValue();
  const nonce = randomValue();
  const verifier = randomValue(48);
  const challenge = base64url(await sha256(verifier));
  const flow = await seal({ state, nonce, verifier, exp: Math.floor(Date.now() / 1000) + 600 }, env.SESSION_SECRET);
  const params = new URLSearchParams({
    client_id: env.TELEGRAM_CLIENT_ID,
    redirect_uri: callbackUrl(request),
    response_type: "code",
    scope: "openid profile",
    state,
    nonce,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });
  return redirect(`${OIDC_AUTH}?${params}`, { "Set-Cookie": cookie(FLOW_COOKIE, flow, 600) });
}

async function exchangeCode(request, env, flow) {
  const url = new URL(request.url);
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    code: url.searchParams.get("code") || "",
    redirect_uri: callbackUrl(request),
    code_verifier: flow.verifier,
  });
  const authorization = btoa(`${env.TELEGRAM_CLIENT_ID}:${env.TELEGRAM_CLIENT_SECRET}`);
  const response = await fetch(OIDC_TOKEN, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded", Authorization: `Basic ${authorization}` },
    body,
  });
  if (!response.ok) throw new Error(`Telegram token exchange failed with ${response.status}`);
  return response.json();
}

async function verifyIdToken(token, env, nonce) {
  const parts = String(token || "").split(".");
  if (parts.length !== 3) throw new Error("Invalid Telegram ID token");
  const header = JSON.parse(decoder.decode(fromBase64url(parts[0])));
  const claims = JSON.parse(decoder.decode(fromBase64url(parts[1])));
  if (header.alg !== "RS256") throw new Error("Unsupported Telegram signing algorithm");
  const jwksResponse = await fetch(OIDC_JWKS, { cf: { cacheTtl: 3600, cacheEverything: true } });
  if (!jwksResponse.ok) throw new Error("Telegram signing keys unavailable");
  const jwks = await jwksResponse.json();
  const jwk = jwks.keys.find((candidate) => candidate.kid === header.kid && candidate.kty === "RSA");
  if (!jwk) throw new Error("Telegram signing key not found");
  const key = await crypto.subtle.importKey("jwk", jwk, { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" }, false, ["verify"]);
  const valid = await crypto.subtle.verify(
    "RSASSA-PKCS1-v1_5",
    key,
    fromBase64url(parts[2]),
    encoder.encode(`${parts[0]}.${parts[1]}`),
  );
  const now = Math.floor(Date.now() / 1000);
  const audience = Array.isArray(claims.aud) ? claims.aud : [claims.aud];
  if (!valid || claims.iss !== OIDC_ISSUER || !audience.map(String).includes(String(env.TELEGRAM_CLIENT_ID))) throw new Error("Telegram token validation failed");
  if (!claims.exp || claims.exp <= now || claims.iat > now + 60 || claims.nonce !== nonce) throw new Error("Telegram token expired or mismatched");
  return claims;
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
  const flow = await unseal(cookies(request)[FLOW_COOKIE], env.SESSION_SECRET);
  const now = Math.floor(Date.now() / 1000);
  if (!flow || flow.exp < now || flow.state !== url.searchParams.get("state")) return html("<h1>Kirjautuminen vanheni</h1><p>Aloita Telegram-kirjautuminen uudelleen.</p><a class=\"button\" href=\"/login\">Yritä uudelleen</a>", 400);
  try {
    const tokens = await exchangeCode(request, env, flow);
    const claims = await verifyIdToken(tokens.id_token, env, flow.nonce);
    if (!(await groupMember(claims.sub, env))) return html("<h1>Ei käyttöoikeutta</h1><p>Dashboard on vain Tietopolitiikka Hermes -superryhmän nykyisille jäsenille.</p>", 403);
    const session = await seal({ sub: String(claims.sub), name: claims.name || claims.preferred_username || "Telegram-jäsen", checked: now, exp: now + SESSION_SECONDS }, env.SESSION_SECRET);
    return redirect("/", { "Set-Cookie": cookie(SESSION_COOKIE, session, SESSION_SECONDS) });
  } catch (error) {
    return html(`<h1>Kirjautuminen epäonnistui</h1><p>${String(error.message || "Tuntematon virhe")}</p><a class=\"button\" href=\"/login\">Yritä uudelleen</a>`, 401);
  }
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

async function proxyDashboard(request, env, refreshed) {
  const incoming = new URL(request.url);
  const origin = new URL(env.HERMES_ORIGIN);
  origin.pathname = incoming.pathname;
  origin.search = incoming.search;
  const headers = new Headers(request.headers);
  headers.set("Authorization", `Basic ${btoa(`${env.ORIGIN_BASIC_AUTH_USERNAME}:${env.ORIGIN_BASIC_AUTH_PASSWORD}`)}`);
  headers.set("X-Forwarded-Host", incoming.host);
  headers.set("X-Forwarded-Proto", incoming.protocol.slice(0, -1));
  headers.delete("CF-Access-Client-Id");
  headers.delete("CF-Access-Client-Secret");
  if (env.CF_ACCESS_CLIENT_ID) headers.set("CF-Access-Client-Id", env.CF_ACCESS_CLIENT_ID);
  if (env.CF_ACCESS_CLIENT_SECRET) headers.set("CF-Access-Client-Secret", env.CF_ACCESS_CLIENT_SECRET);
  const upstream = await fetch(new Request(origin.toString(), {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
    redirect: "manual",
  }));
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("WWW-Authenticate");
  responseHeaders.set("Cache-Control", "no-store");
  if (refreshed) responseHeaders.append("Set-Cookie", refreshed);
  return new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers: responseHeaders });
}

function configurationReady(env) {
  return ["SESSION_SECRET", "TELEGRAM_CLIENT_ID", "TELEGRAM_CLIENT_SECRET", "TELEGRAM_BOT_TOKEN", "TELEGRAM_GROUP_ID", "HERMES_ORIGIN", "ORIGIN_BASIC_AUTH_USERNAME", "ORIGIN_BASIC_AUTH_PASSWORD"].every((key) => env[key]);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") return new Response(configurationReady(env) ? "ok" : "configuration incomplete", { status: configurationReady(env) ? 200 : 503 });
    if (!configurationReady(env)) return html("<h1>Tietopolitiikka Hermes</h1><p>Dashboardin turvallinen käyttöönotto on vielä kesken.</p>", 503);
    if (url.pathname === "/login") return beginLogin(request, env);
    if (url.pathname === "/oauth/callback") return finishLogin(request, env);
    if (url.pathname === "/logout") return redirect("/", { "Set-Cookie": cookie(SESSION_COOKIE, "", 0) });

    const auth = await loadSession(request, env);
    if (!auth.session) {
      if (auth.refreshed) return redirect("/login", { "Set-Cookie": auth.refreshed });
      return html("<h1>Tietopolitiikka Hermes</h1><p>Ryhmän yhteinen agentti, keskustelumuisti ja aineistot yhdessä paikassa.</p><a class=\"button\" href=\"/login\">Kirjaudu Telegramilla</a><p class=\"small\">Käyttöoikeus tarkistetaan yksityisen Telegram-superryhmän jäsenyydestä.</p>");
    }
    if (url.pathname === "/api/auth/me") return Response.json({ id: auth.session.sub, name: auth.session.name, member: true }, { headers: auth.refreshed ? { "Set-Cookie": auth.refreshed } : {} });
    return proxyDashboard(request, env, auth.refreshed);
  },
};
