from pathlib import Path
import json

DBT_PATH: Path = Path("dbt").absolute()
MMD_AUDIO_TEXT_MATCHES_PATH: Path = Path("dbt/data/MMD_audio_text_matches.tsv").absolute()
MMD_MIDI_DIR_PATH: Path = Path("dbt/data/MMD_MIDI/").absolute()
SQLITE_SAVE_PATH: Path = Path("dbt/data.sqlite3").absolute()
TRACKS_FEATURES_PATH: Path = Path("dbt/data/tracks_features.csv")
PROCS: int = 8

def save_progress(ids: list[str]):
    """Save the list of Spotify ids to logs/failed_track_ids.json for a failed attempt."""
    with open("./logs/failed_track_ids.json", "w") as file:
        json.dump(ids, file)