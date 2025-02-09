import json
import subprocess
import sqlite3
import argparse
from typing import Any, Generator, Iterable
import pandas as pd
from pandas import DataFrame, Series
from pathlib import Path
from tqdm import tqdm

from ._utils import (
    DBT_PATH,
    MMD_AUDIO_TEXT_MATCHES_PATH, 
    MMD_MIDI_DIR_PATH, PROCS, 
    SQLITE_SAVE_PATH, 
    TRACKS_FEATURES_PATH,
    save_progress
)
from .models import SpotifyTrack, MIDI

def insert_spotify_track(db: sqlite3.Connection, track: SpotifyTrack):
    """Insert a Spotify Track into the db"""

    insert_many(
        db=db,
        table_name="spotify_tracks",
        cols=[
            "spotify_id", 
            "title", 
            "album_id", 
            "artist_ids", 
            "year_first_released", 
            "duration_ms", 
            "popularity",
            "has_features",
            ],
        vals=[
            (
                track.id,
                track.title,
                track.album.album_id,
                ",".join([artist.artist_id for artist in track.artists]),
                track.year_first_released,
                track.duration_ms,
                track.popularity,
                track.has_features,
            )
        ]
    )

    if track.has_features:
        insert_many(
            db,
            table_name="audio_features",
            cols=[
                "spotify_id",
                "danceability",
                "acousticness",
                "energy",
                "valence",
                "speechiness",
                "instrumentalness",
            ],
            vals=[
                (
                    track.features.id,
                    track.features.danceability,
                    track.features.acousticness,
                    track.features.energy,
                    track.features.valence,
                    track.features.speechiness,
                    track.features.instrumentalness,
                )
            ]
        )

    insert_many(
        db=db,
        table_name="midi_spotify_map",
        cols=["md5", "spotify_id", "score"],
        vals=[(link.md5, link.sid, link.score) for link in track.links]
    )

    insert_many(
        db=db,
        table_name="artists",
        cols=["artist_id", "title"],
        vals=[(artist.artist_id, artist.title) for artist in track.artists],
        integrity_handler="ignore" # since we only care about new artists
    )

    insert_many(
        db=db,
        table_name="albums",
        cols=["album_id", "title"],
        vals=[(track.album.album_id, track.album.title)], # only one album per track
        integrity_handler="ignore"
    )

    insert_many(
        db=db,
        table_name="spotify_album_map",
        cols=["spotify_id", "album_id"],
        vals=[(track.id, track.album.album_id)],
    )

    insert_many(
        db=db,
        table_name="spotify_artist_map",
        cols=["spotify_id", "artist_id"],
        vals=[(track.id, artist.artist_id) for artist in track.artists]
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

    insert_many(
        db=db,
        table_name="midi_spotify_map",
        cols=["md5", "spotify_id", "score"],
        vals=[(link.md5, link.spotify_id, link.score) for link in file.links]
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

def is_one_in_table(db: sqlite3.Connection, table: str, id: str) -> bool:
    """Checks whether an sid/md5 is already in db. table must be either spotify_tracks or midi_files."""
    assert table in ("spotify_tracks", "midi_files")
    key = "spotify_id" if table == "spotify_tracks" else "md5"
    cursor = db.cursor()
    cursor.execute(
        "select exists("
            f"select 1 from {table} where {key} = ?"
        ")",
        (id,)
    )
    return cursor.fetchone()[0] == 1

def are_many_in_table(db: sqlite3.Connection, ids: list[str]) -> bool:
    """ Checks whether the batch of ID's are in the spotify_tracks table.
        This can only be used for spotify_tracks as MIDI files aren't done
        in batches."""
    ids_parameterized = ",".join(["?" for _ in ids])
    cursor = db.cursor()
    cursor.execute(f"""
        select count(distinct spotify_id) 
        from spotify_tracks 
        where spotify_id in ({ids_parameterized})
    """, ids)
    return cursor.fetchone()[0] == len(ids)
    # ids_parameterized = ",".join(["?" for id in ids])
    # cursor = db.cursor()
    # cursor.execute(
    #     "select exists("
    #         f"select spotify_id from spotify_tracks where spotify_id in ({ids_parameterized})"
    #     ")",
    #     (ids,),
    # )
    # return len(cursor.fetchall()) == len(ids)

def chunker(seq: Iterable, size: int) -> Generator:
    """Thx stackoverfow"""
    return (seq[pos : pos + size] for pos in range(0, len(seq), size))

def dbt(*args):
    """Wrapper function for executing dbt command line arguments"""
    return subprocess.call(
        ["dbt", *args, f"--project-dir={DBT_PATH}", f"--profiles-dir={DBT_PATH}"]
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
        help="The path to the TSV file containing matches between MIDI files and Spotify tracks.",
        default=MMD_AUDIO_TEXT_MATCHES_PATH
    )

    parser.add_argument(
        "--features",
        type=Path,
        help="The path to the CSV file containing audio features from the deprecated Spotify API",
        default=TRACKS_FEATURES_PATH
    )

    parser.add_argument(
        "--midis",
        type=Path,
        help="The path to the directory containing the MIDI files.",
        default=MMD_MIDI_DIR_PATH
    )

    parser.add_argument(
        "--out",
        type=Path,
        help="The path to save the SQLite database to.",
        default=SQLITE_SAVE_PATH
    )

    parser.add_argument(
        "--append",
        action="store_true",
        help="Option to append the existing database with new tracks only."
    )

    parser.add_argument(
        "--single",
        type=Path,
        help="Run only a single MIDI file. Useful for debugging/testing."
    )

    parser.add_argument(
        "--procs",
        type=int,
        help="The number of processes to use for multiprocessing",
        default=PROCS
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    # first, dbt clean and dbt run
    # then, read the matches.tsv file into a df
    # then, get a list of unique md5s in the df
    args = parse_args()

    if args.append:
        assert args.out.exists()

    if not args.no_dbt and not args.append:
        dbt("clean")
        dbt("run")

    assert args.matches.exists(), "Must provide a valid path to the matches file."
    assert args.features.exists(), "Must provide a valid path to the audio features file."
    assert args.midis.exists(), "Must provide a valid path to the MIDI file directory."

    db = sqlite3.connect(args.out, timeout=10000)
    matches = pd.read_csv(args.matches, sep="\t")
    audio_features = pd.read_csv(args.features)

    unique_sids = Series(matches["sid"].unique())
    if args.append:
        with open("./logs/failed_track_ids.json", 'r') as file:
            last_ids = json.load(file)
            unique_sids = unique_sids.iloc[unique_sids[unique_sids == last_ids[0]].index[0]:unique_sids.size]
    sid_chunks = list(chunker(unique_sids, min(50, len(unique_sids))))
    midis = []
    for sid_chunk in tqdm(sid_chunks, total=len(sid_chunks)):
        try:
            spotify_tracks = SpotifyTrack.from_ids(list(sid_chunk), matches, audio_features)
            for track in spotify_tracks:
                insert_spotify_track(db=db, track=track)
        except KeyboardInterrupt:
            save_progress(list(sid_chunk))
            print("KeyboardInterrupt interrupted spotify track insertion process. Saving ids to logs/failed_track_ids.json...")
            raise
    
    unique_md5s = matches["md5"].unique()

    for md5 in tqdm(unique_md5s):
        path = args.midis.joinpath(Path(md5[0] + "/" + md5[1] + "/" + md5[2] + "/" + md5 + ".mid"))
        midi = MIDI.from_path(path)
        insert_midi_file(db, midi)

    db.commit()
    db.close()

    if not args.no_dbt:
        dbt("test")
    
    print("All good!")

    


