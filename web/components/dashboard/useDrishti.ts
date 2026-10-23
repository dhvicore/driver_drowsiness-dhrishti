"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { API, getState, post, type Snapshot } from "@/lib/drishti";

const IDLE: Snapshot = {
  running: false,
  error: null,
  fps: 0,
  raw_overlay: false,
  duration: 0,
  metrics: {
    face: false,
    status: "STANDBY",
    severity: 0,
    attention: "—",
    eye_state: "—",
    ear: 0,
    mar: 0,
    closed_duration: 0,
    blinks: 0,
    perclos: 0,
    yawn: false,
    yawn_count: 0,
    recent_yawns: 0,
    recent_long_closures: 0,
    evidence_score: 0,
    drowsiness_score: 0,
    drowsiness_status: "—",
    head_direction: "—",
    pitch: 0,
    yaw: 0,
    head_duration: 0,
    head_distracted: false,
    distraction_score: 0,
    phone_detected: false,
    phone_using: false,
    phone_confidence: 0,
    phone_duration: 0,
    phone_source: "NONE",
  },
  totals: { yawns: 0, long_closures: 0, blinks: 0, phone_events: 0 },
  events: [],
};

export function useDrishti() {
  const camera = useRef<MediaStream | null>(null);
  const upload = useRef<AbortController | null>(null);
  const releaseCamera = useCallback(() => {
    upload.current?.abort();
    camera.current?.getTracks().forEach((track) => track.stop());
    camera.current = null;
  }, []);
  useEffect(() => releaseCamera, [releaseCamera]);
  const [snapshot, setSnapshot] = useState<Snapshot>(IDLE);
  const [online, setOnline] = useState<boolean | null>(null);
  const [pending, setPending] = useState(false);
  const [streamKey, setStreamKey] = useState(0);
  const controller = useRef<AbortController | null>(null);

  useEffect(() => {
    let active = true;

    async function poll() {
      controller.current?.abort();
      controller.current = new AbortController();
      try {
        const next = await getState(controller.current.signal);
        if (!active) return;
        setSnapshot(next);
        setOnline(true);
      } catch {
        if (active) setOnline(false);
      }
    }

    poll();
    const id = setInterval(poll, 250);
    return () => {
      active = false;
      clearInterval(id);
      controller.current?.abort();
    };
  }, []);

  const start = useCallback(async () => {
    setPending(true);
    try {
      releaseCamera();
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera access needs HTTPS or localhost. Open the forwarded Codespaces port in your browser.");
      }
      const media = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 360 } }, audio: false,
      });
      camera.current = media;
      const video = document.createElement("video");
      video.srcObject = media;
      video.muted = true;
      video.playsInline = true;
      await video.play();
      const res = await post("/api/start", { source: "browser" });
      if (res.ok) {
        const abort = new AbortController();
        upload.current = abort;
        const canvas = document.createElement("canvas");
        canvas.width = 640;
        canvas.height = 360;
        const context = canvas.getContext("2d")!;
        async function sendFrames() {
          try {
            while (!abort.signal.aborted) {
              context.drawImage(video, 0, 0, canvas.width, canvas.height);
              const jpeg = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.75));
              if (jpeg && !abort.signal.aborted) {
                const response = await fetch(`${API}/api/frame`, {
                  method: "POST", body: jpeg, signal: abort.signal,
                  headers: { "Content-Type": "image/jpeg" },
                });
                if (!response.ok) throw new Error("Camera upload failed. Stop and restart monitoring.");
              }
              await new Promise((resolve) => setTimeout(resolve, 100));
            }
          } catch (error) {
            if (!abort.signal.aborted) {
              releaseCamera();
              setSnapshot((s) => ({ ...s, running: false, error: error instanceof Error ? error.message : "Camera upload failed" }));
              void post("/api/stop").catch(() => {});
            }
          }
        }
        void sendFrames();
        setStreamKey((k) => k + 1);
        setSnapshot((s) => ({ ...s, running: true, error: null }));
      } else {
        releaseCamera();
        setSnapshot((s) => ({ ...s, error: res.error ?? "Could not start" }));
      }
    } catch (error) {
      releaseCamera();
      setSnapshot((s) => ({ ...s, error: error instanceof Error ? error.message : "Could not start monitoring" }));
    } finally {
      setPending(false);
    }
  }, [releaseCamera]);

  const stop = useCallback(async () => {
    releaseCamera();
    setPending(true);
    try {
      await post("/api/stop");
      setSnapshot((s) => ({ ...s, running: false }));
    } catch {
      setOnline(false);
    } finally {
      setPending(false);
    }
  }, [releaseCamera]);

  const setOverlay = useCallback(async (enabled: boolean) => {
    setSnapshot((s) => ({ ...s, raw_overlay: enabled }));
    await post("/api/overlay", { enabled });
  }, []);

  return { snapshot, online, pending, streamKey, start, stop, setOverlay };
}
