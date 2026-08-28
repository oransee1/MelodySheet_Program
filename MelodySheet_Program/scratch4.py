import pretty_midi
import sys

midi_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input03\Saturday Motion.mid"

pm = pretty_midi.PrettyMIDI(midi_path)
t = 17.5
print(f"Notes active at t={t}:")
for i, inst in enumerate(pm.instruments):
    for n in inst.notes:
        if n.start <= t <= n.end:
            print(f"  Track {i}: pitch={n.pitch}, start={n.start:.2f}, end={n.end:.2f}")
