"""
Uploads the locally-built FAISS vector index and metadata to a HuggingFace
dataset repo, so Render (via download_index.py) can pull the CORRECT index at
startup.

Run this whenever you rebuild the index (e.g. after changing the corpus or the
embedding model), so production stays in sync with your local index.

Usage:
    # Reads HF_REPO_ID and HF_TOKEN from the environment / .env
    python upload_index.py

    # Or override the repo on the command line:
    python upload_index.py <username>/<dataset-name>

Requirements:
    - HF_TOKEN  : a HuggingFace token with WRITE access (https://huggingface.co/settings/tokens)
    - HF_REPO_ID: target dataset repo, e.g. "Ishant57/dharmabot-index"
                  (must match the HF_REPO_ID configured on Render)
"""
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

FILES = ["vector_index.faiss", "metadata.json"]


def main():
    repo_id = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("HF_REPO_ID", "")).strip()
    token = (os.environ.get("HF_TOKEN") or "").strip()

    if not repo_id:
        print("[upload] ERROR: no repo specified. Set HF_REPO_ID in .env or pass it as an argument:")
        print("[upload]        python upload_index.py <username>/<dataset-name>")
        sys.exit(1)

    if not token:
        print("[upload] ERROR: HF_TOKEN not set. Create a WRITE token at")
        print("[upload]        https://huggingface.co/settings/tokens and add it to .env as HF_TOKEN=...")
        sys.exit(1)

    # Confirm the files exist locally before we start
    missing = [f for f in FILES if not os.path.exists(f)]
    if missing:
        print(f"[upload] ERROR: missing local index files: {', '.join(missing)}")
        print("[upload]        Build the index first (initialize the database), then re-run.")
        sys.exit(1)

    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        print("[upload] ERROR: huggingface_hub not installed. Run: pip install huggingface_hub")
        sys.exit(1)

    api = HfApi(token=token)

    # Create the dataset repo if it doesn't already exist (no-op if it does)
    print(f"[upload] Ensuring dataset repo '{repo_id}' exists ...")
    create_repo(repo_id=repo_id, repo_type="dataset", token=token, exist_ok=True)

    for filename in FILES:
        size_mb = os.path.getsize(filename) / 1_048_576
        print(f"[upload] Uploading {filename} ({size_mb:.1f} MB) to {repo_id} ...")
        t0 = time.time()
        api.upload_file(
            path_or_fileobj=filename,
            path_in_repo=filename,
            repo_id=repo_id,
            repo_type="dataset",
            commit_message=f"Update {filename}",
        )
        print(f"[upload] OK {filename} uploaded ({time.time() - t0:.1f}s)")

    print(f"[upload] All index files uploaded to https://huggingface.co/datasets/{repo_id}")
    print("[upload] Render will now download this index on its next deploy/restart.")


if __name__ == "__main__":
    main()
