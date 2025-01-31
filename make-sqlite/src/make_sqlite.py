import os
import subprocess
import sqlite3
import argparse
from typing import Any, Generator, Iterable
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from _utils import DBT_PATH, MMD_AUDIO_TEXT_MATCHES_PATH, MMD_MIDI_DIR, SQLITE_SAVE_PATH
from models import SpotifyTrack, MIDI, Link

def insert_spotify_track(db: sqlite3.Connection, track: SpotifyTrack):
    """Insert a Spotify Track into the db"""

    insert_many(
        db=db,
        table_name="spotify_tracks",
        cols=[
            "spotify_id", 
            "name", 
            "album", 
            "artists", 
            "year_first_released", 
            "duration_ms", 
            "popularity", 
            "danceability", 
            "acousticness", 
            "energy",
            "valence"
            ],
        vals=[
            (
                track.id,
                track.title,
                track.album,
                track.artists,
                track.year_first_released,
                track.duration_ms,
                track.popularity,
                track.danceability,
                track.acousticness,
                track.energy,
                track.valence,
            )
        ]
    )

    insert_many(
        db=db,
        table_name="midi_spotify_map",
        cols=["md5", "spotify_id", "score"],
        vals=[(link.md5, link.sid, link.score) for link in track.links]
    )

def insert_midi_file(db: sqlite3.Connection, file: MIDI):
    """Insert a MIDI file into the db"""

    insert_many(
        db=db,
        table_name="midi_files",
        cols=[
            "md5", 
            "instruments", 
            "summed_WNBD", 
            "mean_WNBD_per_bar", 
            "number_of_bars", 
            "number_of_bars_not_measured", 
            "bars_with_valid_output", 
            "bars_without_valid_output"
            ],
        vals=[
            (
                file.md5,
                file.instruments,
                file.summed_WNBD,
                file.mean_WNBD_per_bar,
                file.number_of_bars,
                file.number_of_bars_not_measured,
                file.bars_with_valid_output,
                file.bars_without_valid_output,
            )
        ]
    )

def insert_many(
        db: sqlite3.Connection,
        table_name: str,
        cols: list[str],
        vals: list[tuple[Any]],
        integrity_handler: str = "raise",
):
    """Wrapper around executemany for arbitrary tables."""
    assert integrity_handler in ("ignore", "raise", "warn")
    col_sql = ", ".join(map(lambda x: f'"{x}"', cols))
    qs_sql = ", ".join(["?"] * len(cols))

    assert all(len(i) == len(cols) for i in vals)

    sql = f"""
        insert into "{table_name}" ({col_sql})
        values ({qs_sql})
    """

    if integrity_handler == "ignore":
        sql += "\n on conflict do nothing"

    try:
        db.executemany(sql, vals)
    except sqlite3.IntegrityError:
        if integrity_handler == "warn":
            print(f"Warning: Integrity error ignored on {table_name}.")
        else:
            raise


def chunker(seq: Iterable, size: int) -> Generator:
    """Thx stackoverfow."""
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))

def dbt(*args):
    """Wrapper function for executing dbt command line arguments"""
    return subprocess.call(
        ["dbt", *args, f"--profiles-dir={DBT_PATH}", f"--project-dir={DBT_PATH}"]
    )

def parse_args() -> argparse.Namespace:
    """Parser for command line arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-dbt",
        action="store_true",
        help="Option to skip dbt steps (assuming run separately)"
    )

    parser.add_argument(
        "--matches",
        type=Path,
        help="The path to the TSV file containing matches between MIDI files and Spotify tracks."
        default=MMD_AUDIO_TEXT_MATCHES_PATH
    )

    parser.add_argument(
        "--midis",
        type=Path,
        help="The path to the directory containing the MIDI files.",
        default=MMD_MIDI_DIR
    )

    parser.add_argument(
        "--out",
        type=Path,
        help="The path to save the SQLite database to.",
        default=SQLITE_SAVE_PATH
    )

    parser.add_argument(
        "--single",
        type=Path,
        help="Run only a single MIDI file. Useful for debugging/testing."
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # first, dbt clean and dbt run
    # then, read the matches.tsv file into a df
    # then, get a list of unique md5s in the df
    args = parse_args()
    
    if not args.no_dbt:
        dbt("clean")
        dbt("run")

    assert args.matches.exists(), "Must provide a valid path to the matches file."
    db = sqlite3.connect(args.out, timeout=10000)
    df = pd.read_csv(args.matches, sep="\t")

    unique_sids = df["sid"].unique()
    sid_chunks = list(chunker(unique_sids, min(50, len(unique_sids))))
    midis = []
    for chunk in tqdm(sid_chunks):
        spotify_tracks = SpotifyTrack.from_ids(chunk, df)
        for track in spotify_tracks:
            insert_spotify_track(db=db, spotify_track=track)
    
    unique_md5s = df["md5"].unique()
    for md5 in tqdm(unique_md5s):
        assert args.midis.exists()
        path = args.midis.joinpath(Path(md5[0] + "/" + md5[1] + "/" + md5[2] + "/" + md5 + ".mid"))
        midi = MIDI.from_path(path)

    db.commit()
    db.close()

    if not args.no_dbt:
        dbt("test")
    
    print("All good!")

    


