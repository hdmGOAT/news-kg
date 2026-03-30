import argparse
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


class ParagraphExtractor(HTMLParser):
	def __init__(self) -> None:
		super().__init__()
		self._in_paragraph = False
		self._in_title = False
		self._skip_depth = 0
		self.paragraphs: list[str] = []
		self._current_paragraph: list[str] = []
		self.title_parts: list[str] = []

	def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
		if tag in {"script", "style", "noscript"}:
			self._skip_depth += 1
			return

		if self._skip_depth > 0:
			return

		if tag == "p":
			self._in_paragraph = True
			self._current_paragraph = []
		elif tag == "title":
			self._in_title = True

	def handle_endtag(self, tag: str) -> None:
		if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
			self._skip_depth -= 1
			return

		if self._skip_depth > 0:
			return

		if tag == "p" and self._in_paragraph:
			text = _normalize_whitespace("".join(self._current_paragraph))
			if text:
				self.paragraphs.append(text)
			self._in_paragraph = False
			self._current_paragraph = []
		elif tag == "title":
			self._in_title = False

	def handle_data(self, data: str) -> None:
		if self._skip_depth > 0:
			return

		if self._in_paragraph:
			self._current_paragraph.append(data)

		if self._in_title:
			self.title_parts.append(data)


def _normalize_whitespace(text: str) -> str:
	cleaned = unescape(text)
	cleaned = re.sub(r"\s+", " ", cleaned)
	return cleaned.strip()


def quick_scrape_url(url: str, timeout_seconds: float = 6.0, max_chars: int = 2400) -> dict[str, str | None]:
	if not url:
		return {"scraped_title": None, "scraped_text": None, "scrape_error": "missing_url"}

	request = Request(
		url,
		headers={
			"User-Agent": "news-kg-context-extractor/1.0",
			"Accept": "text/html,application/xhtml+xml",
		},
	)

	try:
		with urlopen(request, timeout=timeout_seconds) as response:
			content_type = response.headers.get("Content-Type", "")
			if "html" not in content_type.lower():
				return {
					"scraped_title": None,
					"scraped_text": None,
					"scrape_error": f"unsupported_content_type:{content_type}",
				}

			raw_html = response.read(450_000).decode("utf-8", errors="ignore")

	except Exception as exc:
		return {
			"scraped_title": None,
			"scraped_text": None,
			"scrape_error": f"request_failed:{type(exc).__name__}",
		}

	parser = ParagraphExtractor()
	try:
		parser.feed(raw_html)
		parser.close()
	except Exception as exc:
		return {
			"scraped_title": None,
			"scraped_text": None,
			"scrape_error": f"parse_failed:{type(exc).__name__}",
		}

	scraped_text = " ".join(parser.paragraphs)
	scraped_text = scraped_text[:max_chars].strip() if scraped_text else None
	scraped_title = _normalize_whitespace("".join(parser.title_parts)) or None

	return {
		"scraped_title": scraped_title,
		"scraped_text": scraped_text,
		"scrape_error": None,
	}


def build_article_context(article: dict[str, Any], timeout_seconds: float = 6.0) -> dict[str, Any]:
	title = article.get("title")
	description = article.get("description")
	content = article.get("content")
	url = article.get("url") or ""

	scrape = quick_scrape_url(url=url, timeout_seconds=timeout_seconds)

	context_parts = [
		title,
		description,
		content,
		scrape.get("scraped_text"),
	]
	merged_context = "\n\n".join(part for part in context_parts if isinstance(part, str) and part.strip())

	return {
		"source": article.get("source"),
		"title": title,
		"description": description,
		"content": content,
		"url": url,
		"scraped_title": scrape.get("scraped_title"),
		"scraped_text": scrape.get("scraped_text"),
		"scrape_error": scrape.get("scrape_error"),
		"context": merged_context,
	}


def extract_contexts_from_articles(
	articles: list[dict[str, Any]],
	timeout_seconds: float = 6.0,
	limit: int | None = None,
) -> list[dict[str, Any]]:
	selected_articles = articles[:limit] if limit and limit > 0 else articles
	return [build_article_context(article, timeout_seconds=timeout_seconds) for article in selected_articles]


def load_articles(file_path: Path) -> list[dict[str, Any]]:
	content = file_path.read_text(encoding="utf-8")
	data = json.loads(content)
	if not isinstance(data, list):
		raise ValueError(f"Expected a list of articles in {file_path}, got {type(data).__name__}")
	return data


def save_contexts(file_path: Path, contexts: list[dict[str, Any]]) -> None:
	file_path.parent.mkdir(parents=True, exist_ok=True)
	file_path.write_text(json.dumps(contexts, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
	project_root = Path(__file__).resolve().parents[1]
	default_input = project_root / "data" / "top_headlines_us.json"
	default_output = project_root / "data" / "top_headlines_us_context.json"

	parser = argparse.ArgumentParser(description="Extract context from articles + quick URL scrape.")
	parser.add_argument("--input", default=str(default_input), help="Path to input article JSON list")
	parser.add_argument("--output", default=str(default_output), help="Path to output context JSON list")
	parser.add_argument("--limit", type=int, default=None, help="Process only the first N articles")
	parser.add_argument("--timeout", type=float, default=6.0, help="Per-URL scrape timeout seconds")
	args = parser.parse_args()

	input_path = Path(args.input)
	output_path = Path(args.output)

	articles = load_articles(input_path)
	contexts = extract_contexts_from_articles(
		articles=articles,
		timeout_seconds=args.timeout,
		limit=args.limit,
	)
	save_contexts(output_path, contexts)

	print(f"Extracted {len(contexts)} contexts to {output_path}")


if __name__ == "__main__":
	main()