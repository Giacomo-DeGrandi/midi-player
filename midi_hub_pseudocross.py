import mido
import time
import os
import threading

def adjust_velocity(msg, factor):
    if msg.type == 'note_on' and msg.velocity > 0:
        return msg.copy(velocity=int(msg.velocity * factor))
    return msg

def play_midi_file(midi_file_path, outport, stop_event, bpm, fade_in_ticks=480, fade_out_ticks=480):
    midi_file = mido.MidiFile(midi_file_path)
    tempo = int(60_000_000 / bpm)  # Convert BPM to microseconds per beat
    total_ticks = sum(msg.time for track in midi_file.tracks for msg in track)
    current_tick = 0

    for track in midi_file.tracks:
        for msg in track:
            if stop_event.is_set():
                break
            if not msg.is_meta:
                seconds_per_tick = tempo / (midi_file.ticks_per_beat * 1000000.0)
                time.sleep(msg.time * seconds_per_tick)
                current_tick += msg.time

                # Adjust velocities for fade-in and fade-out
                if current_tick < fade_in_ticks:
                    factor = current_tick / fade_in_ticks
                elif total_ticks - current_tick < fade_out_ticks:
                    factor = (total_ticks - current_tick) / fade_out_ticks
                else:
                    factor = 1.0

                adjusted_msg = adjust_velocity(msg, factor)
                outport.send(adjusted_msg)
            elif msg.type == 'set_tempo':
                pass


def start_next_pattern(next_midi_file_path, outport, stop_event, bpm):
    global current_thread
    crossfade_delay = 2.0  # Delay before starting the next pattern (in seconds)
    time.sleep(crossfade_delay)
    current_thread = threading.Thread(target=play_midi_file, args=(next_midi_file_path, outport, stop_event, bpm))
    current_thread.start()

def listen_midi_input(inport, outport, stop_event, bpm):
    global current_thread, midi_files
    for msg in inport:
        if msg.type == 'control_change':
            if msg.control == 10:
                file_index = msg.value % len(midi_files)
                next_midi_file_path = os.path.join('loops', midi_files[file_index])
                if current_thread and current_thread.is_alive():
                    start_next_pattern(next_midi_file_path, outport, stop_event, bpm)
                else:
                    current_thread = threading.Thread(target=play_midi_file, args=(next_midi_file_path, outport, stop_event, bpm))
                    current_thread.start()
            elif msg.control == 11:
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
current_thread = None
bpm = 120

# Start the playback and MIDI input listening threads
threading.Thread(target=listen_midi_input, args=(inport, outport, stop_event, bpm), daemon=True).start()

# Main loop for user input (for quitting the script)
while True:
    if input("Enter 'q' to quit: ").lower() == 'q':
        stop_event.set()
        if current_thread and current_thread.is_alive():
            current_thread.join()
        break
