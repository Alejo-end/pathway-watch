import os

# Tests never call the language model, even on a machine with credentials.
os.environ["PATHWAY_LLM"] = "0"
