"""
Downloads the FAISS vector index and metadata from HuggingFace on startup.
Runs before gunicorn starts (see render.yaml startCommand).
Skips download if files are already present (warm restart / local dev).
"""
import os
import sys
import time

FAISS_FILE = "vector_index.faiss"
META_FILE  = "metadata.db"   # SQLite metadata store (disk-backed, low memory)
REQUIRED   = [FAISS_FILE, META_FILE]


def download():
    repo_id = os.environ.get("HF_REPO_ID", "").strip()

    # Local dev: files already exist, skip entirely
    if all(os.path.exists(f) for f in REQUIRED):
        print("[index] Index files already present — skipping download.")
        return

    if not repo_id:
        print("[index] ERROR: HF_REPO_ID env var not set and index files are missing.")
        print("[index]        Set HF_REPO_ID=<username>/dharmabot-index in Render env vars.")
        sys.exit(1)

    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("[index] ERROR: huggingface_hub not installed. Add it to requirements.txt.")
        sys.exit(1)

    hf_token = os.environ.get("HF_TOKEN") or None  # optional, needed for private repos

    for filename in REQUIRED:
        if os.path.exists(filename):
            size_mb = os.path.getsize(filename) / 1_048_576
            print(f"[index] ✓ {filename} already present ({size_mb:.1f} MB), skipping.")
            continue

        print(f"[index] ⬇  Downloading {filename} from {repo_id} ...")
        t0 = time.time()
        try:
            cached_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type="dataset",
                token=hf_token,
                local_dir=".",
                local_dir_use_symlinks=False,
            )
        except Exception as e:
            print(f"[index] ERROR downloading {filename}: {e}")
            sys.exit(1)

        elapsed = time.time() - t0
        size_mb = os.path.getsize(filename) / 1_048_576
        print(f"[index] ✓ {filename} ready ({size_mb:.1f} MB, {elapsed:.1f}s)")

    print("[index] All index files ready.")


if __name__ == "__main__":
    download()
