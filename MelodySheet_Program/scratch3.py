import pretty_midi
import sys

midi_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input03\Saturday Motion.mid"

pm = pretty_midi.PrettyMIDI(midi_path)
print("Track 1 first 10 notes:")
for n in pm.instruments[1].notes[:10]:
    print(f"  pitch={n.pitch}, start={n.start:.2f}")
