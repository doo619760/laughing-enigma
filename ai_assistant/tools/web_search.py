"""Web search tool - search the web and fetch page content."""

import json
import re
import urllib.request
import urllib.parse
import urllib.error
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    """Extract visible text from HTML."""

    def __init__(self):
        super().__init__()
        self.result = []
        self._skip = False
        self._skip_tags = {"script", "style", "head", "meta", "link"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False
        if tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "tr"):
            self.result.append("\n")

    def handle_data(self, data):
        if not self._skip:
            text = data.strip()
            if text:
                self.result.append(text + " ")

    def get_text(self):
        raw = "".join(self.result)
        # Collapse whitespace
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        raw = re.sub(r"[ \t]+", " ", raw)
        return raw.strip()


def fetch_url(url: str, max_chars: int = 5000) -> str:
    """Fetch a URL and extract readable text content."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AI-Assistant/1.0 (Educational Tool)",
                "Accept": "text/html,application/xhtml+xml,text/plain",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read(200_000).decode("utf-8", errors="replace")

            if "text/plain" in content_type:
                text = data
            elif "application/json" in content_type:
                try:
                    parsed = json.loads(data)
                    text = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    text = data
            else:
                extractor = _TextExtractor()
                extractor.feed(data)
                text = extractor.get_text()

            if len(text) > max_chars:
                text = text[:max_chars] + f"\n\n... (truncated, {len(data):,} chars total)"

            return f"Content from {url}:\n\n{text}"

    except urllib.error.HTTPError as e:
        return f"HTTP Error {e.code}: {e.reason} for URL: {url}"
    except urllib.error.URLError as e:
        return f"URL Error: {e.reason} for URL: {url}"
    except Exception as e:
        return f"Error fetching URL: {e}"


def search_web(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo's HTML interface."""
    try:
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "AI-Assistant/1.0 (Educational Tool)",
                "Accept": "text/html",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read(500_000).decode("utf-8", errors="replace")

        # Parse results from DuckDuckGo HTML
        results = []
        # Find result links and snippets
        link_pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', re.DOTALL
        )
        snippet_pattern = re.compile(
            r'class="result__snippet"[^>]*>(.*?)</(?:a|span|td|div)', re.DOTALL
        )

        links = link_pattern.findall(html)
        snippets = snippet_pattern.findall(html)

        for i, (href, title) in enumerate(links[:num_results]):
            title_clean = re.sub(r"<[^>]+>", "", title).strip()
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""

            # Decode DuckDuckGo redirect URL
            if "uddg=" in href:
                match = re.search(r"uddg=([^&]+)", href)
                if match:
                    href = urllib.parse.unquote(match.group(1))

            results.append(f"{i + 1}. {title_clean}\n   {href}\n   {snippet}")

        if results:
            return f"Search results for '{query}':\n\n" + "\n\n".join(results)
        else:
            return f"No results found for '{query}'. Try rephrasing your search."

    except Exception as e:
        return f"Search error: {e}. Try fetching a specific URL instead."


TOOL_DEFINITION = {
    "name": "web_search",
    "description": (
        "Search the web or fetch content from URLs. Use 'search' to find information "
        "on the web, or 'fetch' to get the content of a specific webpage."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["search", "fetch"],
                "description": "'search' to search the web, 'fetch' to get a URL's content",
            },
            "query": {
                "type": "string",
                "description": "Search query (for 'search') or URL (for 'fetch')",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of search results to return (default: 5)",
            },
        },
        "required": ["action", "query"],
    },
}


def handle(input_data: dict) -> str:
    """Handle a tool call from the API."""
    action = input_data["action"]
    query = input_data["query"]

    if action == "search":
        return search_web(query, input_data.get("num_results", 5))
    elif action == "fetch":
        return fetch_url(query)
    else:
        return f"Error: Unknown action '{action}'"
