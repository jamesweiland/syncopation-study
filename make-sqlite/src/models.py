from pydantic import BaseModel
from dataclasses import dataclass
from pandas import DataFrame
from synpy3 import WNBD
from synpy3.syncopation import calculate_syncopation





class Link:
    sid: str
    score: float # represents confidence of the link
    md5: str

    def from_df(df: DataFrame) -> list["Link"]:
        """Create a list of Links from a dataframe"""
        return [Link(sid=df[idx]["sid"], score = df[idx]["score"], md5=df[idx]["md5"]) for idx,row in df.iterrows()]

class MIDI:
    md5: str
    path_to_midi: str
    matches: list[Link] # note that one md5 can be linked to multiple spotify tracks
    WNBD_score: dict

    def from_path(path: str, df: DataFrame) -> "MIDI":
        """Create a MIDI object from a path to a .mid file."""
        assert path[-4] == ".mid"
        md5 = path[:-4]
        matches = df[df["md5"] == md5]
        WNBD_score = calculate_syncopation(
            model=WNBD,
            source=path
        )
        return MIDI(
            md5=md5,
            path_to_midi=path,
            matches=matches,
            WNBD_score=WNBD_score
        )



class Artist(BaseModel):
    name: str

class SpotifyTrack(BaseModel):
    id: str
    title: str
    artists: list[Artist]
    danceability: float
    grooviness: float
    # i forget the other attributes spotify has but put them here
    WNBD_score: float
    year_first_released: int

