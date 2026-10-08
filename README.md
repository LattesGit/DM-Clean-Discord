# LATENT CLEAN

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square\&logo=python\&logoColor=white)](https://www.python.org/)
[![Discord API](https://img.shields.io/badge/Discord-API-5865F2?style=flat-square\&logo=discord\&logoColor=white)](https://discord.com/developers/docs/intro)
[![License](https://img.shields.io/github/license/LattesGit/DM-Clean-Discord?style=flat-square)](https://github.com/LattesGit/DM-Clean-Discord/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-2ea44f?style=flat-square)](https://github.com/LattesGit/DM-Clean-Discord)

A command-line Discord message cleanup utility written in Python.

LATENT CLEAN is designed for controlled message cleanup across Discord channels, DMs, and servers, with filtering, dry-run support, rate-limit handling, retries, checkpoints, and recovery features.

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
* Discord rate-limit handling
* Automatic retries
* Failed deletion recovery
* Checkpoint-based recovery
* Live progress tracking
* Runtime statistics
* Configurable workers
* Message type filtering
* Interrupted-operation recovery

## Requirements

* Python 3.9 or newer
* `requests`
* A Discord authentication token for an account you are authorized to manage

Install the dependency:

```bash
pip install -r requirements.txt
```

## Installation

Clone the repository:

```bash
git clone https://github.com/LattesGit/DM-Clean-Discord.git
cd DM-Clean-Discord
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Configure the values in `main.py`:

```python
TOKEN = "your_token_here"

WHITELIST_CHANNELS = []
WHITELIST_USERS = []

DRY_RUN = True
OLDER_THAN_DAYS = 0
WORKERS = 5
```

Run the program:

```bash
python3 main.py
```

## Configuration Options

| Option               | Description                                                   |
| -------------------- | ------------------------------------------------------------- |
| `TOKEN`              | Discord authentication token                                  |
| `WHITELIST_CHANNELS` | Channel IDs excluded from cleanup                             |
| `WHITELIST_USERS`    | User IDs whose messages are excluded                          |
| `DRY_RUN`            | Preview deletions without modifying messages                  |
| `OLDER_THAN_DAYS`    | Only process messages older than the specified number of days |
| `WORKERS`            | Number of concurrent workers                                  |

## Dry Run

Dry-run mode is enabled by default:

```python
DRY_RUN = True
```

When enabled, LATENT CLEAN scans the selected targets and reports messages that would be removed without performing deletions.

It is recommended to review the dry-run results before enabling live deletion.

## Age Filtering

To process only messages older than 30 days:

```python
OLDER_THAN_DAYS = 30
```

Set the value to `0` to disable age filtering:

```python
OLDER_THAN_DAYS = 0
```

## Workers

The number of concurrent workers can be configured with:

```python
WORKERS = 5
```

Increasing the worker count can improve throughput, but it does **not** bypass Discord API rate limits.

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

LATENT CLEAN handles Discord API rate-limit responses automatically.

When Discord returns:

```text
429 Too Many Requests
```

the program uses the server-provided retry interval before continuing.

Global rate-limit responses are handled as well.

## Failed Deletions

Failed deletion attempts are stored locally in:

```text
latent_clean_failed.txt
```

Failed operations can later be retried from the menu:

```text
5. Retry failed
```

This avoids having to restart the entire cleanup operation.

## Checkpoints

Long-running operations maintain a local checkpoint:

```text
latent_clean_checkpoint.json
```

The checkpoint stores operation progress and allows interrupted tasks to resume from their previous state.

## Runtime Files

| File                           | Purpose                     |
| ------------------------------ | --------------------------- |
| `latent_clean_log.txt`         | Runtime and error logs      |
| `latent_clean_failed.txt`      | Failed deletion records     |
| `latent_clean_checkpoint.json` | Recovery and progress state |

These files are generated automatically while the program is running.

## Security

Discord authentication tokens are highly sensitive credentials.

**Never commit a real token to GitHub or share it with anyone.**

Example:

```python
TOKEN = "your_token_here"
```

If a real token has been exposed, revoke it immediately and obtain a new credential.

For additional safety, make sure generated runtime files containing sensitive information are excluded from version control.

## Important Notice

LATENT CLEAN is designed around Discord user-account authentication rather than a standard Discord bot account.

Automating user accounts, including self-bot behavior, may violate Discord's Terms of Service and can result in account restrictions or termination.

Only use this software with accounts, servers, channels, and messages that you are authorized to manage.

The author is not responsible for account restrictions, data loss, deleted messages, or other consequences resulting from the use of this software.

## Project Structure

```text
DM-Clean-Discord/
├── main.py
├── requirements.txt
├── LICENSE
└── README.md
```

## License

This project is licensed under the MIT License.

See [`LICENSE`](LICENSE) for the full license text.
