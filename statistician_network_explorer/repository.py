from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from .data import ProcessedData, load_or_build_processed_data
from .models import Author, Paper, Topic


class StatisticianNetworkRepository:
    def __init__(self, processed: ProcessedData):
        self.processed = processed
        self.authors = processed.authors.copy()
        self.papers = processed.papers.copy()
        self.author_papers = processed.author_papers.copy()
        self.topic_columns = processed.topic_columns
        self.coauthor_graph = processed.coauthor_graph
        self.topic_graph = processed.topic_graph
        self.topic_similarity = processed.topic_similarity
        self._authors_with_papers = self.authors[self.authors["paper_count"] > 0].reset_index(drop=True)
        self._author_topic_matrix = self._authors_with_papers[self.topic_columns].to_numpy(dtype=float)
        norms = np.linalg.norm(self._author_topic_matrix, axis=1)
        self._author_norms = np.where(norms == 0, 1.0, norms)

    @classmethod
    def from_project_root(cls, project_root: str | Path, force_rebuild: bool = False) -> "StatisticianNetworkRepository":
        processed = load_or_build_processed_data(Path(project_root), force_rebuild=force_rebuild)
        return cls(processed)

    def search_authors(self, query: str, limit: int = 15) -> list[str]:
        normalized = query.strip().lower()
        if not normalized:
            return self._authors_with_papers["author_name"].sort_values().head(limit).tolist()
        matches = self._authors_with_papers[
            self._authors_with_papers["author_name"].str.lower().str.contains(normalized, na=False)
        ]
        return matches.sort_values(["paper_count", "coauthor_degree"], ascending=False)["author_name"].head(limit).tolist()

    def _author_row(self, author_name: str) -> pd.Series:
        matches = self.authors[self.authors["author_name"] == author_name]
        if matches.empty:
            raise KeyError(f"Unknown author: {author_name}")
        return matches.iloc[0]

    def get_author(self, author_name: str) -> Author:
        row = self._author_row(author_name)
        distribution = {topic: float(row[topic]) for topic in self.topic_columns}
        return Author(
            author_id=int(row["author_id"]),
            name=str(row["author_name"]),
            paper_count=int(row["paper_count"]),
            topic_distribution=distribution,
            topic_entropy=float(row["topic_entropy"]),
            collaboration_degree=int(row["coauthor_degree"]),
            in_collaboration_graph=bool(row["in_coauthor_graph"]),
        )

    def _build_paper_from_row(self, row: pd.Series) -> Paper:
        return Paper(
            paper_id=int(row["paper_id"]),
            title=str(row["title"]),
            year=int(row["year"]),
            journal=str(row.get("journal_label", "Unknown")),
            source_url=str(row.get("sourceURL", "")),
            topic_distribution={topic: float(row[topic]) for topic in self.topic_columns},
        )

    def get_author_papers(self, author_name: str, limit: int = 15) -> list[Paper]:
        author = self.get_author(author_name)
        paper_ids = (
            self.author_papers[self.author_papers["author_id"] == author.author_id]["paper_id"]
            .drop_duplicates()
            .tolist()
        )
        papers = self.papers[self.papers["paper_id"].isin(paper_ids)].sort_values(
            ["year", "dominant_topic_weight"],
            ascending=[False, False],
        )
        return [self._build_paper_from_row(row) for _, row in papers.head(limit).iterrows()]

    def get_similar_authors(self, author_name: str, limit: int = 10) -> pd.DataFrame:
        target_idx = self._authors_with_papers.index[self._authors_with_papers["author_name"] == author_name]
        if len(target_idx) == 0:
            raise KeyError(f"Unknown author: {author_name}")
        idx = int(target_idx[0])
        target_vector = self._author_topic_matrix[idx]
        scores = self._author_topic_matrix @ target_vector
        scores = scores / (self._author_norms * np.linalg.norm(target_vector))
        similar = self._authors_with_papers[["author_name", "paper_count", "dominant_topic"]].copy()
        similar["topic_similarity"] = scores
        similar = similar[similar["author_name"] != author_name]
        return similar.sort_values(["topic_similarity", "paper_count"], ascending=False).head(limit)

    def compare_authors(self, author_a: str, author_b: str) -> dict[str, object]:
        a = self.get_author(author_a)
        b = self.get_author(author_b)
        vector_a = np.array([a.topic_distribution[topic] for topic in self.topic_columns], dtype=float)
        vector_b = np.array([b.topic_distribution[topic] for topic in self.topic_columns], dtype=float)
        similarity = float(vector_a @ vector_b / (np.linalg.norm(vector_a) * np.linalg.norm(vector_b)))

        papers_a = set(self.author_papers[self.author_papers["author_id"] == a.author_id]["paper_id"])
        papers_b = set(self.author_papers[self.author_papers["author_id"] == b.author_id]["paper_id"])
        shared_paper_ids = sorted(papers_a & papers_b)
        shared_papers = [
            asdict(self._build_paper_from_row(row))
            for _, row in self.papers[self.papers["paper_id"].isin(shared_paper_ids)].head(10).iterrows()
        ]

        comparison = pd.DataFrame(
            {
                "topic": self.topic_columns,
                a.name: vector_a,
                b.name: vector_b,
                "difference": np.abs(vector_a - vector_b),
            }
        ).sort_values("difference", ascending=False)

        return {
            "author_a": a,
            "author_b": b,
            "topic_similarity": similarity,
            "shared_papers": shared_papers,
            "comparison_table": comparison,
            "collaboration_path": self.shortest_collaboration_path(author_a, author_b),
        }

    def get_topic(self, topic_name: str, top_n: int = 10) -> Topic:
        if topic_name not in self.topic_columns:
            raise KeyError(f"Unknown topic: {topic_name}")
        author_count = int((self.authors[topic_name] > 0).sum())
        paper_count = int((self.papers[topic_name] > 0).sum())
        related_series = self.topic_similarity.loc[topic_name].drop(index=topic_name).sort_values(ascending=False)
        related = [(name, float(score)) for name, score in related_series.head(top_n).items()]
        return Topic(name=topic_name, paper_count=paper_count, author_count=author_count, related_topics=related)

    def get_topic_profile(self, topic_name: str, top_n: int = 10) -> dict[str, object]:
        topic = self.get_topic(topic_name, top_n=top_n)
        top_authors = self.authors[self.authors["paper_count"] > 0][
            ["author_name", "paper_count", topic_name, "dominant_topic", "coauthor_degree"]
        ].sort_values([topic_name, "paper_count"], ascending=False).head(top_n)
        top_papers = self.papers[["paper_id", "title", "year", "dominant_topic_weight", topic_name, "sourceURL"]]
        top_papers = top_papers.sort_values(topic_name, ascending=False).head(top_n)
        return {
            "topic": topic,
            "top_authors": top_authors,
            "top_papers": top_papers,
        }

    def shortest_collaboration_path(self, author_a: str, author_b: str) -> list[str]:
        if author_a not in self.coauthor_graph or author_b not in self.coauthor_graph:
            return []
        try:
            return nx.shortest_path(self.coauthor_graph, author_a, author_b)
        except nx.NetworkXNoPath:
            return []

    def get_top_collaborators(self, author_name: str, limit: int = 10) -> pd.DataFrame:
        if author_name not in self.coauthor_graph:
            return pd.DataFrame(columns=["author_name", "coauthor_degree"])
        neighbors = list(self.coauthor_graph.neighbors(author_name))
        neighbor_df = self.authors[self.authors["author_name"].isin(neighbors)][["author_name", "coauthor_degree", "paper_count", "dominant_topic"]]
        return neighbor_df.sort_values(["coauthor_degree", "paper_count"], ascending=False).head(limit)

    def get_rankings(self, metric: str, limit: int = 20) -> pd.DataFrame:
        allowed = {"paper_count", "coauthor_degree", "topic_entropy", "dominant_topic_weight"}
        if metric not in allowed:
            raise ValueError(f"Unsupported metric: {metric}")
        ranking = self.authors[self.authors["paper_count"] > 0][
            ["author_name", "paper_count", "coauthor_degree", "topic_entropy", "dominant_topic", "dominant_topic_weight"]
        ]
        return ranking.sort_values(metric, ascending=False).head(limit)
