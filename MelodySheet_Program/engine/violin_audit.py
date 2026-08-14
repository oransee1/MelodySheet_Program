"""바이올린이 악보 음정·화성대로인지 대조.

시계는 악보 마디 격자. 비교 대상은 MusicXML Violin 성부와
MIDI Violin 트랙(program 40)뿐이다. 피아노·첼로·베이스는 넣지 않는다.
이음줄로만 이어지는 음은 새 발음이 아니다.
"""
from __future__ import annotations

from typing import List, Optional

from engine.part_audit import (
    VIOLIN,
    PartAuditReport,
    PartEvent,
    PartHit,
    audit_part,
    parse_part_score,
    write_part_report,
)
from engine.score_timeline import ScoreTimeline

ViolinEvent = PartEvent
ViolinHit = PartHit
ViolinAuditReport = PartAuditReport


def parse_violin_score(musicxml_path: Optional[str], timeline: ScoreTimeline) -> List[PartEvent]:
    return parse_part_score(musicxml_path, timeline, VIOLIN)


def audit_violin(
    timeline: ScoreTimeline,
    midi_path: Optional[str],
    musicxml_path: Optional[str],
) -> PartAuditReport:
    return audit_part(timeline, midi_path, musicxml_path, VIOLIN)


def write_violin_report(output_path: str, report: PartAuditReport) -> str:
    return write_part_report(output_path, report, VIOLIN)
