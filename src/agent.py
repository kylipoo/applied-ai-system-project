"""
Agentic music recommendation assistant powered by Gemma.

Initialization (runs once on startup):
  1. Loads the song catalog
  2. Asks Gemma to map genre relationships from the catalog's actual genres
     (this powers the 0.7 partial-credit subgenre scoring)

Agent loop:
  3. Gemma interviews the user via chat to learn their preferences
  4. When ready, Gemma outputs a RECOMMEND: JSON block with the user's preferences
  5. Python detects the JSON, calls recommend_songs() directly, and feeds the
     results back to Gemma as a chat message
  6. For the top result, GeminiClient.answer_from_snippets generates a RAG-style
     explanation grounded in the song's actual attributes and the user's preferences

Run with: python src/agent.py
"""

import json
import os
import re
import google.generativeai as genai
import wikipedia
from dotenv import load_dotenv
from recommender import load_songs, recommend_songs
from llm_client import GeminiClient

load_dotenv()

MODEL_NAME = "gemma-3-27b-it"


USEFUL_SECTIONS = ["background", "recording", "composition", "music video", "reception", "legacy", "commercial performance"]


def fetch_song_context(title: str, artist: str) -> str:
    """
    Fetch a Wikipedia summary for a song plus any available background/reception
    sections, preferring the song page over albums, films, or disambiguation pages.
    Returns empty string if nothing suitable is found.
    """
    def is_song_page(summary: str) -> bool:
        lower = summary.lower()
        return any(p in lower for p in ["is a song", "single by", "recorded by", "written by"])

    def is_relevant_page(page, title: str, artist: str) -> bool:
        text = page.summary.lower()
        return title.lower() in text and artist.lower() in text

    def extract_sections(page) -> str:
        parts = [page.summary]
        for section in page.sections:
            if section.lower() in USEFUL_SECTIONS:
                content = page.section(section)
                if content:
                    parts.append(f"{section}:\n{content}")
        combined = "\n\n".join(parts)
        return combined[:2000]

    queries = [f"{title} {artist} song", f"{title} song", f"{title} {artist}"]

    for query in queries:
        try:
            page = wikipedia.page(query, auto_suggest=True)
            if is_song_page(page.summary) and is_relevant_page(page, title, artist):
                return extract_sections(page)
        except wikipedia.DisambiguationError as e:
            song_options = [opt for opt in e.options if "song" in opt.lower()]
            for opt in song_options:
                try:
                    page = wikipedia.page(opt, auto_suggest=False)
                    if is_relevant_page(page, title, artist):
                        return extract_sections(page)
                except Exception:
                    continue
        except Exception:
            continue

    return ""


def build_subgenre_map(genres: list, model) -> dict:
    """
    One model call at startup: given the catalog's genres, return a dict
    mapping each genre to a list of related genres (subgenres / siblings).
    """
    genre_list = ", ".join(sorted(genres))
    response = model.generate_content(
        f"Here are all the music genres in my catalog: {genre_list}\n\n"
        "For each genre, list which other genres from this list are closely related — "
        "subgenres, parent genres, or siblings with shared musical roots.\n\n"
        "Return ONLY a JSON object where each key is a genre and its value is a list "
        "of related genres from the same list. Example:\n"
        '{"hip-hop": ["rap", "funk"], "rap": ["hip-hop", "funk"]}\n\n'
        "Only use genres from the list above. Return nothing but the JSON."
    )
    text = response.text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)


REQUIRED_PREF_KEYS = {"favorite_genre", "favorite_mood", "target_energy", "target_tempo", "likes_acoustic"}


def extract_recommend_json(text: str) -> dict | None:
    """
    Look for a RECOMMEND: block in the model's response.
    Returns the parsed dict only if all required preference keys are present,
    None otherwise (treats incomplete JSON as no recommendation yet).
    """
    match = re.search(r"RECOMMEND:\s*(\{.*?\})", text, re.DOTALL)
    if match:
        try:
            prefs = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
        if REQUIRED_PREF_KEYS.issubset(prefs.keys()):
            return prefs
    return None


