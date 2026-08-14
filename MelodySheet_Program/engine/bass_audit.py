"""베이스가 악보 음정·화성대로인지 대조.

시계는 악보 마디 격자. 비교 대상은 MusicXML Double Bass 성부와
MIDI Contrabass 트랙(program 43)뿐이다. 피아노·바이올린·첼로는 넣지 않는다.
이음줄로만 이어지는 음은 새 발음이 아니다.
XML에 transpose가 있으면 실음으로 옮긴다. 이 곡은 transpose가 없고
clef-octave-change=-1만 있으며, MIDI도 기보 높이(D3=50)라 옥타브를 내리지 않는다.
"""
from __future__ import annotations

from typing import List, Optional

from engine.part_audit import (
    BASS,
    PartAuditReport,
    PartEvent,
    PartHit,
    audit_part,
    parse_part_score,
    write_part_report,
)
from engine.score_timeline import ScoreTimeline

BassEvent = PartEvent
BassHit = PartHit
BassAuditReport = PartAuditReport


def parse_bass_score(musicxml_path: Optional[str], timeline: ScoreTimeline) -> List[PartEvent]:
    return parse_part_score(musicxml_path, timeline, BASS)


def audit_bass(
    timeline: ScoreTimeline,
    midi_path: Optional[str],
    musicxml_path: Optional[str],
) -> PartAuditReport:
    return audit_part(timeline, midi_path, musicxml_path, BASS)


def write_bass_report(output_path: str, report: PartAuditReport) -> str:
    return write_part_report(output_path, report, BASS)
