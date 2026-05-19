const textEncoder = new TextEncoder();
const textDecoder = new TextDecoder();

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders(request, env) });
    }

    try {
      if (url.pathname === "/auth/start") {
        return startAuth(request, env);
      }
      if (url.pathname === "/auth/callback") {
        return finishAuth(request, env);
      }
      if (url.pathname === "/api/preferences/pr" && request.method === "POST") {
        return createPreferencePullRequest(request, env);
      }

      return jsonResponse({ error: "not_found" }, 404, request, env);
    } catch (error) {
      return jsonResponse({ error: "server_error", message: error.message }, 500, request, env);
    }
  },
};

function corsHeaders(request, env) {
  const origin = request.headers.get("Origin");
  const allowedOrigin = env.BLOG_ORIGIN || "*";
  const headers = {
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };

  if (origin && (allowedOrigin === "*" || origin === allowedOrigin)) {
    headers["Access-Control-Allow-Origin"] = origin;
    headers["Access-Control-Allow-Credentials"] = "true";
  }

  return headers;
}

function jsonResponse(body, status, request, env, extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      ...corsHeaders(request, env),
      ...extraHeaders,
    },
  });
}

async function startAuth(request, env) {
  const url = new URL(request.url);
  const returnUrl = url.searchParams.get("return_url") || env.BLOG_ORIGIN || "https://bystander9.github.io/repositories/";
  const state = await signJson(
    {
      nonce: crypto.randomUUID(),
      return_url: returnUrl,
      exp: Math.floor(Date.now() / 1000) + 600,
    },
    env.SESSION_SECRET,
  );

  const authUrl = new URL("https://github.com/login/oauth/authorize");
  authUrl.searchParams.set("client_id", env.GITHUB_CLIENT_ID);
  authUrl.searchParams.set("redirect_uri", `${new URL(request.url).origin}/auth/callback`);
  authUrl.searchParams.set("scope", "public_repo");
  authUrl.searchParams.set("state", state);

  return Response.redirect(authUrl.toString(), 302);
}

async function finishAuth(request, env) {
  const url = new URL(request.url);
  const state = await verifySignedJson(url.searchParams.get("state") || "", env.SESSION_SECRET);
  if (!state || state.exp < Math.floor(Date.now() / 1000)) {
    return new Response("Invalid OAuth state", { status: 400 });
  }

  const code = url.searchParams.get("code");
  if (!code) {
    return new Response("Missing OAuth code", { status: 400 });
  }

  const tokenResponse = await fetch("https://github.com/login/oauth/access_token", {
    method: "POST",
    headers: {
      "Accept": "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      client_id: env.GITHUB_CLIENT_ID,
      client_secret: env.GITHUB_CLIENT_SECRET,
      code,
      redirect_uri: `${url.origin}/auth/callback`,
    }),
  });
  const tokenPayload = await tokenResponse.json();
  if (!tokenPayload.access_token) {
    return new Response("GitHub token exchange failed", { status: 401 });
  }

  const user = await githubFetch("https://api.github.com/user", tokenPayload.access_token);
  if (user.login !== env.ALLOWED_GITHUB_LOGIN) {
    return new Response("This GitHub user is not allowed to update this blog.", { status: 403 });
  }

  const session = await encryptJson(
    {
      login: user.login,
      access_token: tokenPayload.access_token,
      exp: Math.floor(Date.now() / 1000) + 60 * 60,
    },
    env.SESSION_SECRET,
  );
  const headers = new Headers();
  headers.set("Location", addReadyParam(state.return_url));
  headers.append("Set-Cookie", `repo_pr_session=${session}; HttpOnly; Secure; SameSite=None; Path=/; Max-Age=3600`);

  return new Response(null, { status: 302, headers });
}

