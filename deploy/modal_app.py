"""Serve Cancer Care Atlas on Modal, with a public link for the judges.

    uvx modal deploy deploy/modal_app.py        (from the repository root)

The cached open data in data/ is part of the image, so the app needs no key and no network.
The three summary sentences come from the fixed template (PATHWAY_LLM=0): the link shows
exactly what the code computes.
"""
from pathlib import Path

import modal

ROOT = Path(__file__).resolve().parent.parent

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_pyproject(str(ROOT / "pyproject.toml"))
    .env({"PATHWAY_LLM": "0"})
    .add_local_dir(ROOT, remote_path="/root/app",
                   ignore=[".venv", ".git", "**/__pycache__", ".pytest_cache", "docs/decks", "tests", "*.pdf"])
)

app = modal.App("pathway-watch", image=image)


# One container stays warm, so a judge never waits for a cold start. It costs a few cents an hour of Modal credits.
@app.function(min_containers=1, max_containers=1, timeout=600)
@modal.concurrent(max_inputs=50)
@modal.asgi_app(label="cancer-care-atlas")
def web():
    import os
    import sys

    os.chdir("/root/app")
    sys.path.insert(0, "/root/app")
    from backend.app import app as fastapi_app
    return fastapi_app
