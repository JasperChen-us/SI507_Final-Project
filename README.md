# Statistician Network Explorer

This project implements the SI 507 final project using the provided MADStat and MADStaText datasets. It builds a graph-centered explorer for statistical research with an author-topic graph, a coauthorship graph, and a topic-similarity graph.

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

This repo is now deployment-ready without the original raw MADStat/MADStaText folders, because the app prefers the pre-exported files in `processed/`.

## Deploy to Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload only these items:
   - `app.py`
   - `requirements.txt`
   - `README.md`
   - `statistician_network_explorer/`
   - `processed/`
3. Keep the raw folders out of the repo. The included `.gitignore` is set up for that.
4. Go to Streamlit Community Cloud:
   - [https://share.streamlit.io/](https://share.streamlit.io/)
5. Click `New app`.
6. Choose your GitHub repo, branch, and set the main file path to `app.py`.
7. Deploy and share the generated public URL.

If Streamlit asks for a Python version in advanced settings, choose Python 3.11 to match the environment used for testing here.

## Test

```powershell
py -m pytest
```
