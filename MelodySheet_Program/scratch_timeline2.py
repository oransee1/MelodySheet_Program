import sys
sys.path.append(r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program")
from engine.score_timeline import build_timeline_from_midi

midi_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input03\Saturday Motion.mid"
timeline = build_timeline_from_midi(midi_path)
for i in range(10):
    m = timeline.measures[i]
    print(f"M{i+1}: start={m.start_sec}, dur={m.duration_sec}")
