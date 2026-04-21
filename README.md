# VibeCheck 3.6 — RAG-Augmented Music Recommender

## Original Project (Modules 1–3)

The base of this project is **VibeCheck 3.6**, a Music Recommender Simulation built in the earlier modules. It is a rule-based recommender that scores every song in a 27-song catalog against a five-field user preference profile (favorite genre, favorite mood, target energy 0–1, target tempo in BPM, and whether the user prefers acoustic-sounding music) and returns the top-k best matches with a template explanation.

The original scoring uses a weighted formula — 40% genre, 25% mood, 20% energy, 10% tempo, 5% acousticness — where genre and mood are binary (exact match or zero) and energy, tempo, and acousticness use linear proximity. Its goal was to demonstrate transparent, traceable recommendation logic; every score can be broken down into its five components.

---

## Title and Summary

**VibeCheck 3.6** is a music recommender that now combines the original numeric scoring engine with a Retrieval-Augmented Generation (RAG) layer powered by Google's Gemma model. Instead of asking users to fill out a rigid preference form, a chat agent interviews the user in natural language, and every recommendation is explained with context pulled from the catalog and Wikipedia.

This matters because the original v1 had a hard failure mode: binary genre matching meant that asking for "jazz" buried every blues song at 0.0, even though the two genres share harmonic roots. The RAG layer fixes that failure directly by letting an LLM decide what counts as a neighboring genre, while keeping the transparent numeric scoring intact underneath.

---

## Architecture Overview

![alt text](<Screenshot 2026-04-20 at 7.18.32 PM.jpg>)

Three components, three jobs:

1. **Agent ([src/agent.py](src/agent.py))** — a Gemma-powered chat loop that replaces the old hard-coded profile list. On startup it asks Gemma to build a **genre-relationship map** from the catalog's actual genres (e.g. `{"hip-hop": ["rap", "funk"], "jazz": ["blues"], ...}`) which is passed into the scorer so that related genres get 0.7 partial credit instead of 0.0.
2. **Scorer ([src/recommender.py](src/recommender.py))** — the original numeric scoring formula, extended with one new branch: if an exact genre match fails, check the AI-generated subgenre map before falling back to 0.0.
3. **RAG Explainer ([src/llm_client.py](src/llm_client.py))** — for each recommended song, Wikipedia is queried for a real-world summary, and Gemma generates a grounded 2–3 sentence explanation from the song attributes + user preferences + (optional) Wikipedia snippet.

---

## Setup Instructions

1. **Clone the repo and enter the directory.**

   ```bash
   git clone <this-repo-url>
   cd applied-ai-system-project
   ```

2. **Install dependencies.** The code also uses `google-generativeai` and `python-dotenv` at runtime:

   ```bash
   pip install -r requirements.txt
   pip install google-generativeai python-dotenv
   ```

3. **Get a Gemini API key** from [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey).

4. **Create a `.env` file** in the project root:

   ```
   GEMINI_API_KEY=your_key_here
   ```

5. **Run the agent (RAG version):**

   ```bash
   python src/agent.py
   ```

6. **Run the non-RAG original (optional, for comparison):**

   ```bash
   cd src && python main.py
   ```

7. **Run the tests:**
   ```bash
   pytest tests/
   ```

---

## Sample Interactions

### Example 1 — The jazz/blues bridge (the motivating failure case)

**Input (chat):**

> I'm into moody jazz, something mellow, maybe 75 BPM, acoustic, not too intense — energy around 0.5.

**Captured preferences:**

```
Genre: jazz, Mood: moody, Energy: 0.5, Tempo: 75 BPM, Acoustic: true
```

**Output (top 2 of 5):**

![alt text](<Screenshot 2026-04-20 at 8.39.06 PM.jpg>)

In v1 this query would have returned 0.0 on genre for every blues song. With the subgenre map, B.B. King surfaces at the top — exactly the failure mode the redesign was built to fix.

### Example 2 — High-energy pop (clean match)

**Input (chat):**

> Give me something upbeat and happy, pop, really high energy like 0.9, around 128 BPM, not acoustic.

**Output (top results):**
![alt text](<Screenshot 2026-04-20 at 8.33.57 PM.jpg>)

### Example 3 — Conflicting profile (lofi genre, intense mood):

**Input (chat):**

> I want lo-fi but something intense and high-energy, 140 BPM, not acoustic.
> This was the main focus and motivation for why I wanted to improve upon the music recommender simulator. My previous calculation for getting the top k picks was a binary yes/no match regarding genre and numerics for energy and tempo.

**Output:**

First, here is when I ran main.py (the original scoring algorithm):

![alt text](<Screenshot 2026-04-20 at 8.51.06 PM.jpg>)

The scores are fairly middling, and are largely focused on the attributes that can be scored (energy, tempo). None of them have a genre match.

This screenshot is when I ran agent.py (the revised algorithm):

![alt text](<Screenshot 2026-04-20 at 8.50.54 PM.jpg>)

Of particular note is that the top scoring song, "Lose yourself" by Eminem is considered a valid candidate now, thanks to the agent performing a genre mapping algorithm, acknowledging hip-hop is often intertwined with lofi so while it's not possible to get a genuine lofi song that has an intense mood, the recommender still tells you "you might like this song because its genre and lofi often go hand in hand."

---

### Example 4 — Subgenres

**Input (chat):**

> I want a jazz song but it's moody, 0.5 energy (lower end energy), acoustic, and a tempo of 75.
> It is a blues song in every attribute EXCEPT genre.

**Output:**

First, here is when I ran main.py (the original scoring algorithm):

