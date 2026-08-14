"""첼로가 악보 음정·화성대로인지 대조.

시계는 악보 마디 격자. 비교 대상은 MusicXML Cello 성부와
MIDI Cello 트랙(program 42)뿐이다. 피아노·바이올린·베이스는 넣지 않는다.
이음줄로만 이어지는 음은 새 발음이 아니다.
"""
from __future__ import annotations

from typing import List, Optional

from engine.part_audit import (
    CELLO,
    PartAuditReport,
    PartEvent,
    PartHit,
    audit_part,
    parse_part_score,
    write_part_report,
)
from engine.score_timeline import ScoreTimeline

CelloEvent = PartEvent
CelloHit = PartHit
CelloAuditReport = PartAuditReport


def parse_cello_score(musicxml_path: Optional[str], timeline: ScoreTimeline) -> List[PartEvent]:
    return parse_part_score(musicxml_path, timeline, CELLO)


def audit_cello(
    timeline: ScoreTimeline,
    midi_path: Optional[str],
    musicxml_path: Optional[str],
) -> PartAuditReport:
    return audit_part(timeline, midi_path, musicxml_path, CELLO)


def write_cello_report(output_path: str, report: PartAuditReport) -> str:
    return write_part_report(output_path, report, CELLO)
