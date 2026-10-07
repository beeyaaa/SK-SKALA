"""
DirectoryFilePatternTrigger — AssetWatcher(trigger=...)에 연결할 커스텀 트리거.

같은 저장소의 검증된 구현(ASSETWATCHER(AIRFLOW ASSET WATCHER)/directory_watcher/dags/
directory_watcher_trigger.py — apache-airflow==3.3.1의 공유 스트림 프로토콜 사용)을
그대로 가져왔다. 상세한 개정 이력·설계 근거 주석은 원본 파일 참고.

⚠️ 이 파일이 plugins/ 안에 있어야 하는 이유(이 Docker 실습에서 실제로 겪은 문제):
Triggerer는 DAG 파일을 재실행하지 않고 DB에 저장된 클래스 경로 문자열
("directory_watcher_trigger.DirectoryFilePatternTrigger")만으로 트리거를 재구성한다.
처음에 이 파일을 dags/에 뒀더니 dag-processor는 정상 파싱했지만 Triggerer 로그에
`Trigger failed to load code ... ModuleNotFoundError("No module named
'directory_watcher_trigger'")`가 찍히며 watcher 등록이 조용히 실패했다 — 이
컨테이너 환경에서 Triggerer의 sys.path에는 dags/가 없기 때문이다. plugins/는
Airflow의 모든 컴포넌트(Scheduler·Triggerer·dag-processor·Worker)가 sys.path에
포함시키는 폴더라 여기로 옮겨 해결했다. (원본 실습 주석의 "실전 배포에서는
plugins/나 별도 패키지로 두는 게 정석"이라는 지적이 실제로 맞았던 셈이다.)
"""

from __future__ import annotations

import asyncio
import fnmatch
import os
from collections.abc import AsyncIterator, Hashable
from typing import Any

from airflow.triggers.base import BaseEventTrigger, TriggerEvent


class DirectoryFilePatternTrigger(BaseEventTrigger):
    """`directory` 안에서 `pattern`에 매칭되는 파일이 "새로" 나타나는지 감시하는 트리거."""

    def __init__(self, *, directory: str, pattern: str, poke_interval: float = 5.0):
        super().__init__()
        self.directory = directory
        self.pattern = pattern
        self.poke_interval = poke_interval

    def serialize(self) -> tuple[str, dict[str, Any]]:
        return (
            f"{self.__class__.__module__}.{self.__class__.__qualname__}",
            {"directory": self.directory, "pattern": self.pattern, "poke_interval": self.poke_interval},
        )

    def shared_stream_key(self) -> Hashable | None:
        # 같은 (directory, poke_interval) 조합이면 폴더 리스팅 자체를 공유한다.
        return ("directory-scan", self.directory, self.poke_interval)

    @classmethod
    async def open_shared_stream(cls, kwargs: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        directory = kwargs["directory"]
        poke_interval = kwargs["poke_interval"]
        while True:
            names = os.listdir(directory) if os.path.isdir(directory) else []
            yield {"directory": directory, "names": names}
            await asyncio.sleep(poke_interval)

    async def filter_shared_stream(self, shared_stream: AsyncIterator[dict[str, Any]]) -> AsyncIterator[TriggerEvent]:
        seen: set[str] | None = None
        async for snapshot in shared_stream:
            current = {f for f in snapshot["names"] if fnmatch.fnmatch(f, self.pattern)}
            if seen is None:
                # 감시 시작 시점에 이미 있던 파일은 "새 파일"로 치지 않는다.
                self.log.info(
                    "[DirectoryFilePatternTrigger] pattern=%s 감시 시작 — 시작 시점 기존 파일 %d개는 무시: %s",
                    self.pattern, len(current), sorted(current),
                )
                seen = current
                continue
            new_files = current - seen
            if new_files:
                self.log.info(
                    "[DirectoryFilePatternTrigger] pattern=%s 새 파일 감지: %s → TriggerEvent 발생",
                    self.pattern, sorted(new_files),
                )
                yield TriggerEvent({"directory": self.directory, "files": sorted(new_files)})
                return
            seen = current

    async def run(self) -> AsyncIterator[TriggerEvent]:
        # shared_stream_key를 안 쓰는 실행 경로용 폴백(독립 검증용)
        stream = self.open_shared_stream({"directory": self.directory, "poke_interval": self.poke_interval})
        async for event in self.filter_shared_stream(stream):
            yield event
