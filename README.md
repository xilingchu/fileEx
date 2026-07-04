# File Extraordinary Manager (FileEM)

File Extraordinary Manager is a Python package, backed by SQLite, that helps you manage
files on your computer from the terminal instead of clicking around in a file manager.

It's for you if you've ever asked:

1. Why should I click through folders with my mouse when I just want to open a file?
2. How can I sort my files in a smarter way?
3. How do I get more out of my computer's terminal?

FileEM is plugin-based. It currently ships one plugin, `wos`, which manages a personal
library of academic papers: it indexes PDFs in a SQLite database, looks up
bibliographic metadata, and opens the matching PDF in your viewer of choice.

> The plugin is named `wos` after Web of Science, which is where it originally pulled
> metadata from. That access was later lost, so it was switched to the
> [Semantic Scholar API](https://api.semanticscholar.org) instead — the name stuck.

## Installation

```bash
git clone https://github.com/xilingchu/fileEM.git
cd fileEM
pip install .
```

This installs the `fileEm` package and the `fileEm` command-line script. It also
copies the default config files into `~/.config/fileEm/` (only files that don't
already exist there are copied, so re-installing/upgrading won't clobber your
settings).

## Configuration

FileEM reads its top-level config from `~/.config/fileEm/config.yaml` (falling back to
the package's bundled default if that file is missing, e.g. when running from source).
Each top-level key enables a plugin and is passed as keyword arguments to that
plugin's handler.

```yaml
wos:
  sql_path: '~/.config/fileEm/wos/wos.yaml'
  viewer: okular
  url: 'https://api.openai.com/v1'
  api: 'sk-...'
  model: 'gpt-4o-mini'
```

- `sql_path` — path to the YAML schema describing the SQLite tables used by the
  `wos` plugin (default schema at `~/.config/fileEm/wos/wos.yaml`, copied from
  `fileEM/config/wos/wos.yaml` at install time: `Journal_articles`, `Author`,
  `Journal`).
- `viewer` — the command used to open a matched PDF (e.g. `okular`, `evince`, `open`).
- `url`, `api`, `model` — connection details for an OpenAI-compatible endpoint, used
  to extract a paper's DOI from its PDF text when adding a new article.

The `wos` plugin also uses the `S2_API_KEY` environment variable, if set, to query the
[Semantic Scholar API](https://api.semanticscholar.org) (an API key raises your rate
limit but is not required).

## Usage

### Add a paper

```bash
fileEm wos add -f /path/to/paper.pdf
```

This extracts text from the first pages of the PDF, asks the configured LLM to pull
out the DOI, fetches the paper's metadata from Semantic Scholar, and stores it (title,
authors, journal, year, abstract, path, etc.) in the local SQLite database.

### Query your library

```bash
fileEm wos query -a "Author Name" -t "some words in the title" -j "Journal Name" -p 2018 2022
```

Available filters:

| Flag | Description |
|------|-------------|
| `-a`, `--author`   | One or more author names |
| `-t`, `--title`    | One or more words in the title |
| `-j`, `--journal`  | Journal name |
| `-f`, `--fields`   | One or more fields of study |
| `-p`, `--pubyear`  | Publication year range, e.g. `2018 2022` |

- No matches: prints `No match returns!`.
- One match: opens it directly in your configured `viewer`.
- Multiple matches: lists them and prompts you to pick one to open.

## Project layout

```
fileEM/
├── app/
│   └── wos/            # Web of Science plugin (add/query papers)
├── chatgpt/            # Minimal OpenAI-compatible client used for DOI extraction
├── config/             # Default config.yaml and per-plugin schemas
├── sql/                # Generic SQLite operation helpers
└── utils/              # Path and misc utilities
scripts/fileEm           # CLI entry point
```

## License

MIT — see [LICENSE.txt](LICENSE.txt).
