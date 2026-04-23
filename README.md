# VibeCheck 3.6 — AI-Augmented Music Recommender

## Original Project (Modules 1–3)

The base of this project is **VibeCheck 3.6**, a Music Recommender Simulation built in the earlier modules. It is a rule-based recommender that scores every song in a 27-song catalog against a five-field user preference profile (favorite genre, favorite mood, target energy 0–1, target tempo in BPM, and whether the user prefers acoustic-sounding music) and returns the top-k best matches with a template explanation.

The original scoring uses a weighted formula — 40% genre, 25% mood, 20% energy, 10% tempo, 5% acousticness — where genre and mood are binary (exact match or zero) and energy, tempo, and acousticness use linear proximity. Its goal was to demonstrate transparent, traceable recommendation logic; every score can be broken down into its five components.

---

## Title and Summary

**VibeCheck 3.6** is a music recommender that now combines the original numeric scoring engine with an AI layer powered by Google's Gemma model. Instead of asking users to fill out a rigid preference form, a chat agent interviews the user in natural language, and every recommendation is explained with context pulled from the catalog and Wikipedia.

This matters because the original v1 had a hard failure mode: binary genre matching meant that asking for "jazz" buried every blues song at 0.0, even though the two genres share harmonic roots. The RAG layer fixes that failure directly by letting an LLM decide what counts as a neighboring genre, while keeping the transparent numeric scoring intact underneath.

---

## Architecture Overview

![alt text](<assets/Screenshot 2026-04-20 at 7.18.32 PM.jpg>)

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

5. **Run the agent (enhanced version):**

   ```bash
   python src/agent.py
   ```

6. **Run the original (optional, for comparison):**

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

![alt text](<assets/Screenshot 2026-04-20 at 8.39.06 PM.jpg>)

In v1 this query would have returned 0.0 on genre for every blues song. With the subgenre map, B.B. King surfaces at the top — exactly the failure mode the redesign was built to fix.

### Example 2 — High-energy pop (clean match)

**Input (chat):**

> Give me something upbeat and happy, pop, really high energy like 0.9, around 128 BPM, not acoustic.

**Output (top results):**
![alt text](<assets/Screenshot 2026-04-20 at 8.33.57 PM.jpg>)

### Example 3 — Conflicting profile (lofi genre, intense mood):

**Input (chat):**

> I want lo-fi but something intense and high-energy, 140 BPM, not acoustic.
> This was the main focus and motivation for why I wanted to improve upon the music recommender simulator. My previous calculation for getting the top k picks was a binary yes/no match regarding genre and numerics for energy and tempo.

**Output:**

First, here is when I ran main.py (the original scoring algorithm):

![alt text](<assets/Screenshot 2026-04-20 at 8.51.06 PM.jpg>)

The scores are fairly middling, and are largely focused on the attributes that can be scored (energy, tempo). None of them have a genre match.

This screenshot is when I ran agent.py (the revised algorithm):

![alt text](<assets/Screenshot 2026-04-20 at 8.50.54 PM.jpg>)

Of particular note is that the top scoring song, "Lose yourself" by Eminem is considered a valid candidate now, thanks to the agent performing a genre mapping algorithm, acknowledging hip-hop is often intertwined with lofi so while it's not possible to get a genuine lofi song that has an intense mood, the recommender still tells you "you might like this song because its genre and lofi often go hand in hand."

---

### Example 4 — Subgenres

**Input (chat):**

> I want a jazz song but it's moody, 0.5 energy (lower end energy), acoustic, and a tempo of 75.
> It is a blues song in every attribute EXCEPT genre.

**Output:**

First, here is when I ran main.py (the original scoring algorithm):

![alt text](<assets/Screenshot 2026-04-20 at 9.03.58 PM.jpg>)

This screenshot is when I ran agent.py (the revised algorithm):

![alt text](<assets/Screenshot 2026-04-20 at 9.06.16 PM.jpg>)

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

## Reliability

The system has four reliability mechanisms layered across input, output, and evaluation — the rubric asks for one, the codebase has several:

**Input validation.**

