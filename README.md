# Music Recommender Simulation

## Project Summary

This project is a music recommendation system that takes a user preference profile and scores every song in a catalog against it, returning the top-k best matches. The user specifies five preferences: favorite genre, favorite mood, target energy level (0–1), target tempo in BPM, and whether they prefer acoustic-sounding music. Each song in the catalog is then evaluated against those preferences using a weighted scoring formula across those same five features, producing a score between 0.0 and 1.0. The songs with the highest scores are returned as recommendations, along with a plain-text explanation of why each one was selected.

The scoring weights are:

| Feature          | Weight |
| ---------------- | ------ |
| Genre match      | 40%    |
| Mood match       | 25%    |
| Energy proximity | 20%    |
| Tempo proximity  | 10%    |
| Acousticness fit | 5%     |

Genre and mood are evaluated as exact binary matches — a song either matches or it doesn't. Energy, tempo, and acousticness use linear proximity, so songs that are close to the user's target still score well rather than dropping to zero.

The catalog currently contains 27 songs across genres including pop, rock, lo-fi, jazz, hip-hop, synthwave, ambient, latin, funk, grunge, reggae, and classical.

---

## Current Limitations

The system works well for users with clear, consistent preferences that align with what is well-represented in the catalog. However, several limitations become apparent under closer examination:

**Binary genre and mood matching.** Genre and mood are treated as exact labels. A jazz song scores 0.0 on genre for a user who wants blues, even though the two genres share harmonic roots and would feel similar to most listeners. A song labeled "moody" scores 0.0 for a user who wants "relaxed," even if the two are closer in feel than "moody" and "intense." There is no concept of genre proximity or mood similarity — only exact matches. This is problematic for users trying to branch out, as it means they'll be stuck with a specific genre when stuff like Blues was inspired by Jazz and Rap being a subgenre of Hip-hop.

- I tried a profile where the user's preferred genre is Jazz yet the other attributes often align strongly with the blues sample data. The screenshot shows the score matches:
  - ![alt text](<Screenshot 2026-04-14 at 3.20.12 PM.jpg>)
- I tried another profile where the user likes the hip-hop genre, but the other attributes align with the rap sample data. The screenshot shows the score matches:
  - ![alt text](<Screenshot 2026-04-14 at 3.30.15 PM.jpg>)

**No semantic understanding of songs.** Two songs can score identically across all five numeric features and yet feel completely different. A 140 BPM rock song written as a victory anthem and one written as a descent into chaos look the same to this system. The numeric features describe the surface of a song, not what it actually means or how it actually feels.

**Conflicting profiles produce degraded results.** A user profile that is internally contradictory — such as wanting lo-fi genre but high energy and intense mood — will consistently score 0.0 on mood, since lo-fi songs in the catalog are labeled as chill or focused. The system has no fallback and no way to recognize that the profile itself is in tension.

**Sparse genres get poor results.** Genres like reggae, classical, and ambient are underrepresented in the catalog. A user with preferences in those areas will receive recommendations based on secondary features rather than genuine genre matches.

**Template-based explanations are mechanical.** The explanation for every recommendation follows the same rigid structure: it lists which attributes matched or didn't. It cannot say anything nuanced about why a song actually fits — only that the numbers aligned.

---

## Planned Enhancements: RAG Integration

To address these limitations, the next version of this system will incorporate Retrieval-Augmented Generation (RAG). Rather than relying solely on numeric scoring, the system will retrieve relevant text-based context about songs and genres, and use a language model to reason over that context alongside the numeric scores. Three specific features are planned:

### 1. Genre Relationship Retrieval

A small knowledge base will be built that describes the relationships between genres — which genres share origins, which overlap in sound, and how closely related they are. When a user requests a genre, the system will retrieve context about that genre and its neighbors, and use it to apply partial credit instead of a binary match. For example, a blues song would score meaningfully higher than 0.0 for a user who wants jazz, because the retrieval step would surface the shared harmonic vocabulary between the two. This directly fixes the hardest limitation of the current scoring model.

This also improves handling of conflicting preference profiles through conflict detection and dual retrieval. When a profile is submitted, the RAG layer retrieves genre context from the knowledge base — for example, looking up "lo-fi" surfaces context like _"lo-fi: characterized by chill, low-stimulation sound, commonly used for studying."_ The LLM then checks that against the requested mood and flags a conflict if the two are incompatible.

When a conflict is detected, the system runs two passes through the existing scoring instead of one:

- **Pass 1** — prioritize genre match, return the top lo-fi songs
- **Pass 2** — prioritize mood match, return the top intense songs

The results are merged into the final k slots (for example, 3 lo-fi + 2 intense for k=5), and the explanation clearly communicates the split: _"Your profile requested lo-fi with intense mood — these are in tension, so your recommendations are split. The first group matches your genre preference; the second matches your intensity preference."_ The numeric scoring system itself remains unchanged throughout — RAG handles detection, retrieval, and explanation on top of it.

### 2. Per-Song Context Blurbs

Each song in the catalog will be given a short text description capturing things the numeric features cannot: the emotional context of the song, what it's commonly associated with, its cultural background, and what kind of listening moment it fits. When two songs score similarly on numeric features, the system will retrieve their blurbs and use them to distinguish between songs that are numerically identical but emotionally different — the gap identified in the current limitations.

### 3. RAG-Powered Explanation Generation

Instead of the current template-based explanations, the top-k recommendations will be passed to a language model along with the song blurbs and the user's stated preferences. The model will generate natural, context-aware explanations for each recommendation — explaining not just that the numbers matched, but why this song actually fits what the user is looking for, in terms a listener would recognize.
