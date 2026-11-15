import os

# Tests never call the language model, even on a machine with credentials.
os.environ["PATHWAY_LLM"] = "0"
for name in ("VERDA_INFERENCE_API_KEY", "VERDA_INFERENCE_BASE_URL", "VERDA_MODEL", "VERDA_MAX_TOKENS"):
    os.environ.pop(name, None)
