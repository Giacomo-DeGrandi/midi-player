import mido
import time
import os
import threading

def play_midi_file(outport, stop_event, shared_data):
    global midi_file_path
    while not stop_event.is_set():
        midi_file = mido.MidiFile(midi_file_path)
        ticks_per_beat = midi_file.ticks_per_beat

        with shared_data["lock"]:
            bpm = shared_data["bpm"]
            steps_per_bar = shared_data["steps_per_bar"]
            if shared_data["queued_midi_file_path"]:
                midi_file_path = shared_data["queued_midi_file_path"]
                midi_file = mido.MidiFile(midi_file_path)
                shared_data["queued_midi_file_path"] = None

        tempo = int(60_000_000 / bpm)  # Convert BPM to microseconds per beat
        ticks_per_step = ticks_per_beat / 4  # Assuming each step is a sixteenth note
        total_ticks_per_step = ticks_per_step * steps_per_bar
        elapsed_ticks = 0

        for track in midi_file.tracks:
            for msg in track:
                if stop_event.is_set():
                    break
                if not msg.is_meta:
                    elapsed_ticks += msg.time
                    if elapsed_ticks >= total_ticks_per_step:
                        elapsed_ticks -= total_ticks_per_step
                        break  # Restart the pattern from the next step

                    seconds_per_tick = tempo / (ticks_per_beat * 1000000.0)
                    time.sleep(msg.time * seconds_per_tick)
                    outport.send(msg)
                elif msg.type == 'set_tempo':
                    pass

def listen_midi_input(inport, shared_data):
    min_bpm = 40   # Define minimum BPM
    max_bpm = 240  # Define maximum BPM
    min_steps = 1   # Define minimum steps per bar
    max_steps = 64  # Define maximum steps per bar
    for msg in inport:
        if msg.type == 'control_change':
            with shared_data["lock"]:
                if msg.control == 10:  # Control Change for pattern selection
                    file_index = msg.value % len(midi_files)
                    shared_data["queued_midi_file_path"] = os.path.join('loops', midi_files[file_index])
                elif msg.control == 11:  # Control Change for BPM
                    bpm_value = msg.value / 127.0  # Normalize to range 0-1
                    shared_data["bpm"] = int(bpm_value * (max_bpm - min_bpm) + min_bpm)
                elif msg.control == 12:  # Control Change for steps_per_bar
                    steps_per_bar_value = msg.value / 127.0  # Normalize to range 0-1
                    shared_data["steps_per_bar"] = int(steps_per_bar_value * (max_steps - min_steps) + min_steps)

# Setup MIDI input and output
inport = mido.open_input('LoopBe Internal MIDI 0')  # Change this to your MIDI input port
outport = mido.open_output('LoopBe Internal MIDI 1')

# List MIDI files in directory
midi_files = [f for f in os.listdir('loops') if f.endswith('.mid')]

# Shared data and lock
shared_data = {
    "bpm": 120,
    "steps_per_bar": 16,
    "queued_midi_file_path": None,
    "lock": threading.Lock()
}

# Global variables
stop_event = threading.Event()
midi_file_path = os.path.join('loops', midi_files[0])  # Default to the first file

# Start the playback and MIDI input listening threads
playback_thread = threading.Thread(target=play_midi_file, args=(outport, stop_event, shared_data))
playback_thread.start()

midi_input_thread = threading.Thread(target=listen_midi_input, args=(inport, shared_data), daemon=True)
midi_input_thread.start()

# Main loop for user input (for quitting the script)
while True:
    if input("Enter 'q' to quit: ").lower() == 'q':
        stop_event.set()
        playback_thread.join()
        break
