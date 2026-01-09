import uuid
from qdrant_client.models import PointStruct
from config.settings import Config

class VectorStore:
    """Handle vector storage and semantic search"""
    
    def __init__(self, qdrant_client, embedding_model):
        self.qdrant_client = qdrant_client
        self.embedding_model = embedding_model
    
    def generate_embeddings(self, texts):
        """
        Generate embeddings using Sentence Transformers
        """
        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def store_transcript_in_qdrant(self, transcript, meeting_id):
        """
        Store transcript entries in Qdrant with embeddings
        """
        # Prepare texts for embedding
        texts = [f"{entry['speaker_name']}: {entry['text']}" for entry in transcript]

        print(f"\nGenerating embeddings for {len(texts)} transcript entries...")
        embeddings = self.generate_embeddings(texts)

        # Prepare points for Qdrant
        points = []
        for i, (entry, embedding) in enumerate(zip(transcript, embeddings)):
            point = PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "meeting_id": meeting_id,
                    "timestamp": entry["timestamp"],
                    "speaker_name": entry["speaker_name"],
                    "text": entry["text"],
                    "sentiment": entry.get("sentiment", "neutral"),
                    "entry_index": i
                }
            )
            points.append(point)

        # Upload to Qdrant in batches
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.qdrant_client.upsert(
                collection_name=Config.COLLECTION_NAME,
                points=batch
            )
            print(f"  Uploaded batch {i//batch_size + 1}/{(len(points)-1)//batch_size + 1}")

        print(f"✓ Stored {len(points)} transcript entries in Qdrant Cloud")
        return points
    
    def search_relevant_transcript(self, query, meeting_id, top_k=5):
        """
        Search for relevant transcript entries using semantic search in Qdrant
        """
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search in Qdrant
        search_results = self.qdrant_client.search(
            collection_name=Config.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter={
                "must": [
                    {
                        "key": "meeting_id",
                        "match": {"value": meeting_id}
                    }
                ]
            },
            limit=top_k
        )

        return search_results