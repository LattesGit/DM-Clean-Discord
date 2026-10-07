# LATENT CLEAN

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square\&logo=python\&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Discord-API-5865F2?style=flat-square\&logo=discord\&logoColor=white)](https://discord.com/developers/docs/intro)
[![License](https://img.shields.io/badge/License-MIT-2ea44f?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-2ea44f?style=flat-square)]()

**Discord message cleanup utility built with Python.**

LATENT CLEAN is a CLI tool for cleaning messages from Discord channels, DMs and servers through the Discord API.

Built for controlled cleanup with dry runs, filtering, whitelists, concurrent deletion, rate limit handling, retries and recovery.

## Features

* Channel-based message cleanup
* DM cleanup
* Server-wide cleanup
* Single-server cleanup
* Message age filtering
* Channel whitelists
* User whitelists
* Dry-run mode
* Concurrent deletion
* Rate-limit handling
* Automatic retries
* Failed deletion recovery
* Checkpoint system
* Live progress
* Runtime statistics
* Configurable workers
* Message type handling
* Interrupted-operation recovery

## Requirements

* Python 3.9+
* `requests`
* Discord account authentication token

Install the dependency:

```bash
pip install requests
```

## Setup

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/LATENT-CLEAN.git
cd LATENT-CLEAN
```

Configure `main.py`:

```python
TOKEN = "your_token_here"

WHITELIST_CHANNELS = []
WHITELIST_USERS = []

DRY_RUN = True
OLDER_THAN_DAYS = 0
WORKERS = 5
```

Run:

```bash
python3 main.py
```

## Configuration

| Option               | Description                                   |
| -------------------- | --------------------------------------------- |
| `TOKEN`              | Discord authentication token                  |
| `WHITELIST_CHANNELS` | Channels excluded from cleanup                |
| `WHITELIST_USERS`    | Users whose messages are excluded             |
| `DRY_RUN`            | Scan without deleting messages                |
| `OLDER_THAN_DAYS`    | Process messages older than the specified age |
| `WORKERS`            | Number of concurrent deletion workers         |

### Dry Run

Dry-run mode is enabled by default:

```python
DRY_RUN = True
```

LATENT CLEAN scans the selected locations and shows what would be deleted without modifying messages.

Live deletion should only be enabled after checking the selected targets and filters.

### Age Filter

Only process messages older than 30 days:

```python
OLDER_THAN_DAYS = 30
```

Set the value to `0` to disable the filter.

### Workers

Configure concurrent deletion workers:

```python
WORKERS = 5
```

The worker count affects request concurrency but does not bypass Discord API rate limits.

## Menu

```text
1. Clean channels by ID
2. Clean all DMs
3. Clean all servers
4. Clean one server
5. Retry failed
6. Statistics
7. Settings
0. Exit
```

## Rate Limits

LATENT CLEAN handles Discord API rate limits automatically.

When Discord responds with `429 Too Many Requests`, the program reads the provided retry interval and waits before continuing.

Global rate limits are handled as well.

## Failed Deletions

Failed deletions are stored locally:

```text
latent_clean_failed.txt
```

They can be retried without restarting the entire cleanup operation.

```text
5. Retry failed
```

## Checkpoints

Long-running operations maintain a local checkpoint:

```text
latent_clean_checkpoint.json
```

The checkpoint stores progress information so interrupted operations can be recovered.

## Runtime Files

| File                           | Purpose                 |
| ------------------------------ | ----------------------- |
| `latent_clean_log.txt`         | Runtime logs            |
| `latent_clean_failed.txt`      | Failed deletion records |
| `latent_clean_checkpoint.json` | Recovery state          |

These files are created automatically during execution.

## Security

Your Discord authentication token is highly sensitive.

Never commit it to GitHub or share it publicly.

```python
TOKEN = "your_token_here"
```

If a real token has been exposed, invalidate it immediately and generate a new one.

## Disclaimer

LATENT CLEAN uses a Discord user account authentication token rather than a standard Discord bot account.

Automating user accounts may violate Discord's Terms of Service. Use this project only with accounts and data you are authorized to manage.

The author is not responsible for account restrictions, deleted data or other consequences resulting from the use of this software.

## Project Structure

```text
LATENT CLEAN/
├── main.py
├── requirements.txt
├── LICENSE
└── README.md
```

## License

MIT License

See [`LICENSE`](LICENSE) for details.
