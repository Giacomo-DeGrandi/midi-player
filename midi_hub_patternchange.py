import mido
import time
import os
import threading

def play_midi_file(outport, stop_event, bpm, bars_per_pattern, queued_midi_file_path):
    global midi_file_path
    while not stop_event.is_set():
        midi_file = mido.MidiFile(midi_file_path)
        ticks_per_beat = midi_file.ticks_per_beat
        ticks_per_bar = ticks_per_beat * 4  # Assuming 4/4 time signature
        total_ticks_for_pattern = ticks_per_bar * bars_per_pattern
        elapsed_ticks = 0

        for track in midi_file.tracks:
            for msg in track:
                if stop_event.is_set():
                    break
                if not msg.is_meta:
                    elapsed_ticks += msg.time
                    if elapsed_ticks >= total_ticks_for_pattern:
                        elapsed_ticks = 0
                        if queued_midi_file_path[0]:
                            midi_file_path = queued_midi_file_path[0]
                            midi_file = mido.MidiFile(midi_file_path)
                            queued_midi_file_path[0] = None
                            continue  # Start playing the new MIDI file immediately

                    seconds_per_tick = (60_000_000 / bpm) / ticks_per_beat
                    time.sleep(msg.time * seconds_per_tick)
                    outport.send(msg)
                elif msg.type == 'set_tempo':
                    pass

def listen_midi_input(inport, queued_midi_file_path):
    global bpm
    for msg in inport:
        if msg.type == 'control_change':
            if msg.control == 10:  # Control Change for pattern selection
                file_index = msg.value % len(midi_files)
                queued_midi_file_path[0] = os.path.join('loops', midi_files[file_index])
            elif msg.control == 11:  # Control Change for BPM
                bpm = max(20, min(msg.value, 250))
# Setup MIDI input and output
inport_name = 'LoopBe Internal MIDI 0'
outport_name = 'LoopBe Internal MIDI 1'

try:
    inport = mido.open_input(inport_name)
except IOError:
    print(f"Error: Could not open MIDI input port '{inport_name}'.")
    exit(1)

try:
    outport = mido.open_output(outport_name)
except IOError:
    print(f"Error: Could not open MIDI output port '{outport_name}'.")
    exit(1)

# List MIDI files in directory
midi_files = [f for f in os.listdir('loops') if f.endswith('.mid')]

# Global variables
stop_event = threading.Event()
midi_file_path = os.path.join('loops', midi_files[0])  # Default to the first file
queued_midi_file_path = [None]  # List used to allow modification by reference
# Start the playback and MIDI input listening threads
bpm = 120  # Default BPM
bars_per_pattern = 0.125  # Number of bars per pattern (can be fractional)


# Start the playback and MIDI input listening threads
playback_thread = threading.Thread(target=play_midi_file, args=(outport, stop_event, bpm, bars_per_pattern, queued_midi_file_path))
playback_thread.start()
threading.Thread(target=listen_midi_input, args=(inport, queued_midi_file_path), daemon=True).start()

# Main loop for user input (for quitting the script)
while True:
    if input("Enter 'q' to quit: ").lower() == 'q':
        stop_event.set()
        playback_thread.join()
        break
