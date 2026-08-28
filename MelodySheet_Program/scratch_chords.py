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
        for meas in part.findall("measure"):
            m_idx_str = meas.get("number")
            if not m_idx_str or not m_idx_str.isdigit():
                continue
            m_idx = int(m_idx_str)
            if m_idx <= 10:
                chords = []
                for h in meas.findall("harmony"):
                    root_step = h.findtext("root/root-step") or ""
                    kind = h.findtext("kind") or ""
                    chords.append(f"{root_step}{kind}")
                print(f"M{m_idx}: {', '.join(chords)}")

except Exception as e:
    print(e)
