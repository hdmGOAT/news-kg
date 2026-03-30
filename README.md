# news-kg

Builds a news knowledge graph pipeline:

1. Scrape top headlines
2. Summarize article context
3. Perform Named Entity Recognition (NER)
4. Perform Relation Extraction
5. Build a Knowledge Graph in Neo4j

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

This creates the raw headline/article dataset used by downstream NLP stages.

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

## End-to-end pipeline

The project flow is:

`Headlines Scrape -> Summarization -> NER -> Relation Extraction -> Neo4j Knowledge Graph`

Current data artifacts in this repo:

- Raw headlines/articles: `data/top_headlines_us.json`
- Context-enriched records: `data/top_headlines_us_context.json`
