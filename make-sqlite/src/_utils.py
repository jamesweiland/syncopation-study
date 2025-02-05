from pathlib import Path

DBT_PATH: Path = Path("dbt").absolute()
MMD_AUDIO_TEXT_MATCHES_PATH: Path = Path("dbt/data/MMD_audio_text_matches.tsv").absolute()
MMD_MIDI_DIR_PATH: Path = Path("dbt/data/MMD_MIDI/").absolute()
SQLITE_SAVE_PATH: Path = Path("dbt/data.sqlite3").absolute()
TRACKS_FEATURES_PATH: Path = Path("dbt/data/tracks_features.csv")
PROCS: int = 8