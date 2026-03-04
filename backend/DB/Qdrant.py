from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


class QdrantConnector:
    def __init__(self, host: str = "qdrant"):
        self.client = QdrantClient(host=host)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")


    def similarity_search(self, query: str, k: int = 10, collectionName: str ="portfolio_documents"):
        """ Return hits object which contain 'text':, 'source_file':, "score" """

        hits = self.client.query_points(
            collection_name=collectionName,
            query=self.encoder.encode(query).tolist(),
            limit=k,
        ).points

        return hits


