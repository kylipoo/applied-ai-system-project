"""
Gemini client wrapper used by the music recommender agent.

Handles:
- Configuring the Gemini client from the GEMINI_API_KEY environment variable
- RAG-style explanations grounded in song and user profile data
"""

import os
import google.generativeai as genai

GEMINI_MODEL_NAME = "gemma-3-27b-it"


class GeminiClient:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY environment variable. "
                "Set it in your shell or .env file."
            )
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)

    def answer_from_snippets(self, query, snippets):
        """
        Generate an answer grounded in the provided snippets.
        snippets: list of (filename, text) tuples
        """
        if not snippets:
            return "I do not know based on the docs I have."

        context_blocks = []
        for filename, text in snippets:
            context_blocks.append(f"File: {filename}\n{text}\n")
        context = "\n\n".join(context_blocks)

        prompt = f"""
You are a music recommendation assistant helping a user understand why a song was recommended.

You will be given one or two snippets:
- "song_and_user_profile": numeric attributes (genre, mood, energy, tempo, acousticness) and the user's preferences.
- "wikipedia" (optional): real-world background about the song — may include summary, recording background, composition details, and reception.

Your job:
- Use the song_and_user_profile snippet to explain how the song's attributes match the user's preferences (1 sentence).
- If a wikipedia snippet is present, draw on it for up to 2 sentences of real-world context — e.g. how the song was made, what it is known for, its cultural impact, or critical reception. Prefer specific details over vague praise. Do not repeat numeric attributes.
- 3 to 4 sentences total. Be specific and friendly.
- Do not invent any information not present in the snippets.

Snippets:
{context}

Question:
{query}
"""
        response = self.model.generate_content(prompt)
        return (response.text or "").strip()
