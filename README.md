# LATENT-CLEAN

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Discord-API-5865F2?logo=discord&logoColor=white" alt="Discord API">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/Status-Active-success" alt="Status">
</p>

<p align="center">
  <strong>Terminal-based Discord message cleanup tool written in Python.</strong>
</p>

<p align="center">
  Clean your own messages across DMs, group DMs, and server channels with rate-limit handling, retries, checkpoints, and configurable cleanup modes.
</p>

## Features

* Written in Python
* Interactive terminal interface
* DM cleanup
* Group DM cleanup
* Server-wide cleanup
* Single-server cleanup
* Specific channel cleanup
* Channel whitelist
* User whitelist
* Dry run mode
* Age-based message filtering
* Configurable worker count
* Multi-threaded deletion
* Automatic rate-limit handling
* Automatic request retries
* Failed message tracking
* Checkpoint and resume support
* Live progress bar
* Deletion speed tracking
* Runtime statistics
* Permanent deletion confirmation
* Graceful interruption handling

## Configuration

LATENT-CLEAN provides configurable options for:

* Dry run mode
* Message age filter
* Concurrent workers
* Channel whitelist
* User whitelist

The default configuration starts with dry run enabled, allowing the cleanup process to scan messages without deleting them.

## Requirements

* Python 3.9+
* `requests`

## Installation

```bash
git clone <repository-url>
cd LATENT-CLEAN
pip install -r requirements.txt
```

## Usage

```bash
python latent_clean.py
```

The application provides an interactive terminal menu:

```text
1  Clean channels by ID
2  Clean all DMs
3  Clean all servers
4  Clean one server
5  Retry failed
6  Statistics
7  Settings
0  Exit
```

The settings menu allows the user to control dry run mode, the age filter, and the number of worker threads.

## Dry Run

LATENT-CLEAN starts with dry run mode enabled.

In dry run mode, the tool scans messages and reports how many messages would be deleted without performing the deletion request.

Live deletion requires explicit confirmation by typing `YES`.

## Age Filter

The age filter can restrict deletion to messages older than a specified number of days.

This can be configured directly from the Settings menu.

## Performance

Message deletion uses a configurable `ThreadPoolExecutor` worker pool.

The tool provides a live progress bar showing:

* Completion percentage
* Processed messages
* Successful deletions
* Failed deletions
* Messages per second

## Rate Limit Handling

LATENT-CLEAN automatically handles Discord API rate limits.

When a `429` response is received, the tool reads the API-provided retry interval and waits before continuing. Global rate limits are tracked separately.

## Checkpoint System

Long-running operations can be resumed through the checkpoint system.

The tool stores:

* Runtime statistics
* Failed messages
* Completed channels
* Checkpoint timestamp

## Runtime Files

The following files may be generated during execution:

```text
latent_clean_log.txt
latent_clean_failed.txt
latent_clean_checkpoint.json
```

These files should not be committed to the repository.

## Security

Never commit your Discord authentication token.

The repository should only contain the placeholder token configuration.

If an authentication token is accidentally exposed, revoke it immediately and generate a new one.

## Disclaimer

LATENT-CLEAN is provided for educational purposes.

Automating a Discord user account may violate Discord's Terms of Service and may result in account restrictions or termination.

Deleted messages cannot be restored.

The author is not responsible for account restrictions, account termination, deleted content, data loss, API restrictions, or any other consequences resulting from the use of this software.

Use LATENT-CLEAN at your own risk.

## License

LATENT-CLEAN is released under the MIT License.
