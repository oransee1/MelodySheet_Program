import os
import sys
from datetime import datetime
from engine.video_renderer import VideoRenderer

def run_test():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, "InputData", "2026-08-14", "Input01")
    
    pdf_path = os.path.join(input_dir, "Sunday Slow Motion.pdf")
    audio_path = os.path.join(input_dir, "Sunday Slow Motion.mp3")
    midi_path = os.path.join(input_dir, "Sunday Slow Motion.mid")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "Output", today_str)
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "Sunday_Slow_Motion_SheetVideo.mp4")

    print(f"PDF Path: {pdf_path} (Exists: {os.path.exists(pdf_path)})")
    print(f"Audio Path: {audio_path} (Exists: {os.path.exists(audio_path)})")
    print(f"MIDI Path: {midi_path} (Exists: {os.path.exists(midi_path)})")

    if not os.path.exists(pdf_path) or not os.path.exists(audio_path):
        print("Required test files missing!")
        return False

    renderer = VideoRenderer(
        pdf_path=pdf_path,
        audio_path=audio_path,
        output_path=output_path,
        title="Sunday Slow Motion",
        artist="Kim Sanghoon",
        sync_mode="klangio",
        midi_path=midi_path if os.path.exists(midi_path) else None,
        progress_callback=lambda p: print(f"Rendering Progress: {p}%")
    )
    
    print("Starting 8-page ensemble render test...")
    renderer.render()
    print(f"Render completed. Output file: {output_path} (Exists: {os.path.exists(output_path)})")
    return os.path.exists(output_path)

if __name__ == "__main__":
    success = run_test()
    if not success:
        sys.exit(1)
