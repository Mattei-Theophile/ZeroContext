from __future__ import annotations

import os
from datetime import UTC, datetime

from gridfs import GridFS
from pymongo import MongoClient


class MongoDiscussionService:
    def __init__(self) -> None:
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        database_name = os.getenv("MONGODB_DATABASE", "anomizum")
        collection_name = os.getenv("MONGODB_COLLECTION", "discussions")

        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.fs = GridFS(self.db)

        self.collection.create_index("discussion_uuid", unique=True)

    def save_prompt(
            self,
            discussion_uuid: str,
            prompt: str,
            anonymized_text: str,
            match_table: dict[str, str],
    ) -> None:
        self.collection.update_one(
            {"discussion_uuid": discussion_uuid},
            {
                "$setOnInsert": {
                    "discussion_uuid": discussion_uuid,
                    "created_at": datetime.now(UTC),
                },
                "$push": {
                    "prompts": {
                        "prompt": prompt,
                        "anonymized_text": anonymized_text,
                        "match_table": match_table,
                        "created_at": datetime.now(UTC),
                    }
                },
            },
            upsert=True,
        )

    def save_file(
            self,
            discussion_uuid: str,
            filename: str,
            content: bytes,
            content_type: str = "application/pdf",
    ) -> str:
        file_id = self.fs.put(
            content,
            filename=filename,
            content_type=content_type,
            discussion_uuid=discussion_uuid,
            created_at=datetime.now(UTC),
        )

        self.collection.update_one(
            {"discussion_uuid": discussion_uuid},
            {
                "$setOnInsert": {
                    "discussion_uuid": discussion_uuid,
                    "created_at": datetime.now(UTC),
                },
                "$push": {
                    "files": {
                        "file_id": str(file_id),
                        "filename": filename,
                        "content_type": content_type,
                        "created_at": datetime.now(UTC),
                    }
                },
            },
            upsert=True,
        )

    def get_all_discussions(self) -> list[dict]:
        return list(self.collection.find({}, {"discussion_uuid": 1, "created_at": 1}).sort("created_at", -1))

    def get_discussion_by_uuid(self, discussion_uuid: str) -> dict | None:
        return self.collection.find_one({"discussion_uuid": discussion_uuid})