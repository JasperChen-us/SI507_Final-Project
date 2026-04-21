# Statistician Network Explorer

This project implements the SI 507 final project using MADStat and MADStaText datasets. It builds a graph-centered explorer for statistical research with an author-topic graph, a coauthorship graph, and a topic-similarity graph.
website: https://si507final-project-ky36zhb79cmmf52fkflbgx.streamlit.app/

## Interaction modes

- Author search and profile exploration
- Topic exploration
- Author comparison
- Collaboration path tracing
- Rankings by papers, collaboration degree, focus, and breadth

## How to use the website

The app is organized into tabs, and each tab answers a different kind of question about the statistics research network.

### 1. Author search and profile exploration

Use this section when you want to learn about one specific researcher.

What you can do:
- Type part of an author's name and choose a matching result.
- View the author's number of papers, dominant research topic, and collaboration degree.
- See a topic profile chart showing how their work is distributed across the 11 topic areas.
- View similar authors based on topic distribution, even if they have never coauthored a paper.
- See top collaborators from the coauthorship graph.
- Browse a list of that author's recent papers, including year, journal, and dominant topic.

This is useful for questions like:
- What topics does this statistician work on most?
- Who has a similar research profile?
- Does this author collaborate broadly or narrowly?

### 2. Topic exploration

Use this section when you want to start from a research area instead of a person.

What you can do:
- Select one of the 11 topics from the dataset.
- See how many papers and authors are associated with that topic.
- View a small related-topic network that shows which topics tend to be connected through shared author interests.
- Explore top authors associated with the selected topic.
- Explore top papers most strongly associated with that topic.

This is useful for questions like:
- Which researchers are most associated with Bayesian methods?
- What papers are strongly connected to time series or regression?
- Which topics tend to appear near each other in the research landscape?

### 3. Author comparison

Use this section when you want to compare two researchers directly.

What you can do:
- Choose two authors.
- View a topic similarity score between them.
- Compare their topic weights side by side in a bar chart.
- See shared papers if they have coauthored together.
- See the shortest collaboration path between them in the coauthorship graph when one exists.

This is useful for questions like:
- Are these two statisticians working on similar problems?
- Do they collaborate directly, indirectly, or not at all?
- Which topics separate their research profiles most?

### 4. Collaboration path tracing

Use this section when you want to explore the network structure itself.

What you can do:
- Select two authors from the coauthorship network.
- Compute the shortest collaboration path between them.
- View the path as a small network diagram.

This is useful for questions like:
- How is one researcher connected to another?
- Are two authors in the same collaboration neighborhood?
- Which people serve as bridges between parts of the network?

### 5. Rankings by papers, collaboration degree, focus, and breadth

Use this section when you want a high-level summary of who stands out in the dataset.

What you can do:
- Rank authors by total paper count.
- Rank authors by collaboration degree, meaning how many coauthors they have in the provided collaboration graph.
- Rank authors by dominant topic weight, which highlights researchers with a strong concentration in one area.
- Rank authors by topic entropy, which captures breadth across topics rather than narrow specialization.

How to interpret the ranking metrics:
- `paper_count`: productivity based on number of linked papers.
- `coauthor_degree`: number of distinct collaborators in the available coauthorship graph.
- `dominant_topic_weight`: how strongly an author is concentrated in their main topic.
- `topic_entropy`: how evenly an author's work is spread across multiple topics.

This is useful for questions like:
- Who publishes the most?
- Who is most connected socially in the collaboration graph?
- Who is highly specialized?
- Who has the broadest research profile?

## Project files

- `app.py`: Streamlit interface
- `statistician_network_explorer/data.py`: preprocessing and cached data loading
- `statistician_network_explorer/models.py`: domain classes
- `statistician_network_explorer/repository.py`: graph queries and analytics
- `statistician_network_explorer/visuals.py`: Plotly chart helpers
- `processed/`: lightweight deployment data used by Streamlit Community Cloud
- `tests/`: behavioral tests

## Run

```powershell
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

## Test

```powershell
py -m pytest
```
