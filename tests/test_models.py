import pytest

from statistician_network_explorer.models import Author, Paper, Topic


def test_author_top_topics_and_dominant_topic():
    author = Author(
        author_id=1,
        name="Ada",
        paper_count=5,
        topic_distribution={"Bayes": 0.2, "Time Series": 0.5, "Causal": 0.3},
        topic_entropy=0.9,
    )
    assert author.dominant_topic == "Time Series"
    assert author.top_topics(2) == [("Time Series", 0.5), ("Causal", 0.3)]
    assert author.topic_weight("Bayes") == 0.2
    assert author.specialization_score() == 0.5
    assert author.is_specialist()
    assert author.has_topic("Time Series", minimum_weight=0.4)
    assert "focuses most on Time Series" in author.profile_summary()


def test_author_topic_overlap():
    author_a = Author(
        author_id=1,
        name="Ada",
        paper_count=5,
        topic_distribution={"Bayes": 0.2, "Time Series": 0.5, "Causal": 0.3},
        topic_entropy=0.9,
    )
    author_b = Author(
        author_id=2,
        name="Grace",
        paper_count=4,
        topic_distribution={"Bayes": 0.4, "Time Series": 0.1, "Causal": 0.5},
        topic_entropy=0.8,
    )
    assert author_a.topic_overlap(author_b) == pytest.approx(0.6)


def test_paper_dominant_topic():
    paper = Paper(
        paper_id=101,
        title="Network Methods",
        year=2014,
        journal="AoS",
        topic_distribution={"Bayes": 0.1, "Networks": 0.7, "Inference": 0.2},
    )
    assert paper.dominant_topic == "Networks"
    assert paper.top_topics(2) == [("Networks", 0.7), ("Inference", 0.2)]
    assert paper.publication_label() == "AoS (2014)"
    assert paper.matches_topic("Networks", minimum_weight=0.5)
    assert "most associated with Networks" in paper.summary()


def test_topic_helpers():
    topic = Topic(
        name="Bayes",
        paper_count=100,
        author_count=30,
        related_topics=[("Inference", 0.85), ("Regression", 0.7), ("Math.Stats.", 0.65)],
    )
    assert topic.top_related(2) == [("Inference", 0.85), ("Regression", 0.7)]
    assert topic.strongest_related_topic() == ("Inference", 0.85)
    assert topic.related_topic_names(2) == ["Inference", "Regression"]
    assert "strongest related topic is Inference" in topic.summary()
