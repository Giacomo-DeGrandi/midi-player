import mido
import time
import os

def play_midi_file(path, outport):
    midi_file = mido.MidiFile(path)

    # Find initial tempo
    tempo = 500000  # default 120 BPM
    for track in midi_file.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                tempo = msg.tempo
                break
        if tempo != 500000:
            break

    # Calculate seconds per tick
    ticks_per_beat = midi_file.ticks_per_beat
    seconds_per_tick = tempo / (ticks_per_beat * 1000000.0)

    # Play the MIDI file
    for track in midi_file.tracks:
        for msg in track:
            if not msg.is_meta:
                time.sleep(msg.time * seconds_per_tick)
                outport.send(msg)
            elif msg.type == 'set_tempo':
                tempo = msg.tempo
                seconds_per_tick = tempo / (ticks_per_beat * 1000000.0)

# List MIDI files in directory
midi_files = [f for f in os.listdir('loops') if f.endswith('.mid')]
for idx, file in enumerate(midi_files):
    print(f"{idx}: {file}")

# Simulated knob input
file_index = int(input("Enter the number to select MIDI file: "))
midi_file_path = os.path.join('loops', midi_files[file_index])

# Setup MIDI output
outport = mido.open_output('LoopBe Internal MIDI 1')

# Play the selected MIDI file
play_midi_file(midi_file_path, outport)