async function createPreferencePullRequest(request, env) {
  const session = await readSession(request, env);
  if (!session) {
    const body = await safeJson(request);
    const returnUrl = body.return_url || `${env.BLOG_ORIGIN || "https://bystander9.github.io"}/repositories/`;
    const loginUrl = `${new URL(request.url).origin}/auth/start?return_url=${encodeURIComponent(returnUrl)}`;
    return jsonResponse({ error: "login_required", login_url: loginUrl }, 401, request, env);
  }

  const body = await safeJson(request);
  const hiddenRepositories = cleanRepositoryList(body.hidden_repositories || []);
  const owner = env.GITHUB_OWNER || "byStander9";
  const repo = env.GITHUB_REPO || "byStander9.github.io";
  const branch = env.GITHUB_BRANCH || "main";
  const path = "_data/repositories.json";
  const newBranch = `repo-preferences-${Date.now()}`;

  const baseRef = await githubFetch(`https://api.github.com/repos/${owner}/${repo}/git/ref/heads/${branch}`, session.access_token);
  await githubFetch(`https://api.github.com/repos/${owner}/${repo}/git/refs`, session.access_token, {
    method: "POST",
    body: {
      ref: `refs/heads/${newBranch}`,
      sha: baseRef.object.sha,
    },
  });

  const file = await githubFetch(
    `https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}?ref=${branch}`,
    session.access_token,
  );
  const config = JSON.parse(decodeBase64(file.content));
  config.hidden_repositories = hiddenRepositories;

  await githubFetch(`https://api.github.com/repos/${owner}/${repo}/contents/${encodeURIComponent(path)}`, session.access_token, {
    method: "PUT",
    body: {
      message: "Update repository visibility preferences",
      content: encodeBase64(JSON.stringify(config, null, 2) + "\n"),
      sha: file.sha,
      branch: newBranch,
    },
  });

  const pull = await githubFetch(`https://api.github.com/repos/${owner}/${repo}/pulls`, session.access_token, {
    method: "POST",
    body: {
      title: "Update repository visibility preferences",
      head: newBranch,
      base: branch,
      body: [
        "Updates `_data/repositories.json` from the blog repository UI.",
        "",
        "Repositories moved to Other:",
        ...hiddenRepositories.map((name) => `- ${name}`),
      ].join("\n"),
    },
  });

  return jsonResponse({ pull_request_url: pull.html_url, hidden_repositories: hiddenRepositories }, 200, request, env);
}

async function githubFetch(url, token, options = {}) {
  const response = await fetch(url, {
    method: options.method || "GET",
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
      "User-Agent": "bystander-github-pages-preferences",
      "X-GitHub-Api-Version": "2022-11-28",
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) {
    throw new Error(payload.message || `GitHub API failed: ${response.status}`);
  }
  return payload;
}

async function safeJson(request) {
  try {
    return await request.json();
  } catch (_error) {
    return {};
  }
}

function cleanRepositoryList(values) {
  return Array.from(new Set(values))
    .filter((value) => typeof value === "string")
    .map((value) => value.trim())
    .filter((value) => /^[A-Za-z0-9._-]+$/.test(value))
    .sort();
}

async function readSession(request, env) {
  const cookie = request.headers.get("Cookie") || "";
  const match = cookie.match(/(?:^|;\s*)repo_pr_session=([^;]+)/);
  if (!match) {
    return null;
  }

  const session = await decryptJson(match[1], env.SESSION_SECRET);
  if (!session || session.exp < Math.floor(Date.now() / 1000) || session.login !== env.ALLOWED_GITHUB_LOGIN) {
    return null;
  }
  return session;
}

async function signJson(payload, secret) {
  const body = base64UrlEncode(textEncoder.encode(JSON.stringify(payload)));
  const signature = await hmac(body, secret);
  return `${body}.${signature}`;
}

async function verifySignedJson(value, secret) {
  const parts = value.split(".");
  if (parts.length !== 2) {
    return null;
  }
  const expected = await hmac(parts[0], secret);
  if (expected !== parts[1]) {
    return null;
  }
  return JSON.parse(textDecoder.decode(base64UrlDecode(parts[0])));
}

async function hmac(value, secret) {
  const key = await crypto.subtle.importKey(
    "raw",
    textEncoder.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign("HMAC", key, textEncoder.encode(value));
  return base64UrlEncode(new Uint8Array(signature));
}

async function encryptJson(payload, secret) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await aesKey(secret);
  const encrypted = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    textEncoder.encode(JSON.stringify(payload)),
  );
  return `${base64UrlEncode(iv)}.${base64UrlEncode(new Uint8Array(encrypted))}`;
}

async function decryptJson(value, secret) {
  try {
    const [ivText, encryptedText] = value.split(".");
    const key = await aesKey(secret);
    const decrypted = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv: base64UrlDecode(ivText) },
      key,
      base64UrlDecode(encryptedText),
    );
    return JSON.parse(textDecoder.decode(decrypted));
  } catch (_error) {
    return null;
  }
}

async function aesKey(secret) {
  const digest = await crypto.subtle.digest("SHA-256", textEncoder.encode(secret));
  return crypto.subtle.importKey("raw", digest, "AES-GCM", false, ["encrypt", "decrypt"]);
}

function addReadyParam(returnUrl) {
  const url = new URL(returnUrl);
  url.searchParams.set("repo_pr_ready", "1");
  return url.toString();
}

function encodeBase64(value) {
  return btoa(unescape(encodeURIComponent(value)));
}

function decodeBase64(value) {
  return decodeURIComponent(escape(atob(value.replace(/\n/g, ""))));
}

function base64UrlEncode(bytes) {
  return btoa(String.fromCharCode(...bytes)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

function base64UrlDecode(value) {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(value.length / 4) * 4, "=");
  const binary = atob(normalized);
  return Uint8Array.from(binary, (char) => char.charCodeAt(0));
}
