# MergeBot User Guide

## Table of Contents
1. [Configuration](#configuration)
2. [Running locally](#running-locally)
3. [Running on GitHub Actions](#running-on-github-actions)
4. [Architecture](#architecture)

## Configuration

The core of MergeBot is controlled by a YAML configuration file.

### Sources

Define where the bot should look for files.

```yaml
sources:
  - id: "source_channel_1"
    type: "telegram"
    selector:
      include_formats: ["npvt", "ovpn"]
    telegram:
      token: "${TELEGRAM_TOKEN}"
      chat_id: "-1001234567890"
```

### Publishing Routes

Define how to merge and where to publish the results.

```yaml
publishing:
  routes:
    - name: "merged_vpn"
      from_sources: ["source_channel_1"]
      formats: ["npvt"]
      destinations:
        - chat_id: "-1009876543210"
          mode: "post_on_change"
          caption_template: "Merged V2Ray Configs\nDate: {timestamp}"
```

## Running Locally

To run the bot manually:

```bash
mergebot --config configs/config.prod.yaml --data-dir ./data --db-path ./data/state/state.db run
```

## Running on GitHub Actions

MergeBot is designed to run periodically on GitHub Actions without a dedicated server.

1. **Fork the repository**.
2. **Add Secrets**:
   - Go to Settings -> Secrets and variables -> Actions.
   - Add `TELEGRAM_TOKEN` (for the scraping bot).
   - Add `PUBLISH_BOT_TOKEN` (if using a separate bot for publishing).
3. **Enable Workflows**:
   - The `.github/workflows/mergebot.yml` workflow is scheduled to run hourly.
   - It will automatically create an orphan branch `mergebot-state` to store the SQLite database between runs.

## Architecture

- **Ingestion**: The bot connects to Telegram, downloads new files, and computes a SHA256 hash.
- **Deduplication**: Files with known hashes are skipped.
- **Transformation**: Files are parsed into a normalized format (if supported) or treated as opaque blobs.
- **Merging**: Compatible formats are combined into a single artifact.
- **Publishing**: The merged artifact is sent to the destination channel.

## New Features

### 72-Hour Fresh Start Rule
When a Telegram source is added for the first time (or if the state is reset), the bot will only process messages from the last 72 hours. This prevents the bot from attempting to download the entire history of a channel, which could take a long time and hit API limits.

### Multi-Format Output
Routes can now specify multiple output formats.

The bot will generate and publish a separate artifact for each requested format.

### Artifact Verification
A verification script `scripts/verify_output.py` is included to:
1. Scan generated artifacts.
2. Verify their integrity and format (e.g., checking if V2Ray links are valid).
3. Prepare them for distribution (copying to a clean `dist/` directory).

This script runs automatically in the CI/CD pipeline, and the results are uploaded as GitHub Artifacts (downloadable from the Actions tab).

## New Features

### 72-Hour Fresh Start Rule
When a Telegram source is added for the first time (or if the state is reset), the bot will only process messages from the last 72 hours. This prevents the bot from attempting to download the entire history of a channel, which could take a long time and hit API limits.

### Multi-Format Output
Routes can now specify multiple output formats.
```yaml
formats: ["npvt", "ovpn", "bundle"]
```
The bot will generate and publish a separate artifact for each requested format.

### Artifact Verification
A verification script `scripts/verify_output.py` is included to:
1. Scan generated artifacts.
2. Verify their integrity and format (e.g., checking if V2Ray links are valid).
3. Prepare them for distribution (copying to a clean `dist/` directory).

This script runs automatically in the CI/CD pipeline, and the results are uploaded as GitHub Artifacts (downloadable from the Actions tab).
