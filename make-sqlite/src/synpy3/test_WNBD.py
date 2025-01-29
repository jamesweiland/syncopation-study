import os

import WNBD
from syncopation import calculate_syncopation
from miditoolkit import MidiFile

""" These midi files represent the scores used as examples in the original paper.
    After trying to calculate them by hand myself, I honestly think there are some
    errors in the example in the original paper -- for example, I'm not quite sure
    how they got 0.5 for the anticipation rhythm. I get 1, which is also what the
    implementation gets.
"""
WNBD_answers = {
    "hesitation_rhythm.mid": 0.5,
    "anticipation_rhythm.mid": 1.0,
    "syncopation_rhythm.mid": 1.2,
    "triplet_rhythm.mid": 0.8571428571428571,
    "bembe_rhythm.mid": 2.142857142857143,
    "bossa_nova_rhythm.mid": 2.4
}


def test_WNBD():
    for file in os.listdir("test_midis/wnbd"):
        if file[-3:] == "mid":
            in_path = os.path.join("test_midis/wnbd", file)
            out_path = in_path[:-3] + "xml"
            assert calculate_syncopation(WNBD, source=in_path, outfile=out_path)["summed_syncopation"] == WNBD_answers[file]

if __name__ == "__main__":
    test_WNBD()
