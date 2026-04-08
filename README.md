# Statistician Network Explorer

This project implements the SI 507 final project using MADStat and MADStaText datasets. It builds a graph-centered explorer for statistical research with an author-topic graph, a coauthorship graph, and a topic-similarity graph.

## Interaction modes

- Author search and profile exploration
- Topic exploration
- Author comparison
- Collaboration path tracing
- Rankings by papers, collaboration degree, focus, and breadth

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
