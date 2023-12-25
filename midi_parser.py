import mido
import time

# Load the MIDI file
path = input('path_to_your_midi_file.mid')
midi_file = mido.MidiFile(path)

# Default tempo: 120 BPM (500,000 microseconds per beat)
tempo = 500000

# First, scan the file for the initial tempo
for track in midi_file.tracks:
    for msg in track:
        if msg.type == 'set_tempo':
            tempo = msg.tempo
            break
    if tempo != 500000:
        # Stop scanning if a tempo event has been found
        break

# Calculate seconds per tick based on initial tempo
ticks_per_beat = midi_file.ticks_per_beat
seconds_per_tick = tempo / (ticks_per_beat * 1000000.0)

# Open virtual MIDI output port
outport = mido.open_output('LoopBe Internal MIDI 1')

# Now start the playback
for track in midi_file.tracks:
    for msg in track:
        if not msg.is_meta:
            # Sleep for the message time converted to seconds
            time.sleep(msg.time * seconds_per_tick)
            outport.send(msg)
        elif msg.type == 'set_tempo':
            # Update the current tempo
            tempo = msg.tempo
            seconds_per_tick = tempo / (ticks_per_beat * 1000000.0)
