# LATENT CLEAN

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Discord API](https://img.shields.io/badge/Discord-API-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/developers/docs/intro)
[![License](https://img.shields.io/github/license/LattesGit/DM-Clean-Discord?style=flat-square)](https://github.com/LattesGit/DM-Clean-Discord/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-2ea44f?style=flat-square)](https://github.com/LattesGit/DM-Clean-Discord)

A fast command-line utility that deletes **your own** Discord messages across channels, DMs and servers. It runs as an interactive menu or fully scripted through command-line flags.

> **Read the [Important Notice](#important-notice) before using this tool.**

## Features

* Clean channels, all DMs / group DMs, one server, or every server
* **Dry run is the default** – nothing is deleted until you pass `--live`
* Proactive per-route rate-limit handling (reads Discord's headers, so far fewer `429`s)
* Automatic retries for network errors, `429` and `5xx`
* Filters: message age, keyword, keep pinned messages
* Channel and user whitelists
* Concurrent deletion with live progress bar and ETA
* Checkpoints and a failed-message list, so interrupted runs can be resumed
* Clean `Ctrl+C` shutdown
* Token is read from an environment variable / `.env` file, never hardcoded

## Installation

```bash
git clone https://github.com/LattesGit/DM-Clean-Discord.git
cd DM-Clean-Discord
pip install -r requirements.txt
```

Requires Python 3.9+.

## Setting your token

The tool looks for the token in this order:

1. The `DISCORD_TOKEN` environment variable
2. A `.env` file in the project folder
3. A hidden prompt when you start the program

Easiest setup:

```bash
cp .env.example .env
# then open .env and paste your token after DISCORD_TOKEN=
```

`.env` is already listed in `.gitignore`, so it will not be committed.

### How to get your token

Your user token is the `authorization` header your own browser sends to Discord. To read it from your own account:

1. Open **https://discord.com/app** in a desktop browser (Chrome, Edge or Firefox) and log in.
2. Press **F12** to open Developer Tools and go to the **Network** tab.
3. Type `api` into the filter box.
4. Click any channel or send a reaction so that new requests appear.
5. Click one of the requests to `discord.com/api/...`.
6. Under **Headers → Request Headers**, find `authorization`. The value is your token.
7. Paste it into your `.env` file.

**Treat the token like a password.**

* Anyone who has it has full access to your account, including without your password or 2FA.
* Never paste it into chats, issues, screenshots or commits. Nobody legitimate will ever ask you for it.
* If it leaks, **change your Discord password** – this invalidates the old token.
* Logging out of Discord in that browser also invalidates it, so copy a fresh one if the tool reports `401`.

## Usage

### Interactive menu

```bash
python3 main.py
```

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

### Command line

Always start with a dry run to see what would be removed, then add `--live`.

```bash
# preview everything in all DMs
python3 main.py --dm

# delete your messages in two channels
python3 main.py -c 123456789012345678 234567890123456789 --live

# one server, only messages older than 30 days, keep pinned, skip a channel
python3 main.py -g 345678901234567890 --older-than 30 --keep-pinned \
    --skip-channel 456789012345678901 --live

# all DMs except conversations with one person, no confirmation prompt
python3 main.py --dm --skip-user 567890123456789012 --live --yes

# continue an interrupted run
python3 main.py --dm --live --resume
```

| Flag | Description |
| ---- | ----------- |
| `-c, --channel ID...` | Clean these channel IDs |
| `--dm` | Clean all DMs and group DMs |
| `-g, --guild ID...` | Clean these server IDs |
| `--all-guilds` | Clean every server you are in |
| `--live` | Actually delete (default is dry run) |
| `--older-than DAYS` | Only messages older than N days |
| `--keyword TEXT` | Only messages containing TEXT |
| `--keep-pinned` | Never delete pinned messages |
| `-w, --workers N` | Delete workers, 1–10 (default 3) |
| `--skip-channel ID...` | Channels to skip |
| `--skip-user ID...` | Skip DMs with these users |
| `--resume` | Resume from the last checkpoint |
| `-y, --yes` | Skip the `YES` confirmation |

Defaults can also be edited at the top of `main.py` (`DRY_RUN`, `OLDER_THAN_DAYS`, `WORKERS`, `WHITELIST_CHANNELS`, `WHITELIST_USERS`, ...).

### Finding IDs

Enable **Settings → Advanced → Developer Mode** in Discord, then right-click a channel, server or user and choose **Copy ID**.

## Workers and rate limits

More workers do **not** bypass Discord's rate limits – deletes are limited per channel. Values of 2–3 are usually the sweet spot. The tool reads Discord's rate-limit headers and waits before it gets blocked; if a `429` still happens it waits for the server-provided time.

## Runtime files

| File | Purpose |
| ---- | ------- |
| `latent_clean_log.txt` | Runtime and error log |
| `latent_clean_failed.txt` | Messages that could not be deleted (`channel_id,message_id`) |
| `latent_clean_checkpoint.json` | Progress state used by `--resume` |

All three are in `.gitignore`. Failed messages can be retried from the menu (`5. Retry failed`).

## Important Notice

LATENT CLEAN authenticates with a **user token**, not a bot token. Automating a user account ("self-botting") **violates Discord's Terms of Service** and can lead to account restrictions or termination. Use it at your own risk, preferably on an account you can afford to lose, and only on messages you are authorized to manage.

Deleted messages cannot be recovered. The author is not responsible for account restrictions, data loss or any other consequences of using this software.

## Project Structure

```text
DM-Clean-Discord/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
