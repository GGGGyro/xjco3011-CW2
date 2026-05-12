# Coursework 2 Search Tool

This project is a baseline implementation of the COMP/XJCO3011 Coursework 2 search engine tool. It crawls the target website with `requests` and `BeautifulSoup`, builds an inverted index, saves and loads that index, and lets the user inspect postings or search for matching pages from a command-line shell.

## Project structure

```text
src/
  crawler.py
  indexer.py
  main.py
  models.py
  search.py
  storage.py
tests/
  test_crawler.py
  test_indexer.py
  test_search.py
  test_storage.py
data/
  quotes_index.json
```

## Features included in this baseline

- Crawl pages starting from `https://quotes.toscrape.com/`
- Respect a 6-second politeness window between requests
- Crawl the full site by default, with an optional page limit for local debugging
- Use the coursework-recommended `requests` + `BeautifulSoup` stack for fetching and parsing pages
- Build an inverted index containing word frequency and positions per page
- Save the index to `data/quotes_index.json`
- Load a previously saved index
- Print postings for a single word
- Find pages that contain all words in a query
- Support exact phrase searching with double quotes
- Rank query results with a TF-IDF style relevance score
- Handle empty queries and missing terms gracefully

## How to run

Run the interactive shell:

```bash
python -m src.main
```

Then use the required commands:

```text
build
load
print nonsense
find good friends
find "good friends"
help
exit
```

You can also run one command directly:

```bash
python -m src.main build
python -m src.main load
python -m src.main print nonsense
python -m src.main find good friends
python -m src.main find "\"good friends\""
```

## Local debugging

If you want a faster local crawl while testing, you can temporarily cap the number of crawled pages:

```bash
python -m src.main build 10
```

Use this only for local debugging. For coursework demonstrations and final outputs, the default `build` command should be used so the reachable site is crawled in full.

## Design notes

- The inverted index stores both term frequency and token positions so the same structure can support `print`, ranked keyword search, and exact phrase matching.
- Keyword results are ranked with a TF-IDF style score that combines per-page term frequency, page length, and document frequency.
- Exact phrase queries are detected with double quotes and matched using adjacent token positions in the postings lists.
- The crawler restricts traversal to the target domain, removes fragment identifiers, and applies a 6-second politeness delay between requests.

## Testing

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

## Notes

- Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

- For this workspace, third-party packages were installed into a local `.vendor/` directory so the project can use them without touching the global Python environment.
- Search results are ranked with a simple TF-IDF style score based on term frequency, page length, and document frequency.
- The crawler now reports how many pages were crawled, how many unique URLs were discovered, and any structured network errors.
- The optional `build [max_pages]` form is intended only for local testing; the default `build` command crawls the full reachable site.
