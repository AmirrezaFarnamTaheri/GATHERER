import logging
import datetime
import os
from typing import Dict, Any, List
from ..state.repo import StateRepo
from ..publishers.telegram.publisher import TelegramPublisher

logger = logging.getLogger(__name__)

class PublishPipeline:
    def __init__(self, state_repo: StateRepo):
        self.state_repo = state_repo
        self.publishers = {} # cache of (token) -> publisher

    def run(self, build_result: Dict[str, Any], destinations: List[Dict[str, Any]]):
        route_name = build_result["route_name"]
        fmt = build_result.get("format", "unknown")
        new_hash = build_result["artifact_hash"]

        # Use a composite key for tracking state to support multiple formats per route
        tracking_key = f"{route_name}:{fmt}"

        # Check if changed
        last_hash = self.state_repo.get_last_published_hash(tracking_key)
        if last_hash == new_hash:
            logger.info(f"No change for {tracking_key}, skipping publish.")
            return

        default_token = os.getenv("TELEGRAM_TOKEN")

        # Determine extension
        ext = ".txt"
        if fmt == "ovpn":
            ext = ".ovpn"
        elif fmt == "bundle":
            ext = ".zip"

        filename = f"{route_name}_{fmt}_{new_hash[:8]}{ext}"

        published_any = False

        for dest in destinations:
            chat_id = dest["chat_id"]
            template = dest.get("caption_template", "Update: {timestamp}")
            token = dest.get("token", default_token)

            if not token:
                logger.error("No token for destination")
                continue

            # Get publisher
            if token not in self.publishers:
                self.publishers[token] = TelegramPublisher(token)
            pub = self.publishers[token]

            # Format caption
            caption = template.format(
                timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                sha12=new_hash[:12],
                count=build_result.get("count", "?"),
                format=fmt
            )

            try:
                pub.publish(chat_id, build_result["data"], filename, caption)
                published_any = True
            except Exception:
                logger.error(f"Failed to publish to {chat_id}")

        if published_any:
            self.state_repo.mark_published(tracking_key, new_hash)
            logger.info(f"Published {tracking_key} ({new_hash})")
