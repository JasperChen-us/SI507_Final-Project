from __future__ import annotations

import networkx as nx
import pandas as pd
import plotly.graph_objects as go


def topic_distribution_figure(topic_distribution: dict[str, float], title: str) -> go.Figure:
    ordered = sorted(topic_distribution.items(), key=lambda item: item[1], reverse=True)
    fig = go.Figure(
        data=[
            go.Bar(
                x=[name for name, _ in ordered],
                y=[value for _, value in ordered],
                marker_color="#0f766e",
            )
        ]
    )
    fig.update_layout(title=title, xaxis_title="Topic", yaxis_title="Weight", height=360)
    return fig


def comparison_figure(comparison: pd.DataFrame, author_a: str, author_b: str) -> go.Figure:
    fig = go.Figure()
    fig.add_bar(x=comparison["topic"], y=comparison[author_a], name=author_a, marker_color="#1d4ed8")
    fig.add_bar(x=comparison["topic"], y=comparison[author_b], name=author_b, marker_color="#dc2626")
    fig.update_layout(barmode="group", height=420, yaxis_title="Topic weight")
    return fig


def network_figure(graph: nx.Graph, title: str, highlight_nodes: list[str] | None = None) -> go.Figure:
    if graph.number_of_nodes() == 0:
        return go.Figure().update_layout(title=title, height=420)

    highlight_nodes = set(highlight_nodes or [])
    positions = nx.spring_layout(graph, seed=7)

    edge_x: list[float] = []
    edge_y: list[float] = []
    for source, target in graph.edges():
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    for node in graph.nodes():
        x, y = positions[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(str(node))
        node_color.append("#ef4444" if node in highlight_nodes else "#0f766e")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line={"width": 1, "color": "#94a3b8"},
            hoverinfo="none",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            marker={"size": 14, "color": node_color},
            hovertext=node_text,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        title=title,
        showlegend=False,
        xaxis={"showgrid": False, "zeroline": False, "visible": False},
        yaxis={"showgrid": False, "zeroline": False, "visible": False},
        height=420,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return fig
