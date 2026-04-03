# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Explain your design in plain language.

Some prompts to answer:

- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo
- What information does your `UserProfile` store
- How does your `Recommender` compute a score for each song
- How do you choose which songs to recommend

You can include a simple diagram or bullet list if helpful.

---

### Context:

- First, some context on how irl streaming platforms predict what users will listen to next. They have two methods: Collaborative filtering, content-based filtering.
  - Collaborative filtering: If two users have similar taste histories, what one enjoys is a good prediction for the other.
    - Build a user-item matrix (rows = each user, columns = songs, values = plays/ratings).
    - Find users with similar behavior patterns (cosine similarity, matrix factorization).
    - Recommend said items that similar users liked.
    - Strengths: Discover surprising recommendations across genres.
    - Weaknesses: Cold start problem (new users/items have no history), popularity bias towards mainstream content.
  - Content-based filtering: Because a user liked a song with certain attributes, find items with similar attributes.
    - Extract features from items (tempo, key, danceability, genre, etc)/
    - Build profile of what user has engaged with.
    - Recommend items with high feature similarity to that profile.
    - Strengths: Work for new items immediately, explainable ("Because you liked this upbeat pop..."), no need for other users' data.
    - Weaknesses: Over-specialization, can't discover genuinely new content.

### My Planned System:

- Each Song is scored using five features: genre, mood, energy, tempo, and acousticness.
- The UserProfile stores a matching set of preferences: favorite_genre, favorite_mood, target_energy, target_tempo (added after listening to criticism from inline agent), and likes_acoustic.
  - The sample profile used for testing: genre = pop, mood = happy, target energy = 0.85, target tempo = 120 BPM, likes_acoustic = False.
- Scoring runs each song through score_song(), which computes a weighted sum capped at 1.0:
  - 0.40 × genre_score + 0.25 × mood_score + 0.20 × energy_score + 0.10 × tempo_score + 0.05 × acoustic_score
  - Genre and mood are binary matches (1.0 or 0.0). Energy and tempo use proximity to the user's target value. Acousticness applies a soft penalty if the user dislikes acoustic songs.
  - All songs are scored, sorted descending, and the top k are returned.
- This is content-based filtering — recommendations are derived entirely from song attributes matched against a single user's preferences, with no data from other users involved.
  - The trade-off is explainability and privacy at the cost of serendipity. That being said, given that we are composing a service similar to spotify and youtube, that doesn't necessarily mean the user is completely blocked off from expanding their scope to other genres, they can always search for themselves.
- **Potential Biases**:
  - Genre can be a finnicky filter to assign a high weight to. The idea though was that oftentimes people will assign certain vibes just based on genre, like rock and roll would be fast and encourage defiance, pop would be talking about daily life experiences.
    - A song in the wrong genre can never outscore a mediocre same-genre song, even if the other attributes are a perfect match.
  - Data has 6 pop songs and 6 happy songs out of 17 total.
  - Mood matching is either "fits the mood or doesn't".
