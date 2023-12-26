import mido

print("Ports de sortie MIDI disponibles:", mido.get_output_names())
print("Ports d'entrée MIDI disponibles:", mido.get_input_names())