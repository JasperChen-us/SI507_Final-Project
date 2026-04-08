from __future__ import annotations

import math
import pickle
import subprocess
from dataclasses import dataclass
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.io import loadmat


PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_CACHE_PATH = PACKAGE_ROOT.parent / ".cache" / "stat_network_processed.pkl"


@dataclass
class ProcessedData:
    authors: pd.DataFrame
    papers: pd.DataFrame
    author_papers: pd.DataFrame
    paper_topics: pd.DataFrame
    topic_columns: list[str]
    topic_graph: nx.Graph
    topic_similarity: pd.DataFrame
    coauthor_graph: nx.Graph
    coauthor_authors: list[str]


def normalize_topic_name(name: str) -> str:
    return " ".join(str(name).replace("\n", " ").split())


def compute_entropy(values: pd.Series) -> float:
    probs = values[values > 0]
    if probs.empty:
        return 0.0
    entropy = float(-(probs * np.log(probs)).sum())
    return entropy / math.log(len(values))


def ensure_cache_dir(cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)


def export_paper_metadata(project_root: Path) -> Path:
    processed_dir = project_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "paper_metadata.csv"
    if csv_path.exists():
        return csv_path

    bibtex_path = project_root / "MADStat-final-version" / "Ready-to-use data matrices" / "Full data" / "BibtexInfo.RData"
    rscript_path = Path(r"C:\Program Files\R\R-4.5.1\bin\Rscript.exe")
    bibtex_r_path = str(bibtex_path).replace("\\", "/")
    csv_r_path = str(csv_path).replace("\\", "/")
    script = (
        f"load('{bibtex_r_path}'); "
        "paper$paper_id <- seq_len(nrow(paper)); "
        f"utils::write.csv(paper, '{csv_r_path}', row.names = FALSE)"
    )
    subprocess.run([str(rscript_path), "-e", script], check=True)
    return csv_path


def export_author_papers(project_root: Path) -> Path:
    processed_dir = project_root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    csv_path = processed_dir / "author_papers.csv"
    if csv_path.exists():
        return csv_path

    author_paper_path = project_root / "MADStaText" / "2-Citation and bibtex information" / "AuthorPaperInfo.RData"
    rscript_path = Path(r"C:\Program Files\R\R-4.5.1\bin\Rscript.exe")
    author_paper_r_path = str(author_paper_path).replace("\\", "/")
    csv_r_path = str(csv_path).replace("\\", "/")
    script = (
        f"load('{author_paper_r_path}'); "
        f"utils::write.csv(AuPapMat, '{csv_r_path}', row.names = FALSE)"
    )
    subprocess.run([str(rscript_path), "-e", script], check=True)
    return csv_path


def read_author_names(project_root: Path) -> pd.DataFrame:
    processed_path = project_root / "processed" / "author_names.csv"
    if processed_path.exists():
        return pd.read_csv(processed_path)

    author_path = project_root / "MADStat-final-version" / "Ready-to-use data matrices" / "Full data" / "author_name.txt"
    names = author_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return pd.DataFrame(
        {
            "author_id": np.arange(1, len(names) + 1, dtype=int),
            "author_name": names,
        }
    )


def read_author_papers(project_root: Path) -> pd.DataFrame:
    csv_path = export_author_papers(project_root)
    author_papers = pd.read_csv(csv_path).rename(
        columns={
            "idxAu": "author_id",
            "idxPap": "paper_id",
            "journal": "journal_code",
        }
    )
    author_papers["author_id"] = author_papers["author_id"].astype(int)
    author_papers["paper_id"] = author_papers["paper_id"].astype(int)
    author_papers["year"] = author_papers["year"].astype(int)
    return author_papers


def read_topic_data(project_root: Path) -> tuple[pd.DataFrame, list[str]]:
    processed_path = project_root / "processed" / "paper_topics.csv"
    if processed_path.exists():
        paper_topics = pd.read_csv(processed_path, low_memory=False)
        topic_names = [column for column in paper_topics.columns if column != "paper_id"]
        return paper_topics, topic_names

    import pyreadr

    topic_path = project_root / "MADStaText" / "3-Topic modeling results" / "TopicResults.RData"
    result = pyreadr.read_r(topic_path)
    topic_names = [normalize_topic_name(name) for name in result["TopicNames"]["TopicNames"].tolist()]
    w_hat = result["W_hat"]
    paper_topics = w_hat.T.reset_index(drop=True)
    paper_topics.columns = topic_names
    paper_topics.insert(0, "paper_id", np.arange(1, len(paper_topics) + 1, dtype=int))
    return paper_topics, topic_names


def read_paper_metadata(project_root: Path) -> pd.DataFrame:
    csv_path = export_paper_metadata(project_root)
    papers = pd.read_csv(csv_path, low_memory=False)
    papers["paper_id"] = papers["paper_id"].astype(int)
    papers["year"] = papers["year"].fillna(0).astype(int)
    papers["sourceURL"] = papers["sourceURL"].fillna("")
    return papers


def build_papers_dataframe(papers: pd.DataFrame, paper_topics: pd.DataFrame, topic_columns: list[str]) -> pd.DataFrame:
    papers_df = papers.merge(paper_topics, on="paper_id", how="left")
    papers_df["dominant_topic"] = papers_df[topic_columns].idxmax(axis=1)
    papers_df["dominant_topic_weight"] = papers_df[topic_columns].max(axis=1)
    papers_df["journal_label"] = papers_df["issn"].fillna("").replace("", "Unknown ISSN")
    return papers_df