- **Diagram**:
  - ![alt text](<Screenshot 2026-04-02 at 2.11.38 PM.jpg>)

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

   ```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

- I created an anomaly profile where they wanted a "Lo-fi rager" which sounds contradictory because lo-fi is known for being calm and meant to be something you can play in the background while you do something else.
- I found that when I ran the algorithm recipe, that the scored results were comparatively lower.
- HOWEVER, when I redistributed the weights to give the energy more weight, this shifted the recommendations to be higher.

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

- Limitations encountered during planning:
  - I had run my original user profile with inline chat and they had a criticism that "intense rock" and "chill lofi" were differentiated for the wrong reasons (through target energy, not because it understood "intense" and "chill" as moods).
  - Mood is considered binary matching, a favorite mood of "happy" will consider both "intense" and "chill" as 0 equally.
  - Genre is too narrow. With "pop" as a target, a high-energy rock track would score worse than a mid-energy pop track. Just because the genre is different doesn't mean the user wouldn't have liked the "rock" example.
  - No tempo signal. Stuff like intense rock and chill lofi would be most cleanly separated by tempo (152 bpm and 72 bpm respectively).
  - Now I have refined profile to have target_tempo. It can now distinguish "high energy + fast tempo" from "high energy + slow tempo" and avoids the issue where energy alone conflates different types of intensity.

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this

---

- Building this recommender showed me that turning data into predictions is really about encoding assumptions and discerning patterns. Every weight in score_song is a judgement call: The system scores songs by weighing numeric attributes such as energy or tempo against a user's stated preferences, then ranks by closeness. That sounds objective, but then the weights are the deciding factor in what "close enough" means. Doubling the energy from 0.2->0.4 completely changed song scores and which ones surfaced, even for users where said genre was top priority. The prediction isn't from the data, it's from choices basked into the formula.
- The bias risk follows directly from that. If the catalog underrepresents certain genres or moods, users with those preferences get worse results through no fault of the algorithm — it's just working with incomplete data. The "Lofi Rager" profile in the code is a clear example: a user who wants intense, high-energy lofi gets broken recommendations because that niche doesn't exist in the dataset. In a real product, that pattern would fall hardest on listeners with niche or non-mainstream tastes, while users who prefer well-catalogued genres like pop consistently get better results. The system appears fair because it applies the same formula to everyone, but equal treatment of unequal data still produces unequal outcomes.

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---
- VibeCheck 3.6

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

- This model suggests the top k songs (I can change how much is returned) from a small catalog based on a user's preferred genre, mood, energy and after consulting inline chat, now also checks **target_tempo**. It is for classroom exploration only, not meant to be reflective of real-world case-studies.


## 3. How It Works (Short Explanation)

For each song in the catalog, the recommender gives it a score between 0 and 1 by comparing five things about the song to what the user told us they like. The higher the score, the better the match.

**What it looks at in each song:**
- Genre (e.g. pop, rock, lofi)
- Mood (e.g. happy, intense, chill)
- Energy level — a number from 0 to 1 representing how high-energy or low-key the song feels
- Tempo — how fast the song is, measured in beats per minute
- Acousticness — how acoustic vs. electronic the song sounds

**What it knows about the user:**
- Their favorite genre and favorite mood
- Their preferred energy level (a target they want songs to match)
- Their preferred tempo
- Whether they like acoustic-sounding music or not

**How it turns those into a number:**

Each of the five features gets its own mini-score from 0 to 1. Genre and mood are all-or-nothing — a song either matches or it doesn't. Energy, tempo, and acousticness are gradual — a song that's close to your target scores nearly as well as a perfect match, and one that's far away scores lower.

Those five mini-scores are then combined into one final score using a weighted average. Energy is weighted the most heavily (40%), meaning a song that matches your energy preference will rise to the top even if the genre or mood isn't a perfect fit. Mood is second (25%), followed by genre (20%), tempo (10%), and acousticness (5%). The top-scoring songs are returned as your recommendations.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

- There are 27 songs in songs.csv.
- I added 17 more songs.
- The genres/moods MOST represented are pop, lo-fi, rock. Some suggestions AI gave along the way included jazz.
- The taste this data mostly reflects are contemporary audiences.

## 5. Strengths
You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits


---

The recommender works best when a user's preferences are clear and consistent — particularly when their favorite genre, mood, and energy level all point in the same direction. The High-Energy Pop profile is a good example: songs like Moskau and Rasputin scored near-perfectly because they matched on every dimension at once, and the results felt intuitive.

It also handles energy-first listeners well. After reweighting energy to 40%, a user who cares most about how a song *feels* (high-drive, fast-paced) will surface strong matches even across genre lines — Storm Runner or Gym Hero appearing near the top for an energetic profile makes sense even if the genre isn't an exact fit.

The scoring is also fully transparent. Every score can be broken down into its five components, and the explanation text tells the user exactly why a song was recommended. There are no hidden factors or black-box behavior — a teacher or student can trace any result back to the math.

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

- Genre and mood matches are an all-or-nothing match (either 1.0 or 0.0). So a song that's "jazz" when you want "blues" would score identical to a song in a totally unrelated genre. This ignores real inspirations that genres could have taken from each other.
- Placing too much stock in energy in my experiment of changing weights means that unrelated results get scored higher.
- Will require very precise preferences. For example, conflicting profiles with intense mood/high energy and being in the lo-fi genre will choose results where the mood always scores 0. The system has no fallback, it just returns songs with the closest energy.
- Certain genres, moods or energy are sparse in the data-set, so users with preferences like reggae or classic might get worse recommendations.

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

- I added multiple user profiles with differing genre preferences and went through each one seeing if the calculated results matched my expectations.
- **High-Energy Pop vs Chill Lofi:** These two profiles are complete opposites. The Pop profile targets energy 0.90 with non-acoustic pop songs in a happy mood, while Chill Lofi targets energy 0.35 with acoustic lofi tracks in a chill mood. The outputs reflected this cleanly — Pop surfaced high-tempo, electric tracks like "Gym Hero" and "Moskau," while Lofi returned quiet, acoustic songs like "Library Rain" and "Midnight Coding." The contrast makes sense because every attribute (energy, genre, mood, acousticness) points in opposite directions.
  -  **High-Energy Pop**:![alt text](<Screenshot 2026-04-03 at 11.10.45 AM.jpg>)
  - **Chill Lofi**: ![alt text](<Screenshot 2026-04-03 at 11.10.51 AM.jpg>)


- **High-Energy Pop vs Deep Intense Rock:** Both profiles want high energy (0.90 vs 0.92) and neither likes acoustic. The difference is genre and mood — Pop wants happy, Rock wants intense. Because energy carries the highest weight (0.40) and genre only 0.20, some high-energy songs that don't match either genre can still score competitively for both profiles. The Rock profile correctly pulls intense rock tracks like "Storm Runner" and "Holding Out for a Hero," while the Pop profile favors upbeat tracks — but the energy overlap means both profiles can occasionally surface the same songs.
  - **High-Energy Pop**: ![alt text](<Screenshot 2026-04-03 at 11.10.45 AM.jpg>)
  - **Deep Intense Rock**:  ![alt text](<Screenshot 2026-04-03 at 11.10.56 AM.jpg>)

- **Chill Lofi vs Lofi Rager:** Both want lofi, but the Lofi Rager wants intense mood and 0.90 energy — which no lofi song in the catalog actually has. Every lofi track is chill or focused at low energy (~0.35–0.42), so the Lofi Rager\'s mood score is always 0. The system falls back on energy proximity alone, returning the same lofi songs as the Chill Lofi profile but ranked differently. The outputs look similar on the surface but for completely different (and broken) reasons.
  - **Chill Lofi**: ![alt text](<Screenshot 2026-04-03 at 11.10.51 AM.jpg>)
  - **Lofi Rager**:  ![alt text](<Screenshot 2026-04-03 at 11.22.03 AM.jpg>)

- **Deep Intense Rock vs Lofi Rager:** Both target high energy (~0.90+) and non-acoustic. Rock gets excellent results because the catalog has many intense rock songs that match all its attributes. The Lofi Rager, despite having the same energy target, gets poor results because there are no high-energy lofi songs: It is a paradox because Lofi tends to be low-energy. This pair best shows how catalog coverage — not just the scoring formula — determines whether a profile gets useful recommendations.
  - **Deep Intense Rock**:  ![alt text](<Screenshot 2026-04-03 at 11.10.56 AM.jpg>)
  - **Lofi Rager**:  ![alt text](<Screenshot 2026-04-03 at 11.22.03 AM.jpg>)



- Example for high-energy pop calculations:
- ![alt text](<Screenshot 2026-04-03 at 11.16.33 AM.jpg>)

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes
---
- I would add more diverse genres and balance the current selection out.
- I would add more attributes like what kind of instruments are being used, the volume, if the song contains any mature themes.

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

```

Building this system revealed how every weight/score is a trade-off — boosting energy matching means a song with the perfect vibe but the "wrong" genre can outrank something that's a much better fit on paper. That tension made me realize how much a real music recommender has to balance, and how those decisions are never neutral.

It also changed how I think about the scope of the problem. Music taste isn't static — genres like K-pop and video game OSTs have exploded in popularity and carry cultural context that a set of numeric attributes can't capture. A system built today on today's catalog will drift out of alignment with listeners faster than the weights can be retuned.

That's where human judgment still matters most. A score derived from energy, tempo_bpm, and valence can tell you a song is similar on the surface, but it can't tell you that a track feels like a rainy afternoon, or that it's the one song from a game that defined someone's childhood. Firsthand listening — and the editorial instinct that comes with it — carries meaning that no feature vector can fully represent.
