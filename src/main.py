"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs.")

    # Three distinct user preference profiles
    profiles = [
        (
            "High-Energy Pop",
            {
                "favorite_genre": "pop",
                "favorite_mood": "happy",
                "target_energy": 0.90,
                "likes_acoustic": False,
                "target_tempo": 128,
            },
        ),
        (
            "Chill Lofi",
            {
                "favorite_genre": "lofi",
                "favorite_mood": "chill",
                "target_energy": 0.35,
                "likes_acoustic": True,
                "target_tempo": 75,
            },
        ),
        (
            "Deep Intense Rock",
            {
                "favorite_genre": "rock",
                "favorite_mood": "intense",
                "target_energy": 0.92,
                "likes_acoustic": False,
                "target_tempo": 150,
            },
        ),
        (
            "Lofi Rager",
            {
    "favorite_genre": "lofi",
    "favorite_mood": "intense",   # lofi tracks are all chill/focused
    "target_energy": 0.90,
    "likes_acoustic": False,
    "target_tempo": 140,
}
        ),
        (
            # This profile demonstrates the binary genre limitation.
            # The mood, energy, tempo, and acousticness all fit blues songs
            # closely — but because the genre is set to "jazz", every blues
            # song in the catalog scores 0.0 on genre and gets pushed down,
            # even though jazz and blues share deep musical roots.
            "Jazz Purist (Blues-Compatible Taste)",
            {
                "favorite_genre": "jazz",
                "favorite_mood": "moody",
                "target_energy": 0.50,
                "likes_acoustic": True,
                "target_tempo": 75,
            },
        ),
        (
            # This profile demonstrates the same binary genre limitation for
            # rap vs hip-hop. The mood, energy, tempo, and acousticness all
            # fit rap songs closely — but because the genre is set to
            # "hip-hop", every rap song scores 0.0 on genre and gets buried,
            # even though rap is effectively a subgenre of hip-hop.
            "Hip-Hop Head (Rap-Compatible Taste)",
            {
                "favorite_genre": "hip-hop",
                "favorite_mood": "intense",
                "target_energy": 0.90,
                "likes_acoustic": False,
                "target_tempo": 145,
            },
        ),
    ]

    for profile_name, user_prefs in profiles:
        print(f"\n{'='*40}")
        print(f"Profile: {profile_name}")
        print(f"{'='*40}")

        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("\nTop recommendations:\n")
        for rec in recommendations:
            # You decide the structure of each returned item.
            # A common pattern is: (song, score, explanation)
            song, score, explanation = rec
            print(f"{song['title']} - Score: {score:.2f}")
            print(f"Because: {explanation}")
            print()


if __name__ == "__main__":
    main()