def run_agent():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in .env")

    genai.configure(api_key=api_key)

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    print("Loading songs...")
    songs = load_songs("data/songs.csv")
    genres = sorted({s["genre"] for s in songs})
    moods  = sorted({s["mood"]  for s in songs})

    model = genai.GenerativeModel(MODEL_NAME)
    rag_client = GeminiClient()

    print("Building genre relationship map...")
    subgenre_map = build_subgenre_map(genres, model)
    print(f"Genre map built: {json.dumps(subgenre_map, indent=2)}\n")

    # ------------------------------------------------------------------
    # Agent loop
    # ------------------------------------------------------------------
    system = (
        "You are a friendly music recommendation assistant. "
        "Your job is to recommend songs from a catalog based on the user's preferences.\n\n"
        "IMPORTANT RULES — follow these exactly:\n"
        "1. NEVER list song titles, artist names, or music recommendations in your own responses. "
        "The system will display songs automatically. Your only job is to ask questions.\n"
        "2. You MUST collect all five of these before outputting RECOMMEND:\n"
        "   a. favorite_genre — ask which genre they want (ONLY from the genre list below)\n"
        "   b. favorite_mood — ask what mood they want (ONLY from the mood list below)\n"
        "   c. target_energy — how energetic (0.0 = very calm, 1.0 = very intense)\n"
        "   d. target_tempo — how fast in BPM (e.g. 70 slow, 128 dance, 160 fast)\n"
        "   e. likes_acoustic — acoustic/unplugged or electronic/produced sound?\n"
        "3. Ask one or two questions at a time. Do NOT output RECOMMEND: until you have "
        "real answers for all five fields.\n\n"
        f"Available genres: {', '.join(genres)}\n"
        f"Available moods: {', '.join(moods)}\n\n"
        "Once you have all five answers, output ONLY this on its own line — no song names:\n"
        "RECOMMEND: {\"favorite_genre\": \"jazz\", \"favorite_mood\": \"relaxed\", "
        "\"target_energy\": 0.4, \"target_tempo\": 90, \"likes_acoustic\": true}\n\n"
        "After the system shows results, describe what was found and ask if they want changes. "
        "If they want something different, ask what to change and output a new RECOMMEND: block."
    )

    chat = model.start_chat()
    # Inject the system prompt as the first exchange
    chat.send_message(system)

    print("Music Recommendation Agent — type 'quit' to exit\n")

    response = chat.send_message("Hi, I'd like some music recommendations.")
    print(f"\nAssistant: {response.text}")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"quit", "exit", "q"}:
            print("Goodbye!")
            break

        response = chat.send_message(user_input)
        reply = response.text

        prefs = extract_recommend_json(reply)

        # Guardrail: if the model listed songs directly instead of using RECOMMEND:,
        # intercept and redirect rather than showing hallucinated tracks.
        if not prefs and re.search(r"^\s*\d+\.", reply, re.MULTILINE):
            redirect = (
                "Do not list songs yourself — the system handles that. "
                "Instead, output a RECOMMEND: JSON block with the user's preferences "
                "so the system can search the catalog."
            )
            response = chat.send_message(redirect)
            reply = response.text
            prefs = extract_recommend_json(reply)
            if not prefs:
                print(f"\nAssistant: {reply}")
                continue

        if prefs:
            # Strip the RECOMMEND: block from what gets printed
            display = re.sub(r"RECOMMEND:\s*\{.*?\}", "", reply, flags=re.DOTALL).strip()
            if display:
                print(f"\nAssistant: {display}")

            # Show captured preferences and ask user to confirm before searching
            print(
                f"\n[Captured preferences]\n"
                f"  Genre:    {prefs['favorite_genre']}\n"
                f"  Mood:     {prefs['favorite_mood']}\n"
                f"  Energy:   {prefs['target_energy']}  (0.0 calm → 1.0 intense)\n"
                f"  Tempo:    {prefs['target_tempo']} BPM\n"
                f"  Acoustic: {prefs['likes_acoustic']}\n"
            )
            confirm = input("Does this look right? (yes / or tell me what to fix): ").strip()
            if confirm.lower() not in {"yes", "y", "yeah", "yep", "yup", "correct", "looks good"}:
                # Feed the correction back into the chat and loop again
                response = chat.send_message(confirm)
                reply = response.text
                print(f"\nAssistant: {reply}")
                continue

            # Call the scoring function directly
            results = recommend_songs(prefs, songs, k=5, subgenre_map=subgenre_map)

            # Print results with match scores and RAG explanation for each
            print("\nTop matches from catalog:\n")
            result_lines = ["Here are the top 5 matches from the catalog:\n"]
            for i, (song, score, explanation) in enumerate(results, 1):
                bar_len = int(score * 20)
                bar = "#" * bar_len + "-" * (20 - bar_len)
                print(
                    f"{i}. {song['title']} by {song['artist']}\n"
                    f"   Match: [{bar}] {score:.2f}/1.0\n"
                    f"   {explanation}"
                )

                profile_snippet = (
                    f"Song: {song['title']} by {song['artist']}\n"
                    f"Genre: {song['genre']}, Mood: {song['mood']}\n"
                    f"Energy: {song['energy']}, Tempo: {song['tempo_bpm']} BPM, "
                    f"Acousticness: {song['acousticness']}\n\n"
                    f"User preferences:\n"
                    f"Favorite genre: {prefs['favorite_genre']}, "
                    f"Favorite mood: {prefs['favorite_mood']}\n"
                    f"Target energy: {prefs['target_energy']}, "
                    f"Likes acoustic: {prefs['likes_acoustic']}"
                )
                snippets = [("song_and_user_profile", profile_snippet)]

                wiki = fetch_song_context(song['title'], song['artist'])
                if wiki:
                    snippets.append(("wikipedia", wiki))
                    wiki_label = "[RAG + Wikipedia]"
                else:
                    wiki_label = "[RAG]"

                rag_explanation = rag_client.answer_from_snippets(
                    f"Why is '{song['title']}' by {song['artist']} "
                    f"a good recommendation for this user?",
                    snippets,
                )
                print(f"   {wiki_label} {rag_explanation}\n")

                result_lines.append(
                    f"{i}. {song['title']} by {song['artist']} (score: {score:.2f}/1.0)\n"
                    f"   {explanation}"
                )
            result_text = "\n".join(result_lines)

            # Feed results back so Gemma can present them
            response = chat.send_message(result_text)
            print(f"\nAssistant: {response.text}")

        else:
            print(f"\nAssistant: {reply}")


if __name__ == "__main__":
    run_agent()
