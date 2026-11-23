# GEO content rewrite: making a page quotable by AI assistants

**Service:** I audit your key pages and rewrite them so ChatGPT, Gemini, Perplexity and Google AI Overviews can understand, trust and quote them.

**Demo (fictional brand "Mavi Kalem"):**

| Page | GEO readiness |
|---|---|
| [`pages/before.md`](pages/before.md): long brand story, no direct answers | **12 / 100** |
| [`pages/after.md`](pages/after.md): rewritten | **100 / 100** |

The score comes from eight transparent checks in [`geo_rewrite.py`](geo_rewrite.py):
direct answer up front, a clear "X is a ..." definition, numbers with a named source, question-style headings, an FAQ block, lists, short paragraphs and author attribution.

```bash
python geo_rewrite.py pages/before.md pages/after.md
pytest -q
```

**What a client receives:** audit score per page, a prioritised fix list, rewritten copy, and a re-score after the changes.

> The checks are a structured editorial checklist, not a guarantee of AI citations. Measured visibility is tracked separately (see `04-geo-monthly-tracking`).
