# LATENT-CLEAN

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square\&logo=python\&logoColor=white)](https://www.python.org/)
[![Discord API](https://img.shields.io/badge/Discord-API-5865F2?style=flat-square\&logo=discord\&logoColor=white)](https://discord.com/developers/docs/intro)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success?style=flat-square)]()

A Python CLI utility for cleaning messages sent by your Discord account.

LATENT-CLEAN uses the Discord API directly and includes dry-run mode, message age filtering, concurrent deletion, rate-limit handling, retry support and checkpoint-based recovery.

## Features

* Clean messages from selected channels
* Clean messages from all accessible DMs
* Clean messages across servers
* Clean a single server
* Filter messages by age
* Dry-run mode
* Concurrent deletion
* Discord rate-limit handling
* Automatic retries
* Failed deletion recovery
* Checkpoint system
* Whitelisted channels
* Whitelisted users
* Live deletion progress
* Runtime statistics
* Configurable worker count
* Supports Discord message types commonly used for normal messages and threads

## Requirements

* Python 3.9+
* A Discord account
* Discord authentication token
* Internet connection

Install the required dependency:

```bash
pip install requests
```

## Configuration

Open the script and configure:

```python
TOKEN = "YOUR_TOKEN_HERE"

WHITELIST_CHANNELS = []
WHITELIST_USERS = []

DRY_RUN = True
OLDER_THAN_DAYS = 0
WORKERS = 5
```

### Options

| Setting              | Description                                                   |
| -------------------- | ------------------------------------------------------------- |
| `TOKEN`              | Discord authentication token                                  |
| `WHITELIST_CHANNELS` | Channel IDs that should never be cleaned                      |
| `WHITELIST_USERS`    | User IDs whose messages should be excluded                    |
| `DRY_RUN`            | Scan without deleting messages                                |
| `OLDER_THAN_DAYS`    | Only process messages older than the specified number of days |
| `WORKERS`            | Number of concurrent deletion workers                         |

## Usage

Run the script with:

```bash
python3 latent-clean.py
```

The main menu provides:

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

## Dry Run

Dry-run mode is enabled by default.

```python
DRY_RUN = True
```

When enabled, LATENT-CLEAN scans the selected locations and reports the messages that would be removed without actually deleting them.

Live deletion requires confirmation before execution.

## Age Filter

Set `OLDER_THAN_DAYS` to limit deletion by message age.

```python
OLDER_THAN_DAYS = 30
```

A value of `0` disables the age filter.

## Performance

Deletion uses a configurable thread pool:

```python
WORKERS = 5
```

The worker count can be changed from the settings menu.

The CLI displays:

* Progress
* Completed deletions
* Failed deletions
* Messages per second
* Rate-limit events

## Rate Limits

Discord API rate limits are handled automatically.

LATENT-CLEAN detects HTTP `429` responses, reads the API-provided retry interval and waits before continuing.

Global rate limits are also tracked.

## Failed Messages

Failed deletions are stored in:

```text
latent_clean_failed.txt
```

They can later be retried from the main menu.

## Checkpoints

Long-running operations periodically save their state to:

```text
latent_clean_checkpoint.json
```

The checkpoint contains progress information such as completed channels and operation statistics.

If the process stops unexpectedly, the saved state can be loaded when the program starts again.

## Runtime Files

| File                           | Purpose                         |
| ------------------------------ | ------------------------------- |
| `latent_clean_log.txt`         | Runtime log                     |
| `latent_clean_failed.txt`      | Failed message deletion records |
| `latent_clean_checkpoint.json` | Operation checkpoint            |

These files are generated during execution.

## Security

Do not publish your Discord authentication token.

Never commit a real token to GitHub.

Use:

```python
TOKEN = "put your token here"
```

If a real token has been exposed, revoke it immediately and generate a new one.

## Disclaimer

LATENT-CLEAN interacts with Discord using a user account authentication token rather than a standard Discord bot account.

Using automation with a user account may violate Discord's Terms of Service. Use this project only on accounts and data you are authorized to manage.

The project is provided for educational and personal use. You are responsible for how you use it.

## License

This project is licensed under the MIT License.

See [LICENSE](LICENSE) for details.
