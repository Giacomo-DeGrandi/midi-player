import mido


# Replace 'your_midi_file.mid' with the path to a MIDI file
# ex "C:\Users\gia\Desktop\ROOT REPO\Python 3\sek01\sek01\groove-v1.0.0-midionly\groove\drummer1\eval_session\1_funk-groove1_138_beat_4-4.mid"
path = input('Path to your MIDI file.mid:')
midi_file = mido.MidiFile(path)

for msg in midi_file.tracks:
    for meta in msg:
        if meta.is_meta: 
            print(meta)


