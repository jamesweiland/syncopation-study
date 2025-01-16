from miditoolkit import Note, MidiFile, TimeSignature

def unique(time_sigs: list[TimeSignature]) -> list[TimeSignature]:
    unique_time_sigs = []
    for time_sig in time_sigs:
        if time_sig not in unique_time_sigs:
            unique_time_sigs.append(time_sig)
    return unique_time_sigs

def find_strong_beats(midi: MidiFile) -> list[int]:
    """ Returns a list of the tick position of every
        strong beat in a MidiFile. A strong beat is
        simply defined as a pulse. For example, a
        song in 4/4 time has strong beats every
        quarter note. """
    result = []
    # in mido/miditoolkit, ticks per beat is the name for "ticks per quarter note" or PPQ. Disambiguating this here.
    ppq = midi.ticks_per_beat
    time_sigs = unique(midi.time_signature_changes) # a midi file can have more than one time signature
    current_time = time_sigs[0].time
    for i in range(0, len(time_sigs)):
        pulse_length = 4 / time_sigs[i].denominator * ppq # number of ticks between every strong beat
        if i == (len(time_sigs) - 1):
            while current_time < midi.max_tick:
                result.append(current_time)
                current_time += pulse_length
        else:
            while current_time < time_sigs[i + 1].time:
                result.append(current_time)
                current_time += pulse_length
    return result

def T(x: Note, E: list[int]) -> tuple[float, int]:
    """ The distance T(x) is defined in https://archive.bridgesmathart.org/2005/bridges2005-73.pdf 
        Returns the distance T(x), and the index of the strong beat i """
    i = 0
    while x.start < E[i] or x.start >= E[i + 1]:
        i += 1
    t = min(abs(x.start - E[i]), abs(x.start - E[i + 1])) if (i < len(E) - 1) else abs(x.start - E[i])
    return (t, i)

def calculate_WNBD(midi_path: str) -> float:
    """ WNBD score is defined in https://archive.bridgesmathart.org/2005/bridges2005-73.pdf. 
        Calculating WNBD is done on a per-rhythm basis in the original paper,
        and finding WNBD of an entire song (or MIDI file) is left undefined.
        This function just takes the unweighted average of all tracks in the MIDI. """
    midi = MidiFile(midi_path)
    # in mido/miditoolkit, ticks per beat is the name for "ticks per quarter note" or PPQ. Disambiguating this here.
    ppq = midi.ticks_per_beat
    E = find_strong_beats(midi)
    total_WNBD = 0.0
    for time_sig in unique(midi.time_signature_changes):
        print(time_sig)
        for instrument in midi.instruments:
            for x in instrument.notes:
                t, i = T(x, E)
                t_frac = (t * time_sig.denominator) / (ppq * 4) # ticks as a fraction of the strong beat = ticks / (ppq * (4/strong beat))
                print(f'{x} has {t_frac}')
                if x.start == E[i]:
                    continue
                elif E[i + 1] < x.end <= E[i + 2]:
                    total_WNBD += 2/t_frac
                else:
                    total_WNBD += 1/t_frac
    total_notes = sum([instrument.num_notes for instrument in midi.instruments])
    return total_WNBD / total_notes

if __name__ == "__main__":
    wnbd = calculate_WNBD("C:/Users/james/Jupyter/syncopation-study/make-sqlite/dbt/tests/test_midis/bembe_rhythm.mid")
    print(f'wnbd: {wnbd}')