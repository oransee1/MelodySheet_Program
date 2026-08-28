import pretty_midi
import sys

midi_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input01\Saturday Motion.mid"

try:
    pm = pretty_midi.PrettyMIDI(midi_path)
    for i, inst in enumerate(pm.instruments):
        print(f"Track {i}: {inst.name}, Program: {inst.program}, Notes: {len(inst.notes)}")
        notes_in_range = [n for n in inst.notes if 3.0 <= n.start <= 6.0]
        for n in notes_in_range:
            print(f"  Note pitch={n.pitch}, start={n.start:.2f}, end={n.end:.2f}")
except Exception as e:
    print(f"Error: {e}")
