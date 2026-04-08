from __future__ import annotations

from dataclasses import dataclass


def _sorted_topics(topic_distribution: dict[str, float]) -> list[tuple[str, float]]:
    return sorted(
        topic_distribution.items(),
        key=lambda item: item[1],
        reverse=True,
    )


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
        return _sorted_topics(self.topic_distribution)[:limit]

    def topic_weight(self, topic_name: str) -> float:
        return float(self.topic_distribution.get(topic_name, 0.0))

    def specialization_score(self) -> float:
        return float(self.topic_distribution[self.dominant_topic])

    def breadth_score(self) -> float:
        return 1.0 - float(self.specialization_score())

    def is_specialist(self, threshold: float = 0.4) -> bool:
        return self.specialization_score() >= threshold

    def has_topic(self, topic_name: str, minimum_weight: float = 0.1) -> bool:
        return self.topic_weight(topic_name) >= minimum_weight

    def topic_overlap(self, other: "Author") -> float:
        shared_topics = set(self.topic_distribution) | set(other.topic_distribution)
        return float(
            sum(min(self.topic_weight(topic), other.topic_weight(topic)) for topic in shared_topics)
        )

    def profile_summary(self) -> str:
        focus = "specialist" if self.is_specialist() else "broad researcher"
        return (
            f"{self.name} has {self.paper_count} papers, focuses most on {self.dominant_topic}, "
            f"and looks like a {focus}."
        )


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

    def top_topics(self, limit: int = 3) -> list[tuple[str, float]]:
        return _sorted_topics(self.topic_distribution)[:limit]

    def topic_weight(self, topic_name: str) -> float:
        return float(self.topic_distribution.get(topic_name, 0.0))

    def publication_label(self) -> str:
        return f"{self.journal} ({self.year})"

    def matches_topic(self, topic_name: str, minimum_weight: float = 0.2) -> bool:
        return self.topic_weight(topic_name) >= minimum_weight

    def summary(self) -> str:
        return (
            f"{self.title} was published in {self.publication_label()} "
            f"and is most associated with {self.dominant_topic}."
        )


@dataclass(frozen=True)
class Topic:
    name: str
    paper_count: int
    author_count: int
    related_topics: list[tuple[str, float]]

    def top_related(self, limit: int = 3) -> list[tuple[str, float]]:
        return self.related_topics[:limit]

    def strongest_related_topic(self) -> tuple[str, float] | None:
        return self.related_topics[0] if self.related_topics else None

    def related_topic_names(self, limit: int = 5) -> list[str]:
        return [name for name, _ in self.related_topics[:limit]]

    def summary(self) -> str:
        strongest = self.strongest_related_topic()
        if strongest is None:
            return f"{self.name} has {self.paper_count} papers and {self.author_count} authors."
        return (
            f"{self.name} has {self.paper_count} papers and {self.author_count} authors; "
            f"its strongest related topic is {strongest[0]}."
        )
