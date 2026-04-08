from __future__ import annotations

from pathlib import Path

import networkx as nx
import streamlit as st

from statistician_network_explorer.repository import StatisticianNetworkRepository
from statistician_network_explorer.visuals import comparison_figure, network_figure, topic_distribution_figure


PROJECT_ROOT = Path(__file__).resolve().parent


@st.cache_resource(show_spinner=False)
def get_repository() -> StatisticianNetworkRepository:
    return StatisticianNetworkRepository.from_project_root(PROJECT_ROOT)


def author_selector(repo: StatisticianNetworkRepository, label: str, key: str) -> str:
    query = st.text_input(label, key=f"{key}_query", placeholder="Type part of an author name")
    matches = repo.search_authors(query)
    if not matches:
        matches = repo.search_authors("")
    return st.selectbox("Choose an author", matches, key=f"{key}_select")


def render_overview(repo: StatisticianNetworkRepository) -> None:
    st.subheader("Project Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Authors", f"{len(repo.authors):,}")
    col2.metric("Papers", f"{len(repo.papers):,}")
    col3.metric("Topics", len(repo.topic_columns))
    col4.metric("Collab Nodes", f"{repo.coauthor_graph.number_of_nodes():,}")

    st.markdown(
        """
        This project uses an author-topic graph as the primary structure and layers in a coauthorship graph
        plus a topic-similarity graph. You can search authors, explore topics, compare research profiles,
        and trace collaboration paths through the statistics literature.
        """
    )

    st.dataframe(repo.get_rankings("coauthor_degree", limit=15), use_container_width=True, hide_index=True)
    st.plotly_chart(network_figure(repo.topic_graph, "Topic Relationship Graph"), use_container_width=True)


def render_author_explorer(repo: StatisticianNetworkRepository) -> None:
    st.subheader("Author Explorer")
    author_name = author_selector(repo, "Search for an author", "author")
    author = repo.get_author(author_name)
    papers = repo.get_author_papers(author_name)
    similar = repo.get_similar_authors(author_name)
    collaborators = repo.get_top_collaborators(author_name)

    col1, col2, col3 = st.columns(3)
    col1.metric("Papers", author.paper_count)
    col2.metric("Dominant Topic", author.dominant_topic)
    col3.metric("Collaboration Degree", author.collaboration_degree)

    st.plotly_chart(
        topic_distribution_figure(author.topic_distribution, f"{author.name}: topic profile"),
        use_container_width=True,
    )
    st.markdown("Top similar authors by topic profile")
    st.dataframe(similar, use_container_width=True, hide_index=True)
    st.markdown("Top collaborators in the provided coauthorship graph")
    st.dataframe(collaborators, use_container_width=True, hide_index=True)
    st.markdown("Recent papers")
    st.dataframe(
        [
            {
                "title": paper.title,
                "year": paper.year,
                "journal": paper.journal,
                "dominant_topic": paper.dominant_topic,
                "source_url": paper.source_url,
            }
            for paper in papers
        ],
        use_container_width=True,
        hide_index=True,
    )


def render_topic_explorer(repo: StatisticianNetworkRepository) -> None:
    st.subheader("Topic Explorer")
    topic_name = st.selectbox("Choose a topic", repo.topic_columns)
    profile = repo.get_topic_profile(topic_name)
    topic = profile["topic"]

    col1, col2 = st.columns(2)
    col1.metric("Paper Count", f"{topic.paper_count:,}")
    col2.metric("Author Count", f"{topic.author_count:,}")

    related_graph = nx.Graph()
    related_graph.add_node(topic.name)
    for related_name, score in topic.related_topics[:6]:
        related_graph.add_edge(topic.name, related_name, weight=score)
    st.plotly_chart(
        network_figure(related_graph, f"Related topics around {topic.name}", highlight_nodes=[topic.name]),
        use_container_width=True,
    )
    st.markdown("Top authors")
    st.dataframe(profile["top_authors"], use_container_width=True, hide_index=True)
    st.markdown("Top papers")
    st.dataframe(profile["top_papers"], use_container_width=True, hide_index=True)


def render_compare_authors(repo: StatisticianNetworkRepository) -> None:
    st.subheader("Compare Authors")
    col1, col2 = st.columns(2)
    with col1:
        author_a = author_selector(repo, "First author", "compare_a")
    with col2:
        author_b = author_selector(repo, "Second author", "compare_b")

    comparison = repo.compare_authors(author_a, author_b)
    st.metric("Topic similarity", f"{comparison['topic_similarity']:.3f}")
    st.plotly_chart(
        comparison_figure(
            comparison["comparison_table"],
            comparison["author_a"].name,
            comparison["author_b"].name,
        ),
        use_container_width=True,
    )
    st.markdown("Shared papers")
    st.dataframe(comparison["shared_papers"], use_container_width=True, hide_index=True)

    path = comparison["collaboration_path"]
    if path:
        path_graph = nx.path_graph(path)
        st.plotly_chart(
            network_figure(path_graph, "Shortest collaboration path", highlight_nodes=path),
            use_container_width=True,
        )
    else:
        st.info("No collaboration path was found in the provided coauthorship subset.")


def render_paths_and_rankings(repo: StatisticianNetworkRepository) -> None:
    st.subheader("Paths and Rankings")
    network_authors = sorted(repo.coauthor_graph.nodes)
    start = st.selectbox("Start author", network_authors, index=0)
    end = st.selectbox("End author", network_authors, index=min(25, len(network_authors) - 1))
    path = repo.shortest_collaboration_path(start, end)
    if path:
        st.write(" -> ".join(path))
        st.plotly_chart(network_figure(nx.path_graph(path), "Collaboration path", highlight_nodes=path), use_container_width=True)
    else:
        st.warning("These authors are not connected in the provided collaboration graph.")

    metric = st.selectbox(
        "Ranking metric",
        ["paper_count", "coauthor_degree", "topic_entropy", "dominant_topic_weight"],
    )
    st.dataframe(repo.get_rankings(metric), use_container_width=True, hide_index=True)


def main() -> None:
    st.set_page_config(page_title="Statistician Network Explorer", layout="wide")
    st.title("Statistician Network Explorer")
    repo = get_repository()

    overview_tab, author_tab, topic_tab, compare_tab, path_tab = st.tabs(
        ["Overview", "Author Explorer", "Topic Explorer", "Compare Authors", "Paths & Rankings"]
    )
    with overview_tab:
        render_overview(repo)
    with author_tab:
        render_author_explorer(repo)
    with topic_tab:
        render_topic_explorer(repo)
    with compare_tab:
        render_compare_authors(repo)
    with path_tab:
        render_paths_and_rankings(repo)


if __name__ == "__main__":
    main()
