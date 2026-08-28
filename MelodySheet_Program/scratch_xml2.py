import xml.etree.ElementTree as ET
import os

musicxml_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input03\Saturday Motion.musicxml"
try:
    tree = ET.parse(musicxml_path)
    root = tree.getroot()
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
            
    for part in root.findall(".//part"):
        divs = 1
        beats = 4
        beat_type = 4
        for meas in part.findall("measure"):
            m_idx_str = meas.get("number")
            if not m_idx_str or not m_idx_str.isdigit():
                continue
            m_idx = int(m_idx_str) - 1
            if m_idx != 5: # Measure 6
                for attrs in meas.findall(".//attributes"):
                    d = attrs.findtext("divisions")
                    if d and d.isdigit(): divs = int(d)
                    b = attrs.findtext("time/beats")
                    if b and b.isdigit(): beats = int(b)
                    bt = attrs.findtext("time/beat-type")
                    if bt and bt.isdigit(): beat_type = int(bt)
                continue
                
            for attrs in meas.findall(".//attributes"):
                d = attrs.findtext("divisions")
                if d and d.isdigit(): divs = int(d)
                b = attrs.findtext("time/beats")
                if b and b.isdigit(): beats = int(b)
                bt = attrs.findtext("time/beat-type")
                if bt and bt.isdigit(): beat_type = int(bt)
                
            total_divs = beats * divs * (4 / beat_type)
            if total_divs <= 0: total_divs = divs * 4
            
            cur_div = 0
            for el in meas:
                if el.tag == "forward":
                    d = el.findtext("duration")
                    if d and d.isdigit(): cur_div += int(d)
                elif el.tag == "backup":
                    d = el.findtext("duration")
                    if d and d.isdigit(): cur_div -= int(d)
                    cur_div = max(0, cur_div)
                elif el.tag == "note":
                    is_chord = el.find("chord") is not None
                    is_rest = el.find("rest") is not None
                    is_grace = el.find("grace") is not None
                    
                    dur_text = el.findtext("duration")
                    duration_divs = int(dur_text) if (dur_text and dur_text.isdigit()) else 0
                    
                    if is_chord:
                        start_div = max(0, cur_div - duration_divs)
                    else:
                        start_div = cur_div
                        
                    if not is_rest and not is_grace:
                        step = el.findtext("pitch/step")
                        octave = el.findtext("pitch/octave")
                        print(f"Measure 6 Note: {step}{octave}, start_div={start_div}/{total_divs}, dur={duration_divs}, staff={el.findtext('staff')}")
                            
                    if not is_chord and not is_grace:
                        cur_div += duration_divs
                        
except Exception as e:
    print(e)
