# EmotionScope

Final project for **[CS50x 2026](https://cs50.harvard.edu/x/2026/)**, Harvard University's Introduction to Computer Science. The problem sets are in [CS50x-2026](https://github.com/pabloooduran/CS50x-2026).

> All code in this repository was written by me, following [CS50's academic honesty policy](https://cs50.harvard.edu/x/2026/honesty/).

**▶ [Live demo](https://pabloooduran--emotionscope-web.modal.run)**: register any username, upload a photo and see the detected faces and emotions.

> The demo runs on [Modal](https://modal.com) and sleeps when nobody is using it, so the first load can take up to a minute while the models load. After that, each image takes a couple of seconds. Accounts and uploads are reset periodically.

EmotionScope is a web-based facial expression analysis application that allows authenticated users to upload an image, detect faces, classify facial expressions, and visualize the results in an intuitive interface.

The system combines a custom-trained emotion classification model with a separate face detection stage, following a modular computer vision pipeline. This design improves robustness by separating **face detection** from **emotion classification**.

---

## Project Overview

EmotionScope is an end-to-end AI web application that integrates:

- Flask backend
- User authentication
- SQLite database
- Image upload and processing
- Face detection
- Emotion classification
- Styled frontend with modern UX

The goal of this project is to demonstrate how a machine learning model can be integrated into a complete product rather than remaining as a standalone experiment or notebook.

Unlike many academic implementations, this system is designed as a full pipeline including frontend, backend, and model inference.

---

## Main Features

- User registration and login
- Password hashing and password change functionality
- Session-based authentication
- Image upload (`png`, `jpg`, `jpeg`, `webp`)
- Face detection
- Emotion classification per detected face
- Confidence-based filtering of predictions
- “No face detected” fallback mechanism
- Annotated output image with bounding boxes
- Image preview before upload
- Loading animation during processing
- Clean and responsive UI

---

## System Architecture

```text
User
  ↓
Frontend (HTML/CSS/JS)
  ↓
Flask Backend
  ↓
Face Detection
  ↓
Face Cropping & Preprocessing
  ↓
Emotion Classification Model
  ↓
Annotated Output
  ↓
Rendered Result Page
```

The system is designed with a modular structure where each component has a clearly defined responsibility. This improves maintainability and allows individual components to be replaced or upgraded independently.

---

## Computer Vision Pipeline

```text
image
→ face detection
→ crop faces
→ grayscale + resize
→ emotion classification
→ confidence filtering
→ annotate image
→ return results
```

---

## Key Steps

### Face Detection
- Uses DeepFace with `mtcnn` backend
- Extracts bounding boxes

### Face Detection Gate
- If no face → skip classification
- Avoids meaningless predictions

### Preprocessing
- Grayscale conversion
- Resize to 64x64

### Classification
- Custom YOLO-based model

### Post-processing
- Confidence threshold
- Margin between top predictions

### Fallback
- Low confidence → `"uncertain"`

---

## Model Description

### Emotion Classes

- angry
- fear
- happy
- sad
- surprise
- neutral

### Removed Class

- `disgust` removed due to dataset imbalance

### Input

- Grayscale images
- Resolution: 64x64

### Confidence Filtering

```text
if top1_conf < 0.40 or margin < 0.15 → "uncertain"
```

---

## Dataset Preparation

Based on FER-2013 style dataset

### Issues

- Low resolution
- Class imbalance

### Fixes

- Removed `disgust`
- Balanced dataset (max ~3000 samples/class)
- Structured train/validation/test splits

---

## Authentication System

### Stack

- Flask
- flask_session
- SQLite
- cs50 SQL
- werkzeug.security

### Features

- Register
- Login
- Logout
- Change password

### Password Security

- Hashed using `generate_password_hash`
- Verified with `check_password_hash`

### Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);
```

---

## Project Structure

```text
project/
├── app.py
├── analyzer.py
├── emotion_model.pt
├── emotion_app.db
├── templates/
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── change_password.html
│   └── result.html
├── static/
│   ├── styles.css
│   ├── uploads/
│   └── results/
└── README.md
```

---

## Core Modules

### app.py

- Flask configuration
- Routing
- Authentication
- File handling
- Calls analyzer

### analyzer.py

- Face detection
- Preprocessing
- Model inference
- Confidence filtering
- Image annotation

### emotion_model.pt

- Custom trained emotion classifier

---

## Frontend

### Pages

- login.html
- register.html
- change_password.html
- index.html
- result.html

### UX Features

- Image preview before upload
- Loading overlay during processing
- Styled cards and navigation
- Responsive layout
- Navy/blue color scheme

---

## Security Considerations

### Implemented

- Password hashing
- Session authentication
- File validation
- Max upload size
- Image validation
- Security headers

### Not implemented

- CSRF protection
- Rate limiting
- Account lockout
- Full production hardening

---

## Limitations

- Emotion recognition is inherently ambiguous
- Low-resolution training data FER-2013
- Similar emotions can be confused
- Real-world images differ from training data
- Domain mismatch (detector vs classifier)
- No temporal context
- Small or partial faces may not be detected

---

## Potential Improvements

### AI / Model

- Higher resolution datasets
- Better architectures
- Video support
- Add "unknown" class

### Product

- User history
- Dashboard
- Reports
- Batch processing

### Security

- CSRF tokens
- Rate limiting
- Logging

### UX

- Emotion color coding
- Animations

### AI API

- Use of an AI API for a detailed description of the emotions of each frame

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Database Setup

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL
);
```

---

## Run the App

```bash
python app.py
```

or

```bash
flask run --port=5000
```

---

## Example Workflow

1. User logs in
2. Uploads image
3. System detects faces
4. Faces are classified
5. Results are filtered
6. Annotated image is generated
7. Results are displayed

---

## Technical Notes

### Why separate detection and classification?

A classifier always outputs a class, even if no face is present.
Face detection prevents invalid predictions.

### Why use "uncertain"?

To avoid misleading results when the model is not confident.

### Why crop faces?

The model is trained on face regions, not full images.

### Why a custom model?

To demonstrate:

- training process
- data handling
- real ML integration

---

## Final Remarks

EmotionScope is a full-stack AI application demonstrating how a custom-trained model can be integrated into a real product.

### Key strengths

- Modular architecture
- Custom model integration
- Face detection gating
- Full-stack implementation
- Clean UI/UX
