import mido
import time
import os
import threading
import tkinter as tk
from tkinter import ttk

def play_midi_file(outport, stop_event, tempo_modifier):
    global midi_file_path
    while not stop_event.is_set():
        midi_file = mido.MidiFile(midi_file_path)
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

        while not stop_event.is_set():
            for track in midi_file.tracks:
                for msg in track:
                    if stop_event.is_set():
                        break
                    if not msg.is_meta:
                        # Modify the tempo based on the slider value
                        adjusted_tempo = tempo * tempo_modifier.get()
                        seconds_per_tick = adjusted_tempo / (ticks_per_beat * 1000000.0)
                        time.sleep(msg.time * seconds_per_tick)
                        outport.send(msg)

class MidiSequencerApp:
    def __init__(self, root):
        self.root = root
        root.title("MIDI Sequencer")

        self.midi_file_list = tk.Listbox(root)
        self.midi_file_list.pack()
        for file in midi_files:
            self.midi_file_list.insert(tk.END, file)
        
        self.play_button = tk.Button(root, text="Play", command=self.play_selected_midi)
        self.play_button.pack()

        self.tempo_modifier = tk.DoubleVar(value=1.0)
        self.tempo_slider = ttk.Scale(root, from_=0.5, to=2.0, variable=self.tempo_modifier, orient='horizontal')
        self.tempo_slider.pack()

    def play_selected_midi(self):
        global midi_file_path
        selected_index = self.midi_file_list.curselection()
        midi_file_path = os.path.join('loops', midi_files[selected_index[0]])
        stop_event.set()  # Signal current thread to stop
        if playback_thread.is_alive():
            playback_thread.join()  # Wait for thread to finish
        stop_event.clear()  # Clear the event for next thread
        start_playback_thread()

def start_playback_thread():
    global playback_thread
    playback_thread = threading.Thread(target=play_midi_file, args=(outport, stop_event, app.tempo_modifier))
    playback_thread.start()

# Setup MIDI output and list MIDI files
outport = mido.open_output('LoopBe Internal MIDI 1')
midi_files = [f for f in os.listdir('loops') if f.endswith('.mid')]

# Thread control event and default MIDI file path
stop_event = threading.Event()
midi_file_path = os.path.join('loops', midi_files[0])  # Default to first file

# Start Tkinter GUI
root = tk.Tk()
app = MidiSequencerApp(root)
start_playback_thread()
root.mainloop()
