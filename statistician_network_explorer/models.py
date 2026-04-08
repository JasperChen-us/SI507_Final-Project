from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Author:
    author_id: int
    name: str
    paper_count: int
    topic_distribution: dict[str, float]
    topic_entropy: float
    collaboration_degree: int = 0
    in_collaboration_graph: bool = False

    @property
    def dominant_topic(self) -> str:
        return max(self.topic_distribution, key=self.topic_distribution.get)

    def top_topics(self, limit: int = 3) -> list[tuple[str, float]]:
        return sorted(
            self.topic_distribution.items(),
            key=lambda item: item[1],
            reverse=True,
        )[:limit]


@dataclass(frozen=True)
class Paper:
    paper_id: int
    title: str
    year: int
    journal: str
    topic_distribution: dict[str, float]
    source_url: str = ""

    @property
    def dominant_topic(self) -> str:
        return max(self.topic_distribution, key=self.topic_distribution.get)


@dataclass(frozen=True)
class Topic:
    name: str
    paper_count: int
    author_count: int
    related_topics: list[tuple[str, float]]
