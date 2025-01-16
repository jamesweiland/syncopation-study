from typing import NamedTuple

""" In MMD_audio_text_matches.tsv and MMD_audio_matches.tsv, 
    MD5 hashes are linked to spotify ids, with a score
    indicating the confidence of the link. scored_ids
    represents the spotify id-score tuple. """
type scored_ids = tuple[str, float]

class MIDI(NamedTuple):
    md5: str
    path_to_midi: str
    spotify_ids: list[scored_ids] # note that one md5 can be linked to multiple spotify tracks
    WNBD_score: float