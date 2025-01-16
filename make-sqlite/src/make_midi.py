""" Functions to help create a MIDI \"struct\". """
import csv
from collections import defaultdict

from models.midi import MIDI, scored_ids


def get_md5(midi_path: str) -> str:
    """ Get the MD5 checksum from the path to a .mid file.
        In the MMD, the name of the file is the MD5. """
    return midi_path.split("/")[-1].split(".")[0]

def md5_spotify_dict(tsv_path: str) -> dict[str, list[scored_ids]]:
    """ Parses the given .tsv file and creates a
        dictionary mapping MD5s to all matched spotify
        ids with scores. """
    result = defaultdict(list)
    with open(tsv_path, newline='') as tsv:
        reader = csv.reader(tsv, delimiter='\t')
        for row in reader:
            assert len(row) == 3
            md5, sid, score = row
            result[md5].append((sid, score))
    

    