def build_authors_dataframe(
    author_names: pd.DataFrame,
    author_papers: pd.DataFrame,
    paper_topics: pd.DataFrame,
    topic_columns: list[str],
) -> pd.DataFrame:
    author_topic_rows = author_papers[["author_id", "paper_id"]].merge(paper_topics, on="paper_id", how="left")
    topic_sums = author_topic_rows.groupby("author_id")[topic_columns].sum()
    paper_counts = author_papers.groupby("author_id")["paper_id"].nunique().rename("paper_count")
    author_topics = topic_sums.div(topic_sums.sum(axis=1), axis=0).fillna(0.0)
    authors = author_names.merge(paper_counts, on="author_id", how="left").fillna({"paper_count": 0})
    authors["paper_count"] = authors["paper_count"].astype(int)
    authors = authors.merge(author_topics, on="author_id", how="left").fillna(0.0)
    authors["topic_entropy"] = authors[topic_columns].apply(compute_entropy, axis=1)
    authors["dominant_topic"] = authors[topic_columns].idxmax(axis=1)
    authors["dominant_topic_weight"] = authors[topic_columns].max(axis=1)
    return authors


def read_coauthor_graph(project_root: Path) -> tuple[nx.Graph, list[str]]:
    processed_edges_path = project_root / "processed" / "coauthor_edges.csv"
    if processed_edges_path.exists():
        edges = pd.read_csv(processed_edges_path)
        graph = nx.from_pandas_edgelist(edges, source="source", target="target")
        author_names = sorted(set(edges["source"]).union(edges["target"]))
        return graph, author_names

    coauthor_path = project_root / "MADStat-final-version" / "Ready-to-use data matrices" / "Co-authorship networks" / "CoauAdjFinal.mat"
    mat = loadmat(coauthor_path, simplify_cells=True)
    sparse_matrix = mat["A"]
    names = [str(name) for name in mat["authorNames"]]
    graph = nx.from_scipy_sparse_array(sparse_matrix)
    graph = nx.relabel_nodes(graph, dict(enumerate(names)))
    return graph, names


def build_topic_graph(authors: pd.DataFrame, topic_columns: list[str]) -> tuple[nx.Graph, pd.DataFrame]:
    topic_matrix = authors[topic_columns].to_numpy(dtype=float)
    norms = np.linalg.norm(topic_matrix, axis=0)
    similarity = topic_matrix.T @ topic_matrix
    denominator = np.outer(norms, norms)
    with np.errstate(divide="ignore", invalid="ignore"):
        similarity = np.divide(similarity, denominator, out=np.zeros_like(similarity), where=denominator > 0)
    similarity_df = pd.DataFrame(similarity, index=topic_columns, columns=topic_columns)

    graph = nx.Graph()
    for topic in topic_columns:
        graph.add_node(topic)

    off_diagonal = similarity[np.triu_indices_from(similarity, k=1)]
    threshold = float(np.quantile(off_diagonal, 0.65)) if len(off_diagonal) else 0.0
    for i, topic_a in enumerate(topic_columns):
        for j in range(i + 1, len(topic_columns)):
            topic_b = topic_columns[j]
            weight = float(similarity[i, j])
            if weight >= threshold:
                graph.add_edge(topic_a, topic_b, weight=weight)
    return graph, similarity_df


def attach_collaboration_stats(authors: pd.DataFrame, coauthor_graph: nx.Graph) -> pd.DataFrame:
    degree_map = dict(coauthor_graph.degree())
    authors = authors.copy()
    authors["coauthor_degree"] = authors["author_name"].map(degree_map).fillna(0).astype(int)
    authors["in_coauthor_graph"] = authors["author_name"].isin(coauthor_graph.nodes)
    return authors


def build_processed_data(project_root: Path) -> ProcessedData:
    author_names = read_author_names(project_root)
    author_papers = read_author_papers(project_root)
    paper_topics, topic_columns = read_topic_data(project_root)
    paper_metadata = read_paper_metadata(project_root)
    papers = build_papers_dataframe(paper_metadata, paper_topics, topic_columns)
    authors = build_authors_dataframe(author_names, author_papers, paper_topics, topic_columns)
    coauthor_graph, coauthor_authors = read_coauthor_graph(project_root)
    authors = attach_collaboration_stats(authors, coauthor_graph)
    topic_graph, topic_similarity = build_topic_graph(authors[authors["paper_count"] > 0], topic_columns)
    return ProcessedData(
        authors=authors,
        papers=papers,
        author_papers=author_papers,
        paper_topics=paper_topics,
        topic_columns=topic_columns,
        topic_graph=topic_graph,
        topic_similarity=topic_similarity,
        coauthor_graph=coauthor_graph,
        coauthor_authors=coauthor_authors,
    )


def load_or_build_processed_data(project_root: Path, cache_path: Path | None = None, force_rebuild: bool = False) -> ProcessedData:
    cache_path = cache_path or DEFAULT_CACHE_PATH
    ensure_cache_dir(cache_path)
    if cache_path.exists() and not force_rebuild:
        with cache_path.open("rb") as handle:
            return pickle.load(handle)

    processed = build_processed_data(project_root)
    with cache_path.open("wb") as handle:
        pickle.dump(processed, handle)
    return processed
