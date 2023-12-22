import mido
import time


# Open virtual MIDI ports
outport = mido.open_output("LoopBe Internal MIDI 1")
inport = mido.open_input("LoopBe Internal MIDI 0")

# Send a MIDI message to Pure Data
outport.send(mido.Message('note_on', note=60))
time.sleep(1)
outport.send(mido.Message('note_off', note=60))

# Receive a MIDI message from Pure Data
for msg in inport.iter_pending():
    print(msg)
