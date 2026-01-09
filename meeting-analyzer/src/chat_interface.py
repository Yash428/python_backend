from config.settings import Config

class ChatInterface:
    """Interactive chat interface for meeting analysis"""
    
    def __init__(self, api_clients, vector_store):
        self.api_clients = api_clients  # Changed to use api_clients instead of just cohere_client
        self.vector_store = vector_store
    
    def chat_with_transcript(self, user_question, processed_data, use_semantic_search=True):
        """
        Answer user questions based on meeting data using LLM with semantic search
        """
        transcript = processed_data.get('transcript', [])
        summary = processed_data.get('summary', {})
        meeting_id = processed_data.get('meeting_id')

        # Use semantic search to find most relevant parts
        relevant_context = ""
        if use_semantic_search and meeting_id:
            try:
                search_results = self.vector_store.search_relevant_transcript(user_question, meeting_id, top_k=5)
                relevant_context = "\n\nMOST RELEVANT TRANSCRIPT SECTIONS (Semantic Search):\n"
                for i, result in enumerate(search_results, 1):
                    payload = result.payload
                    relevant_context += f"{i}. [{payload['timestamp']}] {payload['speaker_name']}: {payload['text']} (Relevance: {result.score:.3f})\n"
            except Exception as e:
                print(f"Semantic search warning: {e}")

        # Format full transcript with sentiment
        formatted_transcript = "\n".join(
            f"[{t['timestamp']}] {t['speaker_name']} (Sentiment: {t['sentiment']}): {t['text']}"
            for t in transcript
        )

        # Format summary
        formatted_summary = f"""
EXECUTIVE SUMMARY:
{summary.get('executive_summary', 'N/A')}

ACTION ITEMS:
"""
        for i, item in enumerate(summary.get('action_items', []), 1):
            formatted_summary += f"""
{i}. Task: {item.get('task', 'N/A')}
   Owner: {item.get('owner', 'N/A')}
   Deadline: {item.get('deadline', 'N/A')}
   Urgency: {item.get('urgency', 'N/A')}
   Reason: {item.get('urgency_reason', 'N/A')}
"""

        formatted_summary += f"""
TOPICS DISCUSSED: {', '.join(summary.get('topics_discussed', ['N/A']))}
NAMED ENTITIES: {', '.join(summary.get('named_entities', ['N/A']))}
OVERALL SENTIMENT: {summary.get('overall_sentiment', 'N/A')}
"""

        system_prompt = """You are an AI meeting assistant. Answer questions based ONLY on the provided meeting data.
        Be concise and accurate. If information is not available, say so clearly.
        Reference specific timestamps and speakers when relevant.
        Prioritize information from the most relevant sections when available."""

        user_message = f"""
FULL MEETING TRANSCRIPT:
{formatted_transcript}

MEETING SUMMARY:
{formatted_summary}
{relevant_context}

USER QUESTION: {user_question}

Provide a clear, concise answer based on the meeting data above. Use the relevant sections highlighted by semantic search for better context."""

        # Use Ollama for Q&A to avoid Cohere rate limits
        try:
            response = self.api_clients.chat_with_ollama(
                prompt=user_message,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500
            )
            return response
        except Exception as e:
            print(f"⚠ Ollama failed, falling back to Cohere: {e}")
            # Fallback to Cohere if Ollama fails
            response = self.api_clients.cohere_client.chat(
                model="command-r-v2",
                preamble=system_prompt,
                message=user_message,
                temperature=0.3,
                max_tokens=500
            )
            return response.text
    
    def interactive_chat(self, processed_data):
        """Start an interactive chat session with semantic search"""
        print("\n" + "="*60)
        print("🤖 INTERACTIVE MEETING ASSISTANT")
        print("="*60)
        print("Ask questions about the meeting using natural language.")
        print("✨ Powered by Qdrant Cloud + Sentence Transformers + Ollama (qwen2:1.5b)")
        print("📝 Meeting analysis by Cohere, Q&A by Ollama (no rate limits!)")
        print("\n📋 Available Commands:")
        print("  • 'exit', 'quit', 'bye' - End chat session")
        print("  • 'summary' - Quick meeting overview")
        print("  • 'search <query>' - Semantic search in transcript")
        print("  • 'stats' - Qdrant storage statistics")
        print("  • 'actions' - List all action items with urgency")
        print("="*60 + "\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n✓ Chat session ended. Thank you! 👋")
                    break

                # Quick summary command
                if user_input.lower() == 'summary':
                    self._show_summary(processed_data)
                    continue

                # Actions command
                if user_input.lower() == 'actions':
                    self._show_actions(processed_data)
                    continue

                # Stats command
                if user_input.lower() == 'stats':
                    self._show_stats(processed_data)
                    continue

                # Semantic search command
                if user_input.lower().startswith('search '):
                    query = user_input[7:].strip()
                    if query:
                        self._perform_search(query, processed_data)
                    continue

                # Regular question - use LLM with semantic search
                print(f"\n🔍 Analyzing your question...\n")
                response = self.chat_with_transcript(user_input, processed_data, use_semantic_search=True)
                print(f"🤖 Assistant: {response}\n")

            except KeyboardInterrupt:
                print("\n\n✓ Chat interrupted. Goodbye! 👋")
                break
            except Exception as e:
                print(f"\n⚠ Error: {e}")
                print("Please try again or type 'exit' to quit.\n")
    
    def _show_summary(self, processed_data):
        """Show quick meeting summary"""
        print(f"\n🤖 Assistant: Here's your meeting overview:")
        print(f"\n📝 Executive Summary:")
        print(f"   {processed_data['summary'].get('executive_summary', 'N/A')}")
        print(f"\n📊 Statistics:")
        print(f"   • Action Items: {len(processed_data['summary'].get('action_items', []))}")
        print(f"   • Overall Sentiment: {processed_data['overall_sentiment']}")
        print(f"   • Topics: {', '.join(processed_data['summary'].get('topics_discussed', ['N/A']))}")
        print(f"   • Participants: {', '.join(processed_data['summary'].get('named_entities', ['N/A']))}\n")
    
    def _show_actions(self, processed_data):
        """Show all action items"""
        print(f"\n🤖 Assistant: Here are all action items:\n")
        for i, item in enumerate(processed_data['summary'].get('action_items', []), 1):
            urgency_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(item.get('urgency', 'medium'), '⚪')

            print(f"{i}. {urgency_emoji} [{item.get('urgency', 'N/A').upper()}] {item.get('task', 'N/A')}")
            print(f"   👤 Owner: {item.get('owner', 'N/A')}")
            print(f"   📅 Deadline: {item.get('deadline', 'Not specified')}")
            print(f"   💡 Reason: {item.get('urgency_reason', 'N/A')}\n")
    
    def _show_stats(self, processed_data):
        """Show Qdrant statistics"""
        try:
            collection_info = self.vector_store.qdrant_client.get_collection(Config.COLLECTION_NAME)
            print(f"\n🤖 Assistant: Qdrant Cloud Storage Statistics:")
            print(f"   • Collection: {Config.COLLECTION_NAME}")
            print(f"   • Total vectors: {collection_info.points_count}")
            print(f"   • Vector dimension: {collection_info.config.params.vectors.size}")
            print(f"   • Distance metric: {collection_info.config.params.vectors.distance}")
            print(f"   • Current Meeting ID: {processed_data['meeting_id']}")
            print(f"   • Embedding Model: {Config.EMBEDDING_MODEL}\n")
        except Exception as e:
            print(f"\n⚠ Error fetching stats: {e}\n")
    
    def _perform_search(self, query, processed_data):
        """Perform semantic search"""
        print(f"\n🔍 Searching for: '{query}'...")
        try:
            results = self.vector_store.search_relevant_transcript(query, processed_data['meeting_id'], top_k=3)
            
            if not results:
                print(f"🤖 Assistant: No relevant results found for '{query}'. Try a different search term.\n")
                return
                
            print(f"🤖 Assistant: Top {len(results)} most relevant transcript sections:\n")
            for i, result in enumerate(results, 1):
                payload = result.payload
                print(f"{i}. [{payload['timestamp']}] 💬 {payload['speaker_name']}:")
                print(f"   \"{payload['text']}\"")
                print(f"   📊 Relevance Score: {result.score:.3f}\n")
        except Exception as e:
            print(f"⚠ Error performing search: {e}")
            print("Please try again or type 'exit' to quit.\n")