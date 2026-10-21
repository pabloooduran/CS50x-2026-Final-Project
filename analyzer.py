import os
import cv2
import tempfile
import gdown
from ultralytics import YOLO
from deepface import DeepFace

MODEL_PATH = "emotion_model.pt"
MODEL_ID = "1XpggsVjk2iuvx8bBA6qVLE6mkPTisHh4"

if not os.path.exists(MODEL_PATH) or os.path.getsize(MODEL_PATH) < 1_000_000:
    print("Downloading emotion model...")
    url = f"https://drive.google.com/uc?id={MODEL_ID}"
    gdown.download(url, MODEL_PATH, quiet=False)

emotion_model = YOLO(MODEL_PATH)

def analyze_image(img_path, output_path):
    img = cv2.imread(img_path)
    detections = []

    try:
        faces = DeepFace.extract_faces(
            img_path=img_path,
            detector_backend="mtcnn",
            enforce_detection=True,   # clave
            align=True
        )
    except ValueError:
        faces = []

    if len(faces) == 0:
        cv2.putText(
            img,
            "No face detected",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2
        )
        cv2.imwrite(output_path, img)
        return detections

    for i, face_obj in enumerate(faces, start=1):
        area = face_obj["facial_area"]
        x, y, w, h = area["x"], area["y"], area["w"], area["h"]

        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(img.shape[1], x + w)
        y2 = min(img.shape[0], y + h)

        face = img[y1:y2, x1:x2]
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        gray = cv2.resize(gray, (64, 64))

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_path = tmp.name
            cv2.imwrite(temp_path, gray)

        r = emotion_model.predict(temp_path, imgsz=64, verbose=False)[0]

        probs = r.probs.data.tolist()
        top1_idx = r.probs.top1
        top1_conf = float(r.probs.top1conf)
        top1_label = r.names[top1_idx]

        sorted_probs = sorted(probs, reverse=True)
        margin = sorted_probs[0] - sorted_probs[1]
        if top1_conf < 0.40 or margin < 0.15:
            label = "uncertain"
        else:
            label = top1_label
        detections.append({
            "face_id": i,
            "emotion": label,
            "confidence": round(top1_conf, 2),
            "box": [x1, y1, x2, y2]
        })

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(
            img,
            f"{label} {top1_conf:.2f}",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2
        )

        os.remove(temp_path)

    cv2.imwrite(output_path, img)
    return detections
