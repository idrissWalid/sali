"""Find and download the French MultiEURLEX dataset (datasets v5 compatible)."""
import ssl, certifi, os

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

_orig = ssl.create_default_context
def _p(*a,**kw):
    ctx = _orig(*a,**kw); ctx.load_verify_locations(cafile=certifi.where()); return ctx
ssl.create_default_context = _p
orig_ldc = ssl.SSLContext.load_default_certs
def p2(self,*a,**kw):
    try: return orig_ldc(self,*a,**kw)
    except: return self.load_verify_locations(cafile=certifi.where())
ssl.SSLContext.load_default_certs = p2

import json, urllib.request

# Check available Parquet configs
print("=== Checking available Parquet configs ===")
try:
    url = "https://datasets-server.huggingface.co/parquet?dataset=nlpaueb/multi_eurlex"
    req = urllib.request.Request(url, headers={"User-Agent": "python"})
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read())
    configs = set()
    for item in data.get("parquet_files", []):
        configs.add(item.get("config", ""))
    print(f"Available configs: {sorted(configs)}")
except Exception as e:
    print(f"Parquet API error: {e}")

# Try loading via datasets with different approaches
from datasets import load_dataset

approaches = [
    ("nlpaueb/multi_eurlex", "fr"),
    ("nlpaueb/multi_eurlex", "all_languages"),
]

# Also try direct parquet URL approach
print("\n=== Trying direct Parquet load ===")
try:
    ds = load_dataset("parquet",
        data_files="https://huggingface.co/datasets/nlpaueb/multi_eurlex/resolve/refs%2Fconvert%2Fparquet/fr/test/0000.parquet",
        split="train")
    print(f"Direct parquet OK: {len(ds)} samples")
    print(f"Columns: {ds.column_names}")
    print(f"First sample keys: {list(ds[0].keys())}")
except Exception as e:
    print(f"Direct parquet failed: {e}")

# Try the all_languages config
print("\n=== Trying all_languages config ===")
try:
    ds = load_dataset("parquet",
        data_files="https://huggingface.co/datasets/nlpaueb/multi_eurlex/resolve/refs%2Fconvert%2Fparquet/all_languages/test/0000.parquet",
        split="train")
    print(f"all_languages OK: {len(ds)} samples")
    print(f"Columns: {ds.column_names}")
    if "text" in ds.column_names:
        sample = ds[0]["text"]
        if isinstance(sample, dict):
            print(f"Languages in text: {list(sample.keys())}")
        else:
            print(f"text type: {type(sample)}, preview: {str(sample)[:100]}")
except Exception as e:
    print(f"all_languages failed: {e}")
