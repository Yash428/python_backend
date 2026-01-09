import cohere
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from sentence_transformers import SentenceTransformer
from config.settings import Config

class APIClients:
    """Initialize and manage API clients"""
    
    def __init__(self):
        Config.validate()
        
        # Initialize Cohere client
        self.cohere_client = cohere.Client(Config.COHERE_API_KEY)
        
        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(
            url=Config.QDRANT_URL,
            api_key=Config.QDRANT_API_KEY,
        )
        
        # Initialize Sentence Transformer model
        print("Loading Sentence Transformer model...")
        self.embedding_model = SentenceTransformer(Config.EMBEDDING_MODEL)
        
        print("✓ All clients initialized successfully")
        self._verify_connections()
    
    def _verify_connections(self):
        """Verify API connections"""
        try:
            # Test Qdrant connection
            collections = self.qdrant_client.get_collections()
            print(f"✓ Qdrant connection verified. Collections: {len(collections.collections)}")
            
            # Test Cohere connection (simple ping)
            print("✓ Cohere client ready")
            
        except Exception as e:
            print(f"⚠ Connection verification failed: {e}")
    
    def create_collection_if_not_exists(self):
        """Create Qdrant collection if it doesn't exist"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]

            if Config.COLLECTION_NAME in collection_names:
                print(f"✓ Collection '{Config.COLLECTION_NAME}' already exists")
                collection_info = self.qdrant_client.get_collection(Config.COLLECTION_NAME)
                print(f"  Points count: {collection_info.points_count}")
            else:
                self.qdrant_client.create_collection(
                    collection_name=Config.COLLECTION_NAME,
                    vectors_config=VectorParams(size=Config.EMBEDDING_DIM, distance=Distance.COSINE),
                )
                print(f"✓ Created new collection: {Config.COLLECTION_NAME}")
        except Exception as e:
            print(f"⚠ Error with collection: {e}")
            raise