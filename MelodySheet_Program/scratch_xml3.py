import xml.etree.ElementTree as ET
import os

musicxml_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input03\Saturday Motion.musicxml"
try:
    tree = ET.parse(musicxml_path)
    root = tree.getroot()
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
            
    notes = []
    for part in root.findall(".//part"):
        for meas in part.findall("measure"):
            m_idx_str = meas.get("number")
            if not m_idx_str or not m_idx_str.isdigit():
                continue
            m_idx = int(m_idx_str) - 1
            if m_idx < 5:
                for el in meas:
                    if el.tag == "note":
                        is_rest = el.find("rest") is not None
                        if not is_rest:
                            step = el.findtext("pitch/step")
                            octave = el.findtext("pitch/octave")
                            notes.append(f"M{m_idx+1}: {step}{octave} (Staff {el.findtext('staff')})")

    print(f"Notes in M1-M5: {len(notes)}")
    for n in notes:
        print(n)
except Exception as e:
    print(e)
