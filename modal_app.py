"""Live demo of EmotionScope on Modal (https://modal.com).

Runs the same Flask app as `app.py`, with the original pipeline
(DeepFace/MTCNN face detection + the custom YOLO emotion classifier).

Deploy with:  modal deploy modal_app.py
"""

import modal

MODEL_ID = "1XpggsVjk2iuvx8bBA6qVLE6mkPTisHh4"  # emotion_model.pt on Google Drive
APP_DIR = "/root/app"

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("libgl1", "libglib2.0-0")
    # CPU-only PyTorch: smaller image, and avoids loading CUDA libraries next to TensorFlow
    .pip_install(
        "torch==2.14.1",
        "torchvision==0.29.1",
        index_url="https://download.pytorch.org/whl/cpu",
    )
    .pip_install(
        "cs50==9.5.0",
        "deepface==0.0.103",
        "Flask==3.1.3",
        "Flask-Session==0.8.0",
        "gdown==6.4.2",
        "mtcnn==1.0.0",
        "opencv-python==5.0.0.93",
        "pillow==13.0.0",
        "tensorflow==2.21.0",
        "tf-keras==2.21.0",
        "ultralytics==8.4.183",
        "Werkzeug==3.1.9",
    )
    .env({"TF_CPP_MIN_LOG_LEVEL": "3", "CUDA_VISIBLE_DEVICES": ""})
    .add_local_dir(
        ".",
        remote_path=APP_DIR,
        copy=True,
        ignore=[".git", ".github", "**/__pycache__", "flask_session", "static/uploads", "static/results", "*.ipynb", "notebooks"],
    )
    # Bake the model into the image so cold starts don't have to download it
    .run_commands(f"cd {APP_DIR} && gdown {MODEL_ID} -O emotion_model.pt")
)

app = modal.App("emotionscope", image=image)


@app.function(
    cpu=1.0,
    memory=4096,
    max_containers=1,  # one container: SQLite and filesystem sessions stay consistent
    scaledown_window=300,  # stay warm for 5 minutes after the last request
    timeout=120,
)
@modal.concurrent(max_inputs=8)
@modal.wsgi_app()
def web():
    import os
    import secrets
    import sys

    os.chdir(APP_DIR)
    sys.path.insert(0, APP_DIR)
    os.environ.setdefault("SECRET_KEY", secrets.token_hex(32))

    from app import app as flask_app

    return flask_app
