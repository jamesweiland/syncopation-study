from src.WNBD import calculate_WNBD

test_midi_directory = "C:/Users/james/Jupyter/syncopation-study/make-sqlite/dbt/tests/test_midis/"

def test_wnbd():
    assert calculate_WNBD(test_midi_directory + "hesitation_rhythm.mid") == .5
    assert calculate_WNBD(test_midi_directory + "anticipation_rhythm.mid") == 1
    assert calculate_WNBD(test_midi_directory + "syncopation_rhythm.mid") == 1.2
    assert (calculate_WNBD(test_midi_directory + "triplet_rhythm.mid") - .857) <= 0.001
    assert calculate_WNBD(test_midi_directory + "bembe_rhythm.mid") == 3
    assert calculate_WNBD(test_midi_directory + "bossa_nova_rhythm.mid") == 4