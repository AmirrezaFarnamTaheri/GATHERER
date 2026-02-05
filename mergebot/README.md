# MergeBot

Incremental multi-format file merger and Telegram publisher.

## Installation

Obtaining file:///app/mergebot
  Installing build dependencies: started
  Installing build dependencies: finished with status 'done'
  Checking if build backend supports build_editable: started
  Checking if build backend supports build_editable: finished with status 'done'
  Getting requirements to build editable: started
  Getting requirements to build editable: finished with status 'done'
  Preparing editable metadata (pyproject.toml): started
  Preparing editable metadata (pyproject.toml): finished with status 'done'
Requirement already satisfied: PyYAML>=6.0 in /home/jules/.pyenv/versions/3.12.12/lib/python3.12/site-packages (from mergebot==0.1.0) (6.0.3)
Building wheels for collected packages: mergebot
  Building editable for mergebot (pyproject.toml): started
  Building editable for mergebot (pyproject.toml): finished with status 'done'
  Created wheel for mergebot: filename=mergebot-0.1.0-0.editable-py3-none-any.whl size=1499 sha256=8e90ae2d32b3a32657639ce731d1df4ab7eddda5c07aa3c63bcf1a308d1ea568
  Stored in directory: /tmp/pip-ephem-wheel-cache-0plvqe7g/wheels/8e/93/b6/a2a0fc92536216ca03860e56e7cc25eb4a3673a855e468413c
Successfully built mergebot
Installing collected packages: mergebot
  Attempting uninstall: mergebot
    Found existing installation: mergebot 0.1.0
    Uninstalling mergebot-0.1.0:
      Successfully uninstalled mergebot-0.1.0
Successfully installed mergebot-0.1.0

## Configuration

Edit . Set your Telegram Token and Chat IDs.

## Usage

Initialize the database (first time):


Run the bot:


## Features

- **Ingest**: Fetches files from Telegram channels.
- **Transform**: Normalizes text configurations or handles binary blobs (ZIP bundling).
- **Build**: Merges unique records.
- **Publish**: Sends updates to Telegram only when content changes.
