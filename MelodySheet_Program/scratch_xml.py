import xml.etree.ElementTree as ET
import os

musicxml_path = r"C:\Users\DiCiA\PycharmProjects\음원+악보병합 프로젝트\MelodySheet_Program\MelodySheet_Program\InputData\2026-08-16\Input03\Saturday Motion.musicxml"
try:
    tree = ET.parse(musicxml_path)
    root = tree.getroot()
    for elem in root.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
            
    xml_notes = []
    for part in root.findall(".//part"):
        for meas in part.findall("measure"):
            m_idx_str = meas.get("number")
            if m_idx_str == "1":
                for el in meas:
                    if el.tag == "note":
                        step = el.findtext("pitch/step")
                        octave = el.findtext("pitch/octave")
                        print(f"Measure 1 Note: {step}{octave}, rest={el.find('rest') is not None}, chord={el.find('chord') is not None}, staff={el.findtext('staff')}")
except Exception as e:
    print(e)
