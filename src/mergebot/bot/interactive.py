import logging
import time
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..store.artifact_store import ArtifactStore
from ..state.repo import StateRepo
from ..state.db import open_db
from ..store.paths import STATE_DB_PATH
from ..config.loader import load_config

logger = logging.getLogger(__name__)

class InteractiveBot:
    def __init__(self, token: str, config_path: str = "config.yaml"):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.artifact_store = ArtifactStore()
        # Ensure path for db
        self.db = open_db(STATE_DB_PATH)
        self.repo = StateRepo(self.db)

        # Load config to know routes/formats if needed
        # self.config = load_config(config_path)

        # Ensure subscription table exists
        self._init_subs_table()

    def _init_subs_table(self):
        with self.db.connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bot_subs (
                    user_id TEXT,
                    chat_id TEXT,
                    format_filter TEXT,
                    frequency_hours INTEGER,
                    last_sent_ts REAL,
                    PRIMARY KEY (user_id, format_filter)
                )
            """)
            conn.execute("CREATE TABLE IF NOT EXISTS bot_state (key TEXT PRIMARY KEY, value TEXT)")

    def _make_request(self, method: str, params: Dict[str, Any] = {}) -> Dict[str, Any]:
        url = f"{self.base_url}/{method}"
        try:
            if params:
                data = json.dumps(params).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            else:
                req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Bot API error {method}: {e}")
            return {"ok": False}

    def _send_message(self, chat_id: str, text: str):
        logger.info(f"Sending message to {chat_id}: {text}")
        self._make_request("sendMessage", {"chat_id": chat_id, "text": text})

    def _send_document(self, chat_id: str, file_path: Path, caption: str = ""):
        # Simple multipart upload via requests (if available) or curl
        # Since we want zero dependencies beyond what we have:
        # We can use 'curl' via subprocess as a fallback if 'requests' is missing.
        # But 'telethon' is installed. We can use telethon bot client?
        # Actually, let's use 'curl' for simplicity as it's available in almost all linux envs including GH Actions.
        import subprocess

        cmd = [
            "curl", "-s", "-X", "POST", f"{self.base_url}/sendDocument",
            "-F", f"chat_id={chat_id}",
            "-F", f"document=@{file_path}",
            "-F", f"caption={caption}"
        ]
        try:
            logger.info(f"Sending document {file_path.name} to {chat_id}")
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.error(f"Failed to send document via curl: {e}")
            self._send_message(chat_id, f"Error sending file: {file_path.name}")

    def run_once(self):
        """
        Since this runs in a cron job (every 3 hours), we:
        1. Fetch updates since last run (we don't persist offset for bot commands heavily).
        2. Process commands.
        3. Check subscriptions and push files.
        """
        logger.info("Starting Interactive Bot run...")

        # 1. Fetch Updates
        last_update_id = self._get_last_update_id()
        # Only process new updates, increment offset
        updates = self._get_updates(offset=last_update_id + 1)

        if updates:
            logger.info(f"Processing {len(updates)} bot updates...")
            for update in updates:
                try:
                    self._process_update(update)
                    last_update_id = max(last_update_id, update["update_id"])
                except Exception as e:
                    logger.error(f"Error processing update {update}: {e}")

            self._set_last_update_id(last_update_id)
        else:
            logger.info("No new bot updates.")

        # 2. Process Subscriptions
        # self._process_subscriptions() # Commented out for now as it needs more robust frequency logic

    def _get_updates(self, offset: int) -> List[Dict[str, Any]]:
        resp = self._make_request("getUpdates", {"offset": offset, "timeout": 5})
        return resp.get("result", [])

    def _process_update(self, update: Dict[str, Any]):
        msg = update.get("message")
        if not msg: return

        chat_id = str(msg["chat"]["id"])
        text = msg.get("text", "")
        user_id = str(msg["from"]["id"])

        if text.startswith("/"):
            parts = text.split()
            cmd = parts[0]
            args = parts[1:]

            if cmd == "/start" or cmd == "/help":
                self._send_message(chat_id,
                    "MergeBot Interactive:\n"
                    "/latest [format] [days] - Get latest merged files (default: all formats, last 4 days)\n"
                    "/subscribe [6h|12h|24h] [format] - Subscribe (Coming Soon)\n"
                )

            elif cmd == "/latest":
                fmt = args[0] if args else None
                days = int(args[1]) if len(args) > 1 and args[1].isdigit() else 4
                self._handle_latest(chat_id, fmt, days)

            # Subscribe logic deferred for simplicity/robustness first pass

    def _handle_latest(self, chat_id: str, fmt_filter: Optional[str], days: int):
        files = self.artifact_store.list_archive(days=days)
        if not files:
            self._send_message(chat_id, f"No artifacts found in the last {days} days.")
            return

        sent_count = 0
        # Group by unique base name (route+format)? No, just send distinct latest files.
        # Use a set to avoid spamming if multiple versions exist?
        # The user said "all last 4 days output".
        # We send ALL of them.

        for f in files:
            parts = f.name.split(".")
            ext = parts[-1]
            if fmt_filter and ext != fmt_filter:
                continue

            self._send_document(chat_id, f, caption=f"Archive: {f.name}")
            sent_count += 1
            # Rate limit slightly
            time.sleep(0.5)

        if sent_count == 0:
             self._send_message(chat_id, f"No artifacts found matching filter '{fmt_filter}'.")

    def _get_last_update_id(self) -> int:
        try:
            with self.db.connect() as conn:
                row = conn.execute("SELECT value FROM bot_state WHERE key='offset'").fetchone()
                return int(row["value"]) if row else 0
        except:
            return 0

    def _set_last_update_id(self, val: int):
        with self.db.connect() as conn:
            conn.execute("INSERT OR REPLACE INTO bot_state (key, value) VALUES ('offset', ?)", (str(val),))

if __name__ == "__main__":
    import os
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", required=True)
    args = parser.parse_args()

    bot = InteractiveBot(token=args.token)
    bot.run_once()
