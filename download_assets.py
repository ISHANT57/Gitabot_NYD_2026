import requests
import os

# Hugging Face URLs
urls = {
    "metadata.json": "https://huggingface.co/Ishant57/Gita-Vector-Index/resolve/main/metadata.json",
    "vector_index.faiss": "https://huggingface.co/Ishant57/Gita-Vector-Index/resolve/main/vector_index.faiss"
}

# Download each file if not already present
for filename, url in urls.items():
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"{filename} downloaded successfully!")
    else:
        print(f"{filename} already exists, skipping download.")
