import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from dotenv import load_dotenv
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://newsapi.org/v2/top-headlines"
DEFAULT_COUNTRY = "us"


@dataclass
class Source:
	id: str | None
	name: str


@dataclass
class Article:
	source: Source
	author: str | None
	title: str
	description: str | None
	url: str
	urlToImage: str | None
	publishedAt: str
	content: str | None


def fetch_top_headlines(country: str = DEFAULT_COUNTRY) -> dict:
	project_root = Path(__file__).resolve().parents[1]
	load_dotenv(project_root / ".env")

	api_key = os.getenv("NEWS_API_KEY")
	if not api_key:
		raise RuntimeError(
			"Missing NEWS_API_KEY. Set it in your environment or in "
			"the project .env file."
		)

	query = urlencode({"country": country, "apiKey": api_key})
	url = f"{BASE_URL}?{query}"

	request = Request(url, headers={"User-Agent": "news-kg/1.0"})
	with urlopen(request, timeout=15) as response:
		payload = response.read().decode("utf-8")
		return json.loads(payload)


def parse_articles(payload: dict[str, Any]) -> list[Article]:
	raw_articles = payload.get("articles", [])
	articles: list[Article] = []

	for raw in raw_articles:
		raw_source = raw.get("source") or {}
		source = Source(
			id=raw_source.get("id"),
			name=raw_source.get("name") or "",
		)

		article = Article(
			source=source,
			author=raw.get("author"),
			title=raw.get("title") or "",
			description=raw.get("description"),
			url=raw.get("url") or "",
			urlToImage=raw.get("urlToImage"),
			publishedAt=raw.get("publishedAt") or "",
			content=raw.get("content"),
		)
		articles.append(article)

	return articles


def store_articles(articles: list[Article], output_path: Path) -> None:
	output_path.parent.mkdir(parents=True, exist_ok=True)
	serialized = [asdict(article) for article in articles]
	output_path.write_text(
		json.dumps(serialized, indent=2, ensure_ascii=False),
		encoding="utf-8",
	)


def main() -> None:
	project_root = Path(__file__).resolve().parents[1]
	payload = fetch_top_headlines(country=DEFAULT_COUNTRY)
	articles = parse_articles(payload)

	output_file = project_root / "data" / f"top_headlines_{DEFAULT_COUNTRY}.json"
	store_articles(articles, output_file)

	print(f"Stored {len(articles)} typed articles to {output_file}")


if __name__ == "__main__":
	main()