# LATENT CLEAN

**Discord Message Management CLI**

[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Discord](https://img.shields.io/badge/Platform-Discord-5865F2?style=flat-square&logo=discord&logoColor=white)](https://discord.com/)
[![License](https://img.shields.io/github/license/LattesGit/DM-Clean-Discord?style=flat-square)](LICENSE)
[![Repository](https://img.shields.io/badge/Interface-CLI-30363D?style=flat-square&logo=gnubash&logoColor=white)](https://github.com/LattesGit/DM-Clean-Discord)

A command-line utility for reviewing and managing your own Discord messages with filtering, progress tracking, checkpoints, and configurable execution options.

LATENT CLEAN provides an interactive menu and command-line interface, with a dry-run mode intended to help you review an operation before making changes.

> [!CAUTION]
> **Read the Security and Compatibility Notice before using this project.**
>
> This project describes user-account automation. Automating normal user accounts (self-botting) is prohibited by Discord's Terms of Service and may result in account restrictions or termination. This README does not imply that the project is officially supported by Discord.

---

## Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command-Line Options](#command-line-options)
- [Filtering and Execution](#filtering-and-execution)
- [Rate Limits and Reliability](#rate-limits-and-reliability)
- [Runtime Files](#runtime-files)
- [Security and Compatibility Notice](#security-and-compatibility-notice)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Interactive CLI** — navigate operations through a menu.
- **Command-line execution** — configure supported operations using flags.
- **Dry-run mode** — preview intended operations before execution.
- **Filtering** — filter by message age and keyword.
- **Pinned-message protection** — optionally exclude pinned messages.
- **Channel and user exclusions** — configure skip lists.
- **Progress tracking** — display progress and estimated completion time.
- **Checkpoint support** — preserve progress for supported interrupted operations.
- **Retry support** — review and retry recorded failures.
- **Rate-limit awareness** — respect server-provided rate-limit information.
- **Error handling** — handle supported network errors and transient server failures.
- **Environment-based configuration** — keep credentials out of source files.
- **Interrupt handling** — handle Ctrl+C during execution.

> Feature availability and behavior depend on the implementation in the current version of `main.py`. Verify each option before relying on it.

## Requirements

- Python 3.9 or newer
- Git
- Internet connectivity
- Dependencies listed in `requirements.txt`

## Installation

Clone the repository and install its dependencies:

```bash
git clone https://github.com/LattesGit/DM-Clean-Discord.git
cd DM-Clean-Discord
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

Verify the Python version:

```bash
python --version
```

## Configuration

LATENT CLEAN documents environment-based configuration for supported settings.

Create a local environment file if the project provides `.env.example`:

```bash
cp .env.example .env
```

Keep `.env` local and make sure it is excluded by `.gitignore`.

### Credential safety

- Never commit credentials, session tokens, or `.env` files.
- Never share authentication headers in screenshots, issue reports, or logs.
- Do not use tokens obtained from another person's browser or account.
- Do not assume that storing a token in `.env` makes an unsupported authentication method safe or compliant.
- If a credential may have been exposed, secure the affected account and follow the provider's current credential-revocation guidance.

**Important:** Environment-variable support is a configuration mechanism, not an endorsement of user-token automation. Prefer official, documented Discord API authentication and supported bot functionality.

## Usage

### Interactive menu

Start the application:

```bash
python3 main.py
```

The documented menu includes the following entries:

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

Menu options may vary by version. Consult the source code if an entry behaves differently.

### Command-line interface

Use the built-in help output to inspect the options supported by your installed version:

```bash
python3 main.py --help
```

If the implementation supports dry-run previews, use them first to inspect the intended scope and filtering rules.

Examples of documented option combinations include:

```bash
# Preview an operation targeting direct messages
python3 main.py --dm

# Specify channel IDs
python3 main.py -c CHANNEL_ID_1 CHANNEL_ID_2

# Inspect options for a specific server
python3 main.py -g SERVER_ID

# Review available filtering options
python3 main.py --help
```

Replace placeholders with IDs you are authorized to manage. These examples illustrate argument structure; they do not guarantee that the current implementation supports every combination or that Discord permits the underlying operation.

## Command-Line Options

The original project documents the following flags. Confirm their behavior with `python3 main.py --help` before use.

| Option | Description |
| --- | --- |
| `-c, --channel ID...` | Select channel IDs |
| `--dm` | Target direct-message conversations |
| `-g, --guild ID...` | Select server IDs |
| `--all-guilds` | Select all joined servers |
| `--live` | Enable execution instead of preview mode |
| `--older-than DAYS` | Filter by message age |
| `--keyword TEXT` | Filter by message content |
| `--keep-pinned` | Exclude pinned messages |
| `-w, --workers N` | Configure worker count |
| `--skip-channel ID...` | Exclude channel IDs |
| `--skip-user ID...` | Exclude user IDs |
| `--resume` | Resume supported interrupted operations |
| `-y, --yes` | Skip the interactive confirmation prompt |

The default behavior, valid argument ranges, and interaction between flags should be verified against the actual source code.

## Filtering and Execution

Before running any operation, review the following:

1. **Scope:** Confirm the selected channels or conversations.
2. **Filters:** Verify message-age and keyword filters.
3. **Exclusions:** Review channel and user skip lists.
4. **Preview:** Inspect the planned operation where dry-run support is available.
5. **Recovery:** Understand the checkpoint and failure-record behavior.
6. **Irreversibility:** Treat deletion as permanent unless the platform explicitly provides a recovery mechanism.

A dry run is only as reliable as the implementation behind it. Verify that preview mode performs no destructive requests before trusting it.

## Rate Limits and Reliability

The project documents support for rate-limit handling, retry behavior, and configurable concurrency.

Keep in mind:

- Increasing worker counts does not remove server-enforced rate limits.
- Retries should respect the server's retry instructions.
- Network failures can leave operations partially completed.
- Checkpoint files may not capture every possible failure state.
- Re-running an operation should be preceded by a review of its current scope.

Do not interpret a progress bar reaching 100% as proof that every requested operation succeeded. Review the final status and error records.

## Runtime Files

The project documents these local runtime files:

| File | Purpose |
| --- | --- |
| `latent_clean_log.txt` | Runtime and error logging |
| `latent_clean_failed.txt` | Records of failed operations |
| `latent_clean_checkpoint.json` | Progress state for supported resume operations |

These files may contain operational metadata. Inspect their contents before sharing them publicly, and ensure that sensitive values are not written to logs.

The project lists these files in `.gitignore`; verify the actual ignore rules in your local checkout.

## Security and Compatibility Notice

LATENT CLEAN is an independent, community-maintained project and is not affiliated with, endorsed by, or supported by Discord.

### Account automation

Discord prohibits automating normal user accounts through self-bots. Using a user token to automate account actions can result in account restrictions or termination.

For integrations, moderation tools, and message-management workflows, use the official Discord API and supported bot authentication wherever the intended operation is available.

Official documentation:

- [Discord Developer Documentation](https://discord.com/developers/docs/intro)
- [Discord Developer Terms](https://discord.com/developers/docs/policies-and-agreements/developer-terms-of-service)
- [Discord Community Guidelines](https://discord.com/guidelines)

### Data loss

Message deletion may be irreversible. The maintainers cannot guarantee that deleted messages can be recovered.

Use the software only with accounts and data you are authorized to manage. Understand the platform's rules and the risks before executing any operation.

## Troubleshooting

### Dependency installation fails

Update `pip` inside your virtual environment and reinstall the listed dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### An option is not recognized

Check the available arguments:

```bash
python3 main.py --help
```

Compare the output with the README for your checked-out version.

### An operation fails partway through

Review the runtime log and failure records. If the program supports resuming, inspect the checkpoint before attempting to continue.

### Authentication or access errors

Confirm that the configured authentication method is supported, that credentials have not expired, and that the requested operation is permitted. Do not attempt to bypass access controls or platform-enforced restrictions.

### Unexpected deletion scope

Stop execution, inspect the argument parsing and filtering logic, and test changes using a verified non-destructive preview before proceeding.

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

Runtime files may be created when the application runs.

## Contributing

Contributions that improve maintainability, reliability, testing, documentation, and security are welcome.

1. Fork the repository.
2. Create a descriptive feature branch.
3. Make a focused change.
4. Test the change locally.
5. Update the documentation when behavior changes.
6. Submit a pull request describing the change and its limitations.

Please avoid submitting credentials, session tokens, personal data, or unredacted runtime logs.

## License

This project is distributed under the MIT License. See [`LICENSE`](LICENSE) for the full license text.

---

**LATENT CLEAN** focused tooling, explicit configuration, and transparent execution behavior.
