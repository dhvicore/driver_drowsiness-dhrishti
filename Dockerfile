FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 GRADIO_ANALYTICS_ENABLED=False MPLCONFIGDIR=/tmp/matplotlib YOLO_CONFIG_DIR=/tmp/ultralytics
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY web/requirements.txt /app/web/requirements.txt
RUN pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu && pip install -r web/requirements.txt
COPY temporal_engine.py head_pose.py phone_detector.py face_landmarker.task yolo11s.pt /app/
COPY web/app.py web/features.py /app/web/
EXPOSE 7860
CMD ["python", "web/app.py"]
