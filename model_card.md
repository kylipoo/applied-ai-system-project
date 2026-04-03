# 🎧 Model Card: Music Recommender Simulation

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

It also handles energy-first listeners well. After reweighting energy to 40%, a user who cares most about how a song _feels_ (high-drive, fast-paced) will surface strong matches even across genre lines — Storm Runner or Gym Hero appearing near the top for an energetic profile makes sense even if the genre isn't an exact fit.

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
  - **High-Energy Pop**:![alt text](<Screenshot 2026-04-03 at 11.10.45 AM.jpg>)
  - **Chill Lofi**: ![alt text](<Screenshot 2026-04-03 at 11.10.51 AM.jpg>)

- **High-Energy Pop vs Deep Intense Rock:** Both profiles want high energy (0.90 vs 0.92) and neither likes acoustic. The difference is genre and mood — Pop wants happy, Rock wants intense. Because energy carries the highest weight (0.40) and genre only 0.20, some high-energy songs that don't match either genre can still score competitively for both profiles. The Rock profile correctly pulls intense rock tracks like "Storm Runner" and "Holding Out for a Hero," while the Pop profile favors upbeat tracks — but the energy overlap means both profiles can occasionally surface the same songs.
  - **High-Energy Pop**: ![alt text](<Screenshot 2026-04-03 at 11.10.45 AM.jpg>)
  - **Deep Intense Rock**: ![alt text](<Screenshot 2026-04-03 at 11.10.56 AM.jpg>)

- **Chill Lofi vs Lofi Rager:** Both want lofi, but the Lofi Rager wants intense mood and 0.90 energy — which no lofi song in the catalog actually has. Every lofi track is chill or focused at low energy (~0.35–0.42), so the Lofi Rager\'s mood score is always 0. The system falls back on energy proximity alone, returning the same lofi songs as the Chill Lofi profile but ranked differently. The outputs look similar on the surface but for completely different (and broken) reasons.
  - **Chill Lofi**: ![alt text](<Screenshot 2026-04-03 at 11.10.51 AM.jpg>)
  - **Lofi Rager**: ![alt text](<Screenshot 2026-04-03 at 11.22.03 AM.jpg>)

- **Deep Intense Rock vs Lofi Rager:** Both target high energy (~0.90+) and non-acoustic. Rock gets excellent results because the catalog has many intense rock songs that match all its attributes. The Lofi Rager, despite having the same energy target, gets poor results because there are no high-energy lofi songs: It is a paradox because Lofi tends to be low-energy. This pair best shows how catalog coverage — not just the scoring formula — determines whether a profile gets useful recommendations.
  - **Deep Intense Rock**: ![alt text](<Screenshot 2026-04-03 at 11.10.56 AM.jpg>)
  - **Lofi Rager**: ![alt text](<Screenshot 2026-04-03 at 11.22.03 AM.jpg>)

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
```
