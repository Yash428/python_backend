# Meeting Analyzer

AI-powered meeting analysis tool that extracts insights, action items, and provides semantic search capabilities.

## Features

- Meeting transcript parsing with timestamps
- AI-powered summarization and action item extraction
- Urgency detection for tasks
- Sentiment analysis
- Semantic search using vector embeddings
- Interactive chat interface

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Run the application:
```bash
python main.py
```

## Project Structure

- `main.py` - Main application entry point
- `config/` - Configuration and environment setup
- `src/` - Core application modules
- `data/` - Sample data and exports
- `tests/` - Unit tests (optional)

## API Keys Required

- Cohere API Key
- Qdrant Cloud URL and API Key