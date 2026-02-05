import logging
from ..store.raw_store import RawStore
from ..state.repo import StateRepo
from ..formats.registry import FormatRegistry
from ..core.router import decide_format

logger = logging.getLogger(__name__)

class TransformPipeline:
    def __init__(self, raw_store: RawStore, state_repo: StateRepo, registry: FormatRegistry):
        self.raw_store = raw_store
        self.state_repo = state_repo
        self.registry = registry

    def process_pending(self):
        with self.state_repo.db.connect() as conn:
            rows = conn.execute(
                "SELECT id, source_id, external_id, raw_hash, filename FROM seen_files WHERE status = 'pending'"
            ).fetchall()

        for row in rows:
            raw_hash = row["raw_hash"]
            source_id = row["source_id"]
            filename = row["filename"] or "unknown"

            try:
                data = self.raw_store.get(raw_hash)
                if not data:
                    self.state_repo.update_file_status(raw_hash, "failed", "Raw data missing")
                    continue

                fmt_id = decide_format(filename, data)

                handler = self.registry.get(fmt_id)
                records = handler.parse(data, {"filename": filename, "source_id": source_id})

                for rec in records:
                    self.state_repo.add_record(
                        raw_hash=raw_hash,
                        record_type=fmt_id,
                        unique_hash=rec["unique_hash"],
                        data=rec["data"]
                    )

                self.state_repo.update_file_status(raw_hash, "processed")

            except Exception as e:
                logger.exception(f"Failed to transform file {raw_hash}")
                self.state_repo.update_file_status(raw_hash, "failed", str(e))
