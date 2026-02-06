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
        new_hash = build_result["artifact_hash"]
        data = build_result["data"]

        # Save to local artifacts (Always, even if not published to TG)
        # This ensures GitHub Artifacts are populated
        artifact_dir = "persist/artifacts"
        try:
            os.makedirs(artifact_dir, exist_ok=True)
            # Use route_name as filename. defaulting to .txt as format is opaque here
            # Ideally we would know the extension from the format.
            filename = f"{route_name}.txt"
            filepath = os.path.join(artifact_dir, filename)
            with open(filepath, "wb") as f:
                f.write(data)
            logger.info(f"Saved artifact to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save artifact locally: {e}")

        # Check if changed (for Telegram Publishing)
        last_hash = self.state_repo.get_last_published_hash(route_name)
        if last_hash == new_hash:
            logger.info(f"No change for {route_name}, skipping publish.")
            return

        # Publish to all destinations
        default_token = os.getenv("TELEGRAM_TOKEN")

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
                count=build_result.get("count", "?")
            )

            # Filename for Telegram
            filename_tg = f"{route_name}_{new_hash[:8]}.txt"

            try:
                pub.publish(chat_id, data, filename_tg, caption)
                published_any = True
            except Exception as e:
                logger.error(f"Failed to publish to {chat_id}: {e}")

        if published_any:
            self.state_repo.mark_published(route_name, new_hash)
            logger.info(f"Published {route_name} ({new_hash})")
