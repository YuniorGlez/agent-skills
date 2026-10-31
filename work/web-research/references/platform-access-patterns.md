# Platform Access Patterns (Bot Detection)

## Tested: July 2026

### Blocked by Bot Detection (Automated Browser)

| Platform | Detection Type | Notes |
|----------|---------------|-------|
| Google | CAPTCHA/sorry page | IP-based block, immediate on search |
| Bing | Cloudflare challenge | Checkbox "verify you are human" |
| DuckDuckGo | CAPTCHA | "Select all squares containing a duck" |
| Brave Search | Slider challenge | "Drag the slider" bot check |
| Yahoo Search | "Temporary problems searching" | Soft block, no CAPTCHA shown |
| Reddit (new) | JS challenge redirect | Redirects to challenge page |
| Reddit (old) | JS challenge redirect | Same as new Reddit; `.json` endpoints also wall even with a browser User-Agent |
| Arctic Shift mirror | ✅ WORKS | `arctic-shift.photon-reddit.com/api/comments/tree?link_id=t3_<id>&limit=N` — full comment tree as JSON, no auth; the reliable route to Reddit content |
| OpenAI blog | Cloudflare challenge | Blocks automated access |
| X/Twitter search | Login wall | Requires authenticated session |
| Bluesky search | Login wall | "Search not available when logged out" |
| Nitter instances | 403 Forbidden | nitter.poast.org blocked |

### Accessible Without Login

| Platform | Method | Notes |
|----------|--------|-------|
| The Verge | Direct navigation + site search | Works well, has good AI coverage |
| TechCrunch | Direct navigation + site search | Works, shows "no results" for niche queries |
| Tom's Guide | Direct navigation + site search | Works, broader consumer focus |
| Hacker News (Algolia) | hn.algolia.com search | Rarely blocks, good for tech/AI topics |
| X/Twitter (profiles) | Direct profile URL | Some profile info visible without login |
| X/Twitter (specific tweets) | Direct tweet URL | May show 404 if tweet doesn't exist or is deleted |
| 404 Media | Direct navigation | Works, niche investigative tech journalism |
| GitHub (public issues/PRs) | web_extract on the issue URL | Full body + comment thread extract cleanly; read-only — posting goes through `gh` |

### Recommended First-Attack Order

1. **hn.algolia.com** — fastest, rarely blocks, good for tech/AI
2. **The Verge /search?q=** — reliable, good AI coverage
3. **TechCrunch /?s=** — reliable, startup/AI focus
4. **Direct URL** to known article — if you have a hunch about the URL pattern
5. **curl** to public endpoints — bypasses browser detection entirely
6. **Search engines** — expect failure, use only as last resort
