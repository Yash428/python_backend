# Ollama Setup Guide

This guide will help you set up Ollama with the qwen2:1.5b model to avoid Cohere API rate limits for Q&A functionality.

## What Changed

- **Meeting Analysis**: Still uses Cohere (for high-quality analysis)
- **Q&A Chat**: Now uses Ollama with qwen2:1.5b (no rate limits!)
- **Fallback**: If Ollama fails, automatically falls back to Cohere

## Installation Steps

### 1. Install Ollama

**Windows:**
```bash
# Download and install from: https://ollama.ai/download
# Or use winget:
winget install Ollama.Ollama
```

**macOS:**
```bash
# Download from: https://ollama.ai/download
# Or use Homebrew:
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Start Ollama Server

```bash
ollama serve
```

Keep this running in a separate terminal.

### 3. Install the qwen2:1.5b Model

```bash
ollama pull qwen2:1.5b
```

This will download the model (about 1GB).

### 4. Verify Installation

```bash
# Test the model
ollama run qwen2:1.5b "Hello, how are you?"
```

### 5. Test Integration

Run the test script:

```bash
cd meeting-analyzer
python test_ollama.py
```

## Configuration

The configuration is already set in your `.env` file:

```env
# Ollama Configuration (for Q&A to avoid rate limits)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:1.5b
```

## Usage

Now when you run the meeting analyzer:

1. **Meeting analysis** (parsing, summarization, urgency detection) uses Cohere
2. **Interactive Q&A chat** uses Ollama (no rate limits!)
3. **Automatic fallback** to Cohere if Ollama is unavailable

## Benefits

- ✅ No more rate limit errors during Q&A
- ✅ Unlimited questions about your meetings
- ✅ Fast local responses
- ✅ Privacy - Q&A data stays local
- ✅ Automatic fallback to Cohere if needed

## Troubleshooting

**"Connection refused" error:**
- Make sure `ollama serve` is running
- Check if port 11434 is available

**"Model not found" error:**
- Run `ollama pull qwen2:1.5b` to download the model
- Verify with `ollama list`

**Slow responses:**
- qwen2:1.5b is optimized for speed
- Consider upgrading to qwen2:7b for better quality (but slower)

## Alternative Models

You can change the model in `.env`:

```env
# Faster, smaller model (current)
OLLAMA_MODEL=qwen2:1.5b

# Better quality, larger model
OLLAMA_MODEL=qwen2:7b

# Other options
OLLAMA_MODEL=llama3.2:3b
OLLAMA_MODEL=phi3:mini
```

Remember to pull the new model: `ollama pull <model-name>`