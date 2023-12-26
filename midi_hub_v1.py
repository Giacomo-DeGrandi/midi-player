import mido
import time
import os
import threading

def play_midi_file(outport, stop_event, bpm):
    global midi_file_path
    while not stop_event.is_set():
        midi_file = mido.MidiFile(midi_file_path)
        tempo = int(60_000_000 / bpm)  # Convert BPM to microseconds per beat

        for track in midi_file.tracks:
            for msg in track:
                if stop_event.is_set():
                    break
                if not msg.is_meta:
                    # Adjust message timing based on tempo
                    seconds_per_tick = tempo / (midi_file.ticks_per_beat * 1000000.0)
                    time.sleep(msg.time * seconds_per_tick)
                    outport.send(msg)
                elif msg.type == 'set_tempo':
                    # Ignore tempo changes in the MIDI file
                    pass

def listen_midi_input(inport):
    global midi_file_path, bpm
    for msg in inport:
        if msg.type == 'control_change':
            if msg.control == 10:  # Control Change for pattern selection
                file_index = msg.value % len(midi_files)
                midi_file_path = os.path.join('loops', midi_files[file_index])
                restart_playback()
            elif msg.control == 11:  # Control Change for BPM
                bpm = max(20, min(msg.value, 250))  # Set a reasonable BPM range

def restart_playback():
    global playback_thread
    stop_event.set()
    if playback_thread.is_alive():
        playback_thread.join()
    stop_event.clear()
    start_playback_thread()

def start_playback_thread():
    global playback_thread
    playback_thread = threading.Thread(target=play_midi_file, args=(outport, stop_event, bpm))
    playback_thread.start()

# Setup MIDI input and output
inport = mido.open_input('LoopBe Internal MIDI 0')  # Change this to your MIDI input port
outport = mido.open_output('LoopBe Internal MIDI 1')

# List MIDI files in directory
midi_files = [f for f in os.listdir('loops') if f.endswith('.mid')]

# Global variables
stop_event = threading.Event()
midi_file_path = os.path.join('loops', midi_files[0])  # Default to the first file
bpm = 120  # Default BPM

# Start the playback and MIDI input listening threads
start_playback_thread()
threading.Thread(target=listen_midi_input, args=(inport,), daemon=True).start()

# Main loop for user input (for quitting the script)
while True:
    if input("Enter 'q' to quit: ").lower() == 'q':
        stop_event.set()
        break
