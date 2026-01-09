import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration settings"""
    
    # API Keys
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
    
    # Application Settings
    COLLECTION_NAME = os.getenv("COLLECTION_NAME", "meeting_transcripts")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Rate limiting
    API_DELAY_SECONDS = float(os.getenv("API_DELAY_SECONDS", "0.5"))
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            ("COHERE_API_KEY", cls.COHERE_API_KEY),
            ("QDRANT_URL", cls.QDRANT_URL),
            ("QDRANT_API_KEY", cls.QDRANT_API_KEY)
        ]
        
        missing = [name for name, value in required_vars if not value]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True