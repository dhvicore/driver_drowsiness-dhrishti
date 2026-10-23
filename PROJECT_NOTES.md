# Drishti — Project Notes

*Real-time vigilance, powered by foresight.*
Driver drowsiness and distraction detection from a single webcam. All values are taken from the project code and `yawn.ipynb`.

---

## 1. Overview

| Item | Value |
|---|---|
| Input | Webcam, 1280 × 720, mirrored |
| Face landmarks | **478** per frame (MediaPipe Face Landmarker) |
| Speed | ~30 fps on a MacBook Air |
| Outputs | ALERT · FATIGUED · DROWSY · DISTRACTED · CRITICAL |
| Tools | Python, OpenCV, MediaPipe, YOLO11, TensorFlow, Flask, Next.js |

**Pipeline:** Camera → Face landmarks → Feature extraction → Temporal analysis → Risk scores → Driver status

---

## 2. Features extracted

| Feature | Measures | From |
|---|---|---|
| EAR (Eye Aspect Ratio) | Eye openness | 6 landmarks per eye |
| MAR (Mouth Aspect Ratio) | Mouth opening | 4 mouth landmarks |
| Pitch / Yaw | Head tilt / turn (°) | 6 landmarks + 3D face model |
| Phone | Phone in view | YOLO11, COCO class 67 |
| Blinks, long closures | Eye-closure events | EAR over time |
| PERCLOS | % time eyes closed (30 s) | EAR over time |
| Yawns | Confirmed yawn events | MAR over time |

**Formulas**

- **EAR** = (‖p₂ − p₆‖ + ‖p₃ − p₅‖) / (2 · ‖p₁ − p₄‖), averaged over both eyes
- **MAR** = ‖upper lip − lower lip‖ / ‖left corner − right corner‖
- **PERCLOS** = closed-eye frames ÷ total frames in the last 30 s

EAR, MAR, pitch and yaw are each smoothed over **7 frames**.

---

## 3. Drowsiness detection

### Thresholds

| Parameter | Value |
|---|---|
| Eye closed / reopened | EAR < **0.23** / > **0.27** |
| Blink | **0.08 – 0.65 s** |
| Long closure (microsleep) | **≥ 0.8 s** |
| Yawn start / end | MAR > **0.42** / < **0.28** |
| Minimum yawn duration | **0.65 s** |
| Memory windows | PERCLOS **30 s**, yawns **45 s**, long closures **30 s** |

### Evidence score (0–100, per frame)

| Signal | Points |
|---|---|
| Eyes closed now | ≥0.8 s **20** · ≥1.5 s **45** · ≥2 s **65** · ≥3 s **85** |
| PERCLOS | ≥20% **10** · ≥30% **18** · ≥40% **25** · ≥50% **30** |
| Recent yawns | 1 → **10** · 2 → **20** · ≥3 → **30** (+5 during a yawn) |
| Recent long closures | 1 → **8** · 2–3 → **18** · ≥4 → **25** |
| Combined signs | +**10** if eyes closed ≥0.8 s with ≥2 yawns or PERCLOS ≥35% |

The **drowsiness score** smooths the evidence score: it rises **20%** of the gap per frame and falls **8%**, so alerts appear quickly and clear gradually.

### Status

| Status | Condition |
|---|---|
| CRITICAL | Eyes closed ≥ **3 s**, or ≥ **2 s** with ≥2 recent yawns |
| DROWSY | Eyes closed ≥ **1.5 s**, or PERCLOS ≥ **45%** with ≥2 long closures, or score ≥ **55** with PERCLOS ≥35% / closure ≥0.8 s |
| FATIGUED | ≥2 recent yawns, or score ≥ **30** |
| ALERT | Otherwise |

---

## 4. Distraction detection

### Head pose (OpenCV solvePnP)

| Direction | Threshold | Distracted after |
|---|---|---|
| Left | yaw < **−25°** | 1.5 s |
| Right | yaw > **20°** | 1.5 s |
| Up | pitch < **−15°** | 1.5 s |
| Down | pitch > **20°** | **1.2 s** |

### Phone (YOLO11s)

| Parameter | Value |
|---|---|
| Confidence | **0.20** full frame, **0.16** in tiles |
| Tiles | **5** overlapping regions, to catch small phones |
| Stable detection | ≥ **3** of the last 10 checks |
| "Phone use" after | **1.0 s** continuous |
| Runs every | **8** frames |

### Distraction score (0–100)

| Signal | Points |
|---|---|
| Head left / right / up | ≥0.5 s **15** · ≥1 s **35** · ≥1.5 s **55** · ≥3 s **75** |
| Head down | ≥0.4 s **20** · ≥0.8 s **40** · ≥1.2 s **60** · ≥2.5 s **80** |
| Phone detected / in use | **+15** / **+35** |
| Phone in use + head down | **+40** |

### Final status

Checked in order: **CRITICAL** (critical drowsiness, or drowsy with distraction ≥ 60) → **DROWSY** → **DISTRACTED** (distraction ≥ 60, or phone use with head down) → **FATIGUED** → **DISTRACTED** (head away or phone use) → **ALERT**.

---

## 5. Yawn classifier (deep-learning experiment)

A CNN was trained and evaluated as an alternative to MAR. The real-time system uses MAR geometry because it is faster and needs no image cropping.

| Setting | Value |
|---|---|
| Model | MobileNetV2 (ImageNet, frozen) + GAP + Dropout 0.3 + Dense(1, sigmoid) |
| Input / batch | 224 × 224 / 32 |
| Optimiser | Adam, lr 0.001, binary cross-entropy, ≤15 epochs, early stopping |
| Data | **5,119** images: 3,582 train · 767 val · 770 test (70 / 15 / 15) |

| Test metric (770 images) | Value |
|---|---|
| **Accuracy** | **97.92%** |
| Precision (yawn) | 98.40% |
| Recall (yawn) | 97.37% |
| F1-score | 0.98 |

**Confusion matrix:** normal 384 correct / 6 wrong · yawn 370 correct / 10 wrong.

---

## 6. Web system

Flask backend (port 5001) streams video as MJPEG (~30 fps) and metrics as JSON; the Next.js dashboard (port 3000) refreshes every **250 ms**.

## 7. Limitations

Needs a visible, lit face · sunglasses block EAR · fixed thresholds (no per-driver calibration) · looking down can mimic eye closure · phone must be in view.
