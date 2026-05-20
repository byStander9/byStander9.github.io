# byStander9.github.io

GitHub Pages 기반 개인 블로그 저장소.

## Repository post automation

`scripts/generate_repo_posts.py` reads public repositories from `byStander9`, checks README and repository files, and creates generated posts in `_posts`.

- Home pinned repositories are read from the GitHub profile pinned repositories through GraphQL.
- `featured_repositories` is only a fallback when the GitHub pinned repository lookup is unavailable.
- `hidden_repositories` is excluded from generated posts and separated on `/repositories/`.
- `excluded_repositories` is ignored entirely.
- Existing manual posts are preserved while `keep_manual_posts` is `true`.

Example:

```json
"hidden_repositories": ["repo-you-do-not-want-on-the-blog"]
```

Run locally:

```bash
python scripts/generate_repo_posts.py
```

GitHub Actions refreshes generated posts every day and can also be run manually from the Actions tab.

## AI enrichment

The generator can create richer Korean README drafts and blog post bodies through either Codex CLI subscription auth or the OpenAI Responses API.

- Configure it in `_data/repositories.json` under `ai_enrichment`.
- `provider: "codex_cli"` uses your local Codex login/subscription through `codex exec`.
- `provider: "openai_api"` uses `OPENAI_API_KEY` and API billing.
- README drafts are written to `repo-readmes/`.
- Generated posts link to the README draft with `readme_draft_url`.
- `max_repositories_per_run` limits API usage each scheduled run.
- If the configured provider is unavailable, the script falls back to the rule-based generator.

For local subscription-backed enrichment:

```bash
codex login
python scripts/generate_repo_posts.py
```

The default model is `gpt-5.4-mini`, chosen as a lower-cost model for periodic writing work. Override it with the `OPENAI_MODEL` environment variable if needed.

## Browser-managed repository display

The `/repositories/` page lets the blog owner move repositories into an Other folder from the browser UI. Pinned repositories come from the GitHub profile pinned repositories.

There are two layers:

- Local browser preference: saved in `localStorage`, instant, no login required.
- Persistent PR workflow: signs in with GitHub and opens a pull request that updates `_data/repositories.json`.

This can run on free tiers for a personal blog:

- GitHub Pages hosts the static blog.
- GitHub OAuth and GitHub REST API create the branch, commit, and pull request.
- Cloudflare Workers Free can host the tiny OAuth/API backend for low personal traffic.

```text
┌────────────────────────────────────────────────────────────────┐
│ Browser: https://bystander9.github.io/repositories/             │
│                                                                │
│  GitHub profile pinned repos -> Pinned Repositories            │
│  [x] repo-b -> Other                                           │
│  [PR 생성]                                                     │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                │ POST /api/preferences/pr
                                ▼
┌────────────────────────────────────────────────────────────────┐
│ Cloudflare Worker                                              │
│ workers/repo-preference-pr-worker.js                           │
│                                                                │
│  1. Checks session cookie                                      │
│  2. Redirects to GitHub OAuth if login is needed               │
│  3. Allows only ALLOWED_GITHUB_LOGIN                           │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                │ GitHub OAuth
                                ▼
┌────────────────────────────────────────────────────────────────┐
│ GitHub                                                         │
│                                                                │
│  1. User signs in as byStander9                                │
│  2. Worker creates a new branch                                │
│  3. Worker edits _data/repositories.json                       │
│  4. Worker opens a pull request                                │
└───────────────────────────────┬────────────────────────────────┘
                                │
                                │ Merge PR
                                ▼
┌────────────────────────────────────────────────────────────────┐
│ GitHub Pages                                                   │
│                                                                │
│  1. Rebuilds the blog                                          │
│  2. GitHub profile pinned repos appear as Pinned Repositories  │
│  3. hidden_repositories appear in Other only                   │
└────────────────────────────────────────────────────────────────┘
```

### Worker setup

1. Create a GitHub OAuth App.
   - Homepage URL: `https://bystander9.github.io`
   - Authorization callback URL: `https://YOUR_WORKER_DOMAIN/auth/callback`
2. Deploy `workers/repo-preference-pr-worker.js` to Cloudflare Workers.
3. Copy `workers/wrangler.example.toml` to `workers/wrangler.toml` and adjust the Worker name/domain.
4. Set Worker secrets:

```bash
wrangler secret put GITHUB_CLIENT_ID
wrangler secret put GITHUB_CLIENT_SECRET
wrangler secret put SESSION_SECRET
```

5. Set `_config.yml`:

```yaml
repo_pr_worker_url: "https://YOUR_WORKER_DOMAIN"
```

The Worker only accepts the GitHub login configured by `ALLOWED_GITHUB_LOGIN`, then creates a PR instead of pushing directly to `main`.
