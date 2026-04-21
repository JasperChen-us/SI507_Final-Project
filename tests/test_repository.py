import networkx as nx
import pandas as pd

from statistician_network_explorer.data import ProcessedData
from statistician_network_explorer.repository import StatisticianNetworkRepository


def build_repository() -> StatisticianNetworkRepository:
    topic_columns = ["Bayes", "Inference", "Networks"]
    authors = pd.DataFrame(
        [
            {"author_id": 1, "author_name": "Alice", "paper_count": 2, "Bayes": 0.7, "Inference": 0.2, "Networks": 0.1, "topic_entropy": 0.6, "dominant_topic": "Bayes", "dominant_topic_weight": 0.7, "coauthor_degree": 1, "in_coauthor_graph": True},
            {"author_id": 2, "author_name": "Bob", "paper_count": 2, "Bayes": 0.6, "Inference": 0.3, "Networks": 0.1, "topic_entropy": 0.7, "dominant_topic": "Bayes", "dominant_topic_weight": 0.6, "coauthor_degree": 2, "in_coauthor_graph": True},
            {"author_id": 3, "author_name": "Cara", "paper_count": 1, "Bayes": 0.1, "Inference": 0.2, "Networks": 0.7, "topic_entropy": 0.6, "dominant_topic": "Networks", "dominant_topic_weight": 0.7, "coauthor_degree": 1, "in_coauthor_graph": True},
        ]
    )
    papers = pd.DataFrame(
        [
            {"paper_id": 11, "title": "Bayesian Paper", "year": 2010, "journal_label": "AoS", "sourceURL": "", "Bayes": 0.8, "Inference": 0.1, "Networks": 0.1, "dominant_topic": "Bayes", "dominant_topic_weight": 0.8},
            {"paper_id": 12, "title": "Network Paper", "year": 2011, "journal_label": "JRSSB", "sourceURL": "", "Bayes": 0.2, "Inference": 0.1, "Networks": 0.7, "dominant_topic": "Networks", "dominant_topic_weight": 0.7},
        ]
    )
    author_papers = pd.DataFrame(
        [
            {"author_id": 1, "paper_id": 11},
            {"author_id": 2, "paper_id": 11},
            {"author_id": 2, "paper_id": 12},
            {"author_id": 3, "paper_id": 12},
        ]
    )
    topic_graph = nx.Graph()
    topic_graph.add_edge("Bayes", "Inference", weight=0.8)
    topic_graph.add_edge("Inference", "Networks", weight=0.5)
    topic_similarity = pd.DataFrame(
        [[1.0, 0.8, 0.2], [0.8, 1.0, 0.5], [0.2, 0.5, 1.0]],
        index=topic_columns,
        columns=topic_columns,
    )
    coauthor_graph = nx.Graph()
    coauthor_graph.add_edges_from([("Alice", "Bob"), ("Bob", "Cara")])
    processed = ProcessedData(
        authors=authors,
        papers=papers,
        author_papers=author_papers,
        paper_topics=pd.DataFrame(),
        topic_columns=topic_columns,
        topic_graph=topic_graph,
        topic_similarity=topic_similarity,
        coauthor_graph=coauthor_graph,
        coauthor_authors=["Alice", "Bob", "Cara"],
    )
    return StatisticianNetworkRepository(processed)


def test_search_and_similarity():
    repo = build_repository()
    assert repo.search_authors("ali") == ["Alice"]
    similar = repo.get_similar_authors("Alice", limit=1)
    assert similar.iloc[0]["author_name"] == "Bob"


def test_compare_authors_and_shared_papers():
    repo = build_repository()
    comparison = repo.compare_authors("Alice", "Bob")
    assert comparison["shared_papers"][0]["title"] == "Bayesian Paper"
    assert comparison["collaboration_path"] == ["Alice", "Bob"]


def test_topic_profile_and_path():
    repo = build_repository()
    topic = repo.get_topic("Bayes")
    assert topic.related_topics[0][0] == "Inference"
    assert repo.shortest_collaboration_path("Alice", "Cara") == ["Alice", "Bob", "Cara"]