- [`extract_recommend_json`](src/agent.py#L86) rejects any `RECOMMEND:` block missing one of the five required preference keys (`favorite_genre`, `favorite_mood`, `target_energy`, `target_tempo`, `likes_acoustic`). A half-parsed JSON blob never reaches the scorer — it just falls through as "no recommendation yet" and the conversation continues.
- The **confirm-before-search** step at [agent.py:203-209](src/agent.py#L203) echoes captured preferences back to the user before `recommend_songs` runs. This catches mis-parsed decimals (e.g. `0.9` → `9`) and lets the user correct Gemma mid-conversation instead of silently getting bad matches.

**Output guardrails.**

- The **hallucinated-songs guardrail** at [agent.py:176-187](src/agent.py#L176) uses the regex `^\s*\d+\.` to detect numbered lists in Gemma's reply and re-prompts the model to emit a `RECOMMEND:` block instead. Without this, Gemma will happily invent songs that aren't in the catalog; with it, the only songs a user ever sees are ones that came out of the deterministic scorer.
- The **Wikipedia disambiguation filter** [`is_song_page`](src/agent.py#L40) checks retrieved page summaries for phrases like `"is a song"`, `"single by"`, or `"recorded by"` before accepting them. This prevents film pages, album pages, or unrelated disambiguation drift from leaking into the RAG explanation — the RAG layer degrades to "no Wikipedia context" rather than explaining the song with irrelevant text.
- The prompt in [llm_client.py:39-49](src/llm_client.py#L39) explicitly instructs the model to **"not invent any information not present in the snippets,"** grounding every generated explanation in the song attributes and (optional) Wikipedia summary that were actually retrieved.
- **Input validation**: The system prompt at [agent.py:131-152](src/agent.py#L131) frames Gemma as "a friendly music recommendation assistant" whose job is narrowly defined as recommending songs from the catalog. This role-framing means off-topic questions get deflected back to the task rather than answered. In the example screenshot below, I asked the AI agent "how do I bake a cake?" and rather than go off topic, it re-iterated its question of what song attributes I wanted. I was inspired to add this feature after I learned how some people would abuse customer support agents to help them with math problems instead of inquiring about a product or doing anything the agent was meant to actually do.
  - ![alt text](<assets/Screenshot 2026-04-21 at 2.16.01 PM.jpg>)
  - The next screenshot shows an example of a correct query. It has 5 parameters, and matches any of the available keywords/has the right typing.
    - ![alt text](<assets/Screenshot 2026-04-21 at 2.23.34 PM.jpg>)

**Evaluation script.**

- [src/main.py](src/main.py) runs the deterministic scorer across six contrasting user profiles — High-Energy Pop, Chill Lofi, Deep Intense Rock, Lofi Rager, Jazz Purist (Blues-Compatible), and Hip-Hop Head (Rap-Compatible) — and prints the top-5 ranked output for each. The last two profiles specifically exercise the subgenre-map code path, so running `python src/main.py` is effectively a regression check that related genres still get partial credit.

---

## Testing Summary

**What's automated.** [tests/test_recommender.py](tests/test_recommender.py) covers the core scoring contract with two tests: that `recommend()` returns songs sorted by score, and that `explain_recommendation()` returns a non-empty string. These run against the OOP `Recommender`/`UserProfile`/`Song` dataclasses and pass on the current implementation.

**What I tested by hand.** Six user profiles across the pipeline — High-Energy Pop, Chill Lofi, Deep Intense Rock, Lofi Rager, Jazz Purist, and Hip-Hop Head (the last two are the genre-proximity failure cases from v1). Screenshots of each are in the repo root.

**What worked.**

- The subgenre map consistently surfaced blues for jazz queries and rap for hip-hop queries, which was the headline goal.
- Wikipedia retrieval hits the right page ~80% of the time on mainstream songs (The Weeknd, Kendrick Lamar, Queen). The `is_song_page()` filter in [agent.py:40](src/agent.py#L40) catches most cases where it tries to hand back a movie or album page instead.
- The `RECOMMEND:` JSON contract between Gemma and Python held up well — the five-field guard in `extract_recommend_json` cleanly rejects incomplete blocks.

**What didn't.**

- Wikipedia strikes out on obscure catalog tracks (`Sunrise City by Neon Echo`, `Library Rain by Paper Lanterns`) because those are fictional entries I added. The code degrades to looking for vaguely related articles,returns warning messages of no explicitly identified parsers.
- Gemma occasionally ignores the "don't list songs yourself" rule on the first turn and has to be re-prompted by the guardrail. It's caught, but it's a round-trip of latency.
- Conflicting profiles (lofi + intense) still produce mediocre results. The planned "dual-pass retrieval" from the v1 README isn't implemented — it's one of the things I'd build next.

**What I learned.** LLM-assisted retrieval is best used for the fuzzy, linguistic parts of the problem (what's close to what, why does this fit) while crisp scoring stays deterministic. When I tried to push more of the ranking logic into the model, results got worse and harder to debug. The split — rules for math, model for meaning — held up better than I expected.

---

## Reflection

The biggest shift in how I think about AI after this project: **the LLM is most useful where the rules are impossible to enumerate.** I spent the v1 version trying to list every genre relationship and gave up — there are too many and they're too fuzzy. One API call that returns `{"jazz": ["blues"], ...}` solved in seconds what a hand-written mapping couldn't.

At the same time, the places where I let the model take over the most are the places I had to add the most guardrails. Gemma will invent songs if you let it, misread decimals, and drift from the task if the conversation gets long. Every "smart" behavior I added to the agent came with a corresponding safety net (the guardrail regex, the confirm-preferences step, the JSON schema validation). The project ended up being as much about bounding the model as about using it.

### How I Used AI During Development

I used AI in three concrete modes across this project:

- **Design.** The overall RAG architecture was brainstormed in chat before any code was written — the idea of building the subgenre map at runtime rather than hard-coding it, the decision to keep the deterministic scorer under the LLM instead of replacing it, and the guardrail strategy (input validation + role priming + hallucination regex) all came out of those design conversations.
- **Code generation.** Scaffolding for the agent chat loop, the Wikipedia retrieval function, the RAG prompt structure, and the JSON-extraction regex were all AI-generated starting points that I then edited and patched against real failure cases.
- **Model selection.** When I hit request limits on one model mid-development, I asked chat for guidance on alternatives and pivoted to Gemma as the final choice. That unblocking conversation is the reason `gemma-3-27b-it` is the model in [src/llm_client.py:12](src/llm_client.py#L12).

### Helpful AI Suggestion: Catalog Guardrails

An AI suggestion that was helpful was adding guardrails around what data the agent was free to reference.

- Prior to adding guardrails, the music recommender agent would output information not fed in by the dataset. For example, when I was looking for high energy pop, the AI response hallucinated artists and worst case scenario, songs not even in my csv file.
  - ![alt text](<assets/Screenshot 2026-04-21 at 2.49.42 PM.jpg>) (The artists Dua Lipa, Harry Styles, Lizzo, etc are not in my csv file).
- Here is an example of a helpful recommendation. It's the same original prompt of high energy prompt but after I've added guardrails. There's less hallucinated information, all songs I checked are in the dataset.
  - ![alt text](<assets/Screenshot 2026-04-22 at 6.52.18 PM.jpg>)

### Flawed AI Suggestion: Wikipedia-First Retrieval

When I was designing the RAG layer, AI proposed a clean Wikipedia-backed retrieval format that assumed every song in the catalog would have a dedicated Wikipedia article — one `wikipedia.page(title)` call returns the summary, done. In practice this broke in three places:

1. **Fictional catalog entries.** Roughly half the catalog is lesser known tracks (Sunrise City, Library Rain, Focus Flow). These have no Wikipedia page at all, so the call just errored out.
2. **Disambiguation pages.** Even for real songs, a title often maps to multiple articles (film, album, unrelated song). The naive retrieval returned malformed responses or the wrong article entirely when Wikipedia served a disambiguation page. In one case, searching for "Library Rain" returned the Wikipedia page for "Purple Rain" by Prince — a completely different song — because it passed the basic "is this a song page?" check but nothing verified it was the _right_ song.
3. **Shallow explanations even when retrieval succeeded.** The initial suggestion used only the Wikipedia summary and instructed the model to add "one sentence of real-world context." When I tested this, the RAG explanations were barely better than the attribute-only fallback — the model was just rephrasing the numeric data rather than saying anything meaningful about the song itself.

I had to patch the retrieval in three places. The `is_song_page` filter at [agent.py:43-45](src/agent.py#L43) checks that the summary contains phrases like "is a song", "single by", or "recorded by" before accepting a result. The `DisambiguationError` handler at [agent.py:64-71](src/agent.py#L64) walks disambiguation options and picks ones labeled "song." And the `is_relevant_page` check at [agent.py:47-49](src/agent.py#L47) verifies that both the song title and artist name actually appear in the retrieved page — which is what caught the Purple Rain problem. For the shallow explanations, I expanded retrieval to pull named sections like `background`, `reception`, and `legacy` in addition to the summary, and updated the prompt to allow up to two sentences of Wikipedia context with the instruction to prefer specific details over vague praise. The lesson: when AI suggests pulling from an external knowledge source, it tends to assume the source is complete, unambiguous, and rich enough to be useful on its own. None of those held up.

### System Limitations and Future Improvements

#### What the RAG layer didn't fix, and what's next:

- **Binary mood matching.** The subgenre map fixed binary _genre_ matching but mood is still 1.0 or 0.0 — "moody" vs "relaxed" scores zero even though they're close. **Fix:** apply the same startup LLM call pattern to build a mood-relationship map.
- **Conflicting profiles still produce mediocre results.** A user asking for lofi + intense still gets a low-scoring compromise. **Fix:** implement the "dual-pass retrieval" I promised in v1 — split the top-k between the two conflicting preferences and explain the split.
- **Wikipedia gaps on fictional catalog entries.** The RAG explanation degrades to attribute-only for the made-up songs, losing its best hook. **Fix:** hand-write (or AI-generate once and cache) a short blurb per song so every track has context regardless of Wikipedia coverage, or if I were to really take the recommender to another level, have it call another agent specifically assigned to looking up information on the song.
- **RAG explanations aren't mechanically verified.** The "do not invent" instruction is prompt-only — if Gemma hallucinates, nothing catches it. **Fix:** add a self-critique pass where a second model call checks whether each claim in the explanation appears in the provided snippets, and rejects the explanation if not.
- **Can't prove which tracks are real.** Claude added some songs like "Gym Hero" by Max Pulse into the songs csv file, but the recommender treats it the same as real tracks from the likes of Eminem, Kendrick Lamar. So while I have addressed the agent making up songs outside the dataset, there hasn't been anything done for when the dataset itself has holes. This relates to the wikipedia gap in the sense that I would use multiple sources to verify if the song in the dataset is real or not.

#### Potential misuses:

- **Off-task abuse**: A user could potentially try to repurpose the chatbot, asking it to write code, do homework or generate harmful content, as underneath it's a general-purpose LLM. I mitigiated potential off task abuse by adding guardrails framing Gemma to only focus on recommending music.
- **API abuse if deployed publicly**: A hostile user could potentially spam the chat endpoint to burn through the API quota, belonging to whoever deployed the system

#### Surprises encountered:

- **Simplicity of guardrail implementation**: I was expecting to need complex code, specialized classifiers, validation chains to constratin the agent. In practice, however, natural language in the system prompt did most of the heavy lifting, telling Gemma "you are a music recommendation assistant" was all that was needed to deflect off-topic questions. It is impressive how intuitive AI can be that even people without much development experience can get the hang of it.

- **Wikipedia failure reason**: Wikipedia potentially leading to disambiguation pages was the dominant failure mode, not quota or latency. Going in, I expected rate limits or slow responses to be my main issue. Instead, most RAG failures came from Wikipedia handing back the wrong article entirely — a film page, an album page, or a disambiguation list. The is_song_page filter was the single most important line of defensive code.

Problem-solving-wise, the lesson was to weigh my original work with that of AI's suggestions, determine what had to go, what would be neat to add. The v1 numeric scorer was transparent and correct for the cases it could handle. My first instinct was to replace it; my final design treats it as the foundation and uses the LLM to patch only the specific failure mode — binary genre matching — that the scorer couldn't solve on its own. Adding capability without removing legibility turned out to be the actual design problem.
