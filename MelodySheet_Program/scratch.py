import pretty_midi
import sys
import glob
import os

files = glob.glob(r"InputData\*\*\Saturday Motion.mid")
if not files:
    print("File not found")
    sys.exit(1)

midi_path = files[-1]
print(f"Reading {midi_path}")

try:
    pm = pretty_midi.PrettyMIDI(midi_path)
    for i, inst in enumerate(pm.instruments):
        print(f"Track {i}: {inst.name}, Program: {inst.program}, Notes: {len(inst.notes)}")
        if inst.notes:
            min_pitch = min(n.pitch for n in inst.notes)
            max_pitch = max(n.pitch for n in inst.notes)
            print(f"  Pitch range: {min_pitch} to {max_pitch}")
except Exception as e:
    print(f"Error: {e}")