![alt text](<Screenshot 2026-04-20 at 9.03.58 PM.jpg>)

This screenshot is when I ran agent.py (the revised algorithm):

![alt text](<Screenshot 2026-04-20 at 9.06.16 PM.jpg>)

With the refactored algorithm, the agent goes "Hey wait, these songs basically are just blues! You should listen to these songs since besides genre, it's got everything you want!"

---

## Design Decisions

**Why keep the numeric scorer under the LLM instead of replacing it?**
The v1 scoring was one of my project's biggest strengths as it is fully transparent — every score decomposes into five components. Replacing it with "ask the LLM to rank the songs" would trade that transparency for a black box. The RAG layer sits _on top of_ the scorer: the LLM decides genre neighborhoods and writes explanations, but the actual ranking is still deterministic math.

**Why let the LLM build the subgenre map at startup instead of hard-coding it?**
Hard-coding `{"jazz": ["blues"], "hip-hop": ["rap"]}` would mean updating code every time the catalog grows. One startup call asks Gemma to look at the actual catalog genres and return a JSON map — this makes the system adapt to whatever data is loaded. The trade-off is a one-time API call cost and the occasional weird edge (e.g. does "indie pop" belong with "pop"? the model decides).

**Why 0.7 partial credit for subgenre matches?**
An exact genre match is 1.0, a totally unrelated genre is 0.0. 0.7 is high enough that a related genre can legitimately out-rank a non-matching one on genre alone, but low enough that two songs with the exact same genre preference still win. Tuning this value is the single biggest lever for how "adventurous" the recommendations feel.

**Why a confirm-before-search step in the agent loop?**
Gemma is good at conversation but occasionally mis-parses numbers (`0.9` becomes `9`, etc). The captured preferences are echoed back to the user before `recommend_songs` runs — one extra keystroke to catch drift. I chose friction over silent errors.

**Why a guardrail against the model listing songs itself?**
Without it, Gemma will happily invent songs that aren't in the catalog. The `^\s*\d+\.` regex in [agent.py:176](src/agent.py#L176) catches numbered lists in the reply and forces the model to emit a `RECOMMEND:` block instead. This was a case where letting the LLM speak freely was actively harmful.

---

## Testing Summary

**What's automated.** [tests/test_recommender.py](tests/test_recommender.py) covers the core scoring contract with two tests: that `recommend()` returns songs sorted by score, and that `explain_recommendation()` returns a non-empty string. These run against the OOP `Recommender`/`UserProfile`/`Song` dataclasses and pass on the current implementation.

**What I tested by hand.** Six user profiles across the pipeline — High-Energy Pop, Chill Lofi, Deep Intense Rock, Lofi Rager, Jazz Purist, and Hip-Hop Head (the last two are the genre-proximity failure cases from v1). Screenshots of each are in the repo root.

**What worked.**

- The subgenre map consistently surfaced blues for jazz queries and rap for hip-hop queries, which was the headline goal.
- Wikipedia retrieval hits the right page ~80% of the time on mainstream songs (The Weeknd, Kendrick Lamar, Queen). The `is_song_page()` filter in [agent.py:40](src/agent.py#L40) catches most cases where it tries to hand back a movie or album page instead.
- The `RECOMMEND:` JSON contract between Gemma and Python held up well — the five-field guard in `extract_recommend_json` cleanly rejects incomplete blocks.

**What didn't.**

- Wikipedia strikes out on obscure catalog tracks (`Sunrise City by Neon Echo`, `Library Rain by Paper Lanterns`) because those are fictional entries I added. The code degrades to a RAG-only explanation (no Wikipedia tag), which is acceptable but feels thinner.
- Gemma occasionally ignores the "don't list songs yourself" rule on the first turn and has to be re-prompted by the guardrail. It's caught, but it's a round-trip of latency.
- Conflicting profiles (lofi + intense) still produce mediocre results. The planned "dual-pass retrieval" from the v1 README isn't implemented — it's one of the things I'd build next.

**What I learned.** LLM-assisted retrieval is best used for the fuzzy, linguistic parts of the problem (what's close to what, why does this fit) while crisp scoring stays deterministic. When I tried to push more of the ranking logic into the model, results got worse and harder to debug. The split — rules for math, model for meaning — held up better than I expected.

---

## Reflection

The biggest shift in how I think about AI after this project: **the LLM is most useful where the rules are impossible to enumerate.** I spent the v1 version trying to list every genre relationship and gave up — there are too many and they're too fuzzy. One API call that returns `{"jazz": ["blues"], ...}` solved in seconds what a hand-written mapping couldn't.

At the same time, the places where I let the model take over the most are the places I had to add the most guardrails. Gemma will invent songs if you let it. It will misread decimals. It will drift from the task if the conversation gets long. Every "smart" behavior I added to the agent came with a corresponding safety net (the guardrail regex, the confirm-preferences step, the JSON schema validation). The project ended up being as much about bounding the model as about using it.

Problem-solving-wise, the lesson was to preserve what already works before adding AI on top. The v1 numeric scorer was transparent and correct for the cases it could handle. My first instinct was to replace it; my final design treats it as the foundation and uses the LLM to patch only the specific failure mode — binary genre matching — that the scorer couldn't solve on its own. Adding capability without removing legibility turned out to be the actual design problem.

Where human judgment still matters: a score can tell you two songs share the same energy and tempo, but it can't tell you one is from a video game that defined someone's childhood. The RAG layer narrows the gap — a Wikipedia blurb at least gives the model _something_ to reason about — but it doesn't close it. Numbers describe a song's surface; what makes a song matter still lives somewhere no feature vector can reach.
