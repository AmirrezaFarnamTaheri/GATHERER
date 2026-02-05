import yaml
from typing import Dict, Any
from pathlib import Path
from .env_expand import expand_env
from .schema import AppConfig, SourceConfig, TelegramSourceConfig, SourceSelector, PublishRoute, DestinationConfig

def load_config(path: Path) -> AppConfig:
    with open(path, "r") as f:
        raw_text = f.read()

    expanded_text = expand_env(raw_text)
    data = yaml.safe_load(expanded_text)

    # Parse sources
    sources = []
    for s in data.get("sources", []):
        tg_conf = None
        if s.get("telegram"):
            tg_conf = TelegramSourceConfig(
                token=s["telegram"]["token"],
                chat_id=s["telegram"]["chat_id"]
            )

        sources.append(SourceConfig(
            id=s["id"],
            type=s["type"],
            selector=SourceSelector(include_formats=s["selector"]["include_formats"]),
            telegram=tg_conf
        ))

    # Parse routes
    routes = []
    for r in data.get("publishing", {}).get("routes", []):
        dests = []
        for d in r.get("destinations", []):
            dests.append(DestinationConfig(
                chat_id=d["chat_id"],
                mode=d["mode"],
                caption_template=d.get("caption_template", ""),
                token=d.get("token")
            ))

        routes.append(PublishRoute(
            name=r["name"],
            from_sources=r["from_sources"],
            formats=r["formats"],
            destinations=dests
        ))

    return AppConfig(sources=sources, routes=routes)
