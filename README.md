# vinted-notifier

![logo](logo.svg)

Receive Apprise notifications when new Vinted items matching your criteria are added.

## Features

- Python-based executable with optional daemon mode
- Configurable `config.yaml` for Apprise targets, Vinted instances, notification formatting, and searches
- SQLite storage of already-notified items to avoid duplicates
- Supports Vinted instances like `.it`, `.fr`, `.com`, and more
- Parses Vinted catalog URLs and tracks items matching the search criteria
- Docker-ready `Dockerfile`

## Quickstart

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Customize `config.yaml` with your Apprise targets and query URLs.

3. Run once:

```bash
python -m vinted_notifier --config config.yaml --once
```

4. Run as a daemon:

```bash
python -m vinted_notifier --config config.yaml --daemon
```

## Configuration

The sample `config.yaml` includes:

- `apprise_urls`: list of Apprise URLs for notification targets
- `default_instance`: default Vinted locale to use when `instance` is not specified
- `database`: path to SQLite database file for notified item tracking
- `run_interval`: polling interval in seconds for daemon mode
- `notification.title`: title template using placeholders like `{query_name}`, `{title}`, `{brand}`, `{price}`, and `{url}`
- `notification.body`: body template for detailed notifications
- `queries`: list of tracked search URLs with optional `name` and `instance`

## Docker

Build and run with Docker:

```bash
docker build -t vinted-notifier .
docker run --rm -v "$PWD/config.yaml:/app/config.yaml" vinted-notifier
```

To run continuously, set the daemon environment variable in Docker:

```bash
docker run --rm -v "$PWD/config.yaml:/app/config.yaml" -e DAEMON=true -e RUN_INTERVAL=600 vinted-notifier
```

## Notes

- The project uses the Vinted catalog API to fetch search results.
- Only new item IDs are notified once and recorded in the SQLite database.
- You can track multiple search URLs and use separate Vinted instances per query.

## License

This project is licensed under the MIT License.
