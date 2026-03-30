# news-kg

Fetches top headlines from NewsAPI, converts each item into typed Python models, and stores them as JSON.

## Setup

Create `.env` in project root:

```env
NEWS_API_KEY=your_newsapi_key_here
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python src/news_fetcher.py
```

## Output

The fetcher writes typed article records to:

- `data/top_headlines_us.json`

## Context extractor

Builds context records from each article's `title`, `description`, and `content`, then performs a quick scrape of the article `url` and appends scraped text.

```bash
python src/context_extractor.py
```

Optional args:

- `--input` path to article JSON list (default: `data/top_headlines_us.json`)
- `--output` path for context JSON (default: `data/top_headlines_us_context.json`)
- `--limit` process only first `N` articles
- `--timeout` scrape timeout per URL in seconds
