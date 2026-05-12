# Coursework 2 Search Tool

This project is a baseline implementation of the COMP/XJCO3011 Coursework 2 search engine tool. It crawls the target website, builds an inverted index, saves and loads that index, and lets the user inspect postings or search for matching pages from a command-line shell.

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
- Build an inverted index containing word frequency and positions per page
- Save the index to `data/quotes_index.json`
- Load a previously saved index
- Print postings for a single word
- Find pages that contain all words in a query
- Support exact phrase searching with double quotes
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

## Testing

Run the unit tests with:

```bash
python -m unittest discover -s tests -v
```

## Notes

- This baseline uses only the Python standard library so that it can run without third-party dependencies.
- For a stronger final submission, you can later replace or extend the crawler with `requests` and `BeautifulSoup` as recommended in the brief.
