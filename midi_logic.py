import mido
import time
import os
import threading

def play_midi_file(outport, stop_event):
    global midi_file_path
    while not stop_event.is_set():
        midi_file = mido.MidiFile(midi_file_path)
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
                if stop_event.is_set():
                    break
                if not msg.is_meta:
                    time.sleep(msg.time * seconds_per_tick)
                    outport.send(msg)
                elif msg.type == 'set_tempo':
                    tempo = msg.tempo
                    seconds_per_tick = tempo / (ticks_per_beat * 1000000.0)

# Global variable for MIDI file path
midi_file_path = None

# Setup MIDI output
outport = mido.open_output('LoopBe Internal MIDI 1')

# List MIDI files in directory
midi_files = [f for f in os.listdir('loops') if f.endswith('.mid')]
for idx, file in enumerate(midi_files):
    print(f"{idx}: {file}")

# Thread control event
stop_event = threading.Event()

# Start initial playback thread
midi_file_path = os.path.join('loops', midi_files[0])  # Default to first file
playback_thread = threading.Thread(target=play_midi_file, args=(outport, stop_event))
playback_thread.start()

# Main loop for user input
while True:
    file_index = input("Enter the number to select MIDI file (or 'q' to quit): ")
    if file_index.lower() == 'q':
        stop_event.set()
        break
    file_index = int(file_index)
    midi_file_path = os.path.join('loops', midi_files[file_index])
    stop_event.set()  # Signal current thread to stop
    if playback_thread.is_alive():
        playback_thread.join()  # Wait for thread to finish
    stop_event.clear()  # Clear the event for next thread
    playback_thread = threading.Thread(target=play_midi_file, args=(outport, stop_event))
    playback_thread.start()
