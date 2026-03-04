"""
ReportStore — Qdrant-backed persistence for Company Intelligence reports.

Schema (collection: company_reports):
  vector : 384-dim embedding of "{company_name} {company_region}"
  payload:
    id            : UUID str (same as Qdrant point id)
    company_name  : str
    company_region: str
    created_at    : ISO-8601 timestamp str
    report        : full StructuredBusinessAnalysis as dict
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)
from sentence_transformers import SentenceTransformer

COLLECTION = "company_reports"
EMBEDDING_DIM = 384


class ReportStore:
    """
    Persists and retrieves Company Intelligence reports in Qdrant.
    """

    def __init__(self, host: str = "qdrant", port: int = 6333) -> None:
        self._client = QdrantClient(host=host, port=port)
        self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self._ensure_collection()

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _ensure_collection(self) -> None:
        """Create the collection if it doesn't already exist."""
        if not self._client.collection_exists(COLLECTION):
            self._client.create_collection(
                collection_name=COLLECTION,
                vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
            )

    def _embed(self, text: str) -> List[float]:
        return self._encoder.encode(text).tolist()

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def save(self, company_name: str, company_region: str, report: Dict[str, Any]) -> str:
        """
        Persist a report to Qdrant. Returns the generated UUID for this record.
        """
        report_id = str(uuid.uuid4())
        vector_text = f"{company_name} {company_region}"

        payload = {
            "id": report_id,
            "company_name": company_name,
            "company_region": company_region,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "report": report,  # full dict — nested sub-models included
        }

        point = PointStruct(
            id=report_id,
            vector=self._embed(vector_text),
            payload=payload,
        )

        self._client.upsert(collection_name=COLLECTION, points=[point])
        return report_id

    def list_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Return metadata for all saved reports (newest first), without the full report body.
        Suitable for populating the sidebar.
        """
        results, _ = self._client.scroll(
            collection_name=COLLECTION,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        summaries = []
        for point in results:
            p = point.payload or {}
            summaries.append({
                "id":             p.get("id", str(point.id)),
                "company_name":   p.get("company_name", ""),
                "company_region": p.get("company_region", ""),
                "created_at":     p.get("created_at", ""),
            })

        # Sort newest first
        summaries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return summaries

    def delete(self, report_id: str) -> bool:
        """
        Delete a report from Qdrant by its UUID.
        Returns True if deleted, False if not found.
        """
        results = self._client.retrieve(
            collection_name=COLLECTION,
            ids=[report_id],
            with_payload=False,
            with_vectors=False,
        )
        if not results:
            return False
        from qdrant_client.http.models import PointIdsList
        self._client.delete(
            collection_name=COLLECTION,
            points_selector=PointIdsList(points=[report_id]),
        )
        return True

    def get_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a full report payload by its UUID.
        Returns None if not found.
        """
        results = self._client.retrieve(
            collection_name=COLLECTION,
            ids=[report_id],
            with_payload=True,
            with_vectors=False,
        )
        if not results:
            return None

        payload = results[0].payload or {}
        return payload.get("report")
