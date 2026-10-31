# Digital Book Acquisition Research

> Tested: July 2026

Finding digital copies of books the user already owns physically, or buying new ebook copies.

## Pragmatic Approach

If the user says they own a physical copy and wants the digital version:
- Do NOT lecture about copyright — they already paid for the content
- DO be pragmatic: find where to buy the ebook, or find the text via legitimate means
- The user just wants convenience (reading on phone/tablet) or wants the agent to have the text for Q&A

## OpenLibrary API (Best Source for Book Metadata)

OpenLibrary rarely blocks automated access and is the best source for discovering editions, ISBNs, and publication info.

### Work search
```bash
curl -sL -A "Mozilla/5.0" "https://openlibrary.org/search.json?q=4+hour+workweek"
```
Returns work keys like `/works/OL3353439W`. To filter by author+title:
```bash
curl -sL -A "Mozilla/5.0" "https://openlibrary.org/search.json?q=author:%22Tim+Ferriss%22+title:%224-Hour+Workweek%22"
```

### Editions lookup (from work key)
```bash
curl -sL -A "Mozilla/5.0" "https://openlibrary.org/works/OL3353439W/editions.json?limit=30"
```
Returns all editions with ISBNs, publishers, languages, publish dates. Use `offset` for pagination when there are many editions: `?limit=30&offset=10`.

### Direct ISBN lookup
```bash
curl -sL -A "Mozilla/5.0" "https://openlibrary.org/isbn/9788490567470.json"
```

### Key data points to extract (Python one-liner)
```bash
curl -sL -A "Mozilla/5.0" "https://openlibrary.org/works/OL3353439W/editions.json?limit=10" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for e in d.get('entries',[]):
    isbns = e.get('isbn_13',[]) or e.get('isbn_10',[]) or []
    print(f'Edition: {e.get(\"title\",\"?\")} | ISBN: {isbns} | Year: {e.get(\"publish_date\",\"?\")} | Publisher: {e.get(\"publishers\",[\"?\"])}')"
```

### Key data points to extract
- ISBN-13 (for purchasing) — in `isbn_13` array, or fallback to `isbn_10`
- Publisher and publish date
- Language code
- Number of pages
- **Note**: OpenLibrary's `editions.json` groups ALL language editions — Spanish, English, German, etc. Scan the full list.

## Amazon (by region)

- **Amazon.es** (Spanish): works without login for browsing product pages (`/dp/{ISBN10}`), less aggressive bot detection than .com
- **Amazon.com** (English): typically blocked by bot detection for automated browsers — returns "Documento no encontrado"
- Navigate to `/dp/{ISBN10}` or search by ISBN directly
- **Amazon.es uses regional redirect** — URLs like `/ap/signin` redirect to `/ax/claim` then block with cookie errors

### Amazon Login Limitation (Headless Browser)

**Amazon will NOT accept login from headless browsers.** Even after clicking "Aceptar" on the cookies banner, the login silently fails with "Habilita las cookies para continuar" (hidden in the DOM). This is a fundamental limitation — Amazon requires full browser cookie persistence that headless sessions cannot maintain.

**PITFALL**: Do NOT retry Amazon login in the headless browser. After 1-2 attempts showing the same password form without progress, pivot immediately. The password IS being read (it shows as •••) but Amazon's JS authentication pipeline requires persistent cookies.

### When You Need the Book's Text (Agent Q&A Workflow)

User owns physical copy → wants agent to read the full text for Q&A:

1. **Find the Kindle edition** via OpenLibrary API (get ISBN-13)
2. **Direct user to buy** at Amazon.es using `/dp/{ISBN10}` link — Kindle price is typically 40-50% of paperback
3. **Cannot log in to download** due to headless browser limitation → ask user to:
   - Open Amazon app on their **phone** (where they're already logged in)
   - Go to "Mi cuenta" → "Gestionar contenido y dispositivos"
   - Select the book → "Descargar y transferir a USB" → downloads .azw3 file
   - Upload the file to Google Drive/Dropbox and share the link
4. **Once you have the file**, convert with Calibre (free: calibre-ebook.com):
   - Install: `brew install calibre` or download from website
   - Convert: `ebook-convert book.azw3 book.txt`
5. Feed the .txt to the agent context

Amazon Kindle pricing example (Spanish, July 2026):
- Kindle: 9,49€ (0€ with Kindle Unlimited)
- Audiolibro: 0€ with trial
- Tapa blanda: 19,85€

## Platforms That Block

- **Google Books**: inconsistent, some previews accessible, many blocked
- **Casa del Libro**: Access Denied (aggressive bot detection)
- **Goodreads**: 403 Forbidden