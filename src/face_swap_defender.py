import os
import sys
import json
import cv2
import numpy as np
import torch
import insightface
from insightface.app import FaceAnalysis


# Integrated custom tracker for usage logging
from tracker_hub import log_app_usage # This is a custom module and needs to be provided by the user. It is commented out for now.

# ==========================================================
# 🔑 [Supabase Credentials Setup for Google Colab]
# ==========================================================
os.environ["SUPABASE_URL"] = "https://gkzbiacodysnrzbpvavm.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdremJpYWNvZHlzbnJ6YnB2YXZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1NzE2MTgsImV4cCI6MjA4OTE0NzYxOH0.Lv5uVeNZOyo21tgyl2jjGcESoLl_iQTJYp4jdCwuYDU"
# ==========================================================

# 🚨 [PATCH] Google Colab Environment Detection
# Google Colab runs on a Linux environment, so we bypass Windows DLL injection.
IS_COLAB = "google.colab" in sys.modules

if not IS_COLAB and sys.platform == "win32":
    try:
        # For local Windows environment, force recognize CUDA/cuDNN DLL paths inside virtualenv
        site_packages = next((p for p in sys.path if 'site-packages' in p), None)
        if site_packages:
            nvidia_dir = os.path.join(site_packages, "nvidia")
            if os.path.exists(nvidia_dir):
                for root, dirs, files in os.walk(nvidia_dir):
                    if os.path.basename(root) == "bin":
                        os.environ["PATH"] = root + os.path.pathsep + os.environ["PATH"]
                        os.add_dll_directory(root)
    except Exception:
        pass


def add_invisible_watermark(image, text="AI GENERATED - DO NOT TRUST"):
    """Inserts a subtle forensic watermark into the output image to track AI generation"""
    watermarked = image.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    overlay = image.copy()
    cv2.putText(overlay, text, (50, 50), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.1, watermarked, 0.9, 0, watermarked)
    return watermarked


def execute_face_swap(source_img_path, target_img_path, output_path, model_path):
    """Executes ultra-fast GPU-accelerated face swapping with safety watermarking"""
    print("[INFO] Loading Face Analysis AI Model...")

    # Track the initialization of the application
    log_app_usage(
        "face_swap_defender",
        "process_started",
        details=json.dumps({
            "source": os.path.basename(source_img_path),
            "target": os.path.basename(target_img_path)
        })
    )

    # Enable CUDA execution provider for ultra-fast GPU acceleration
    face_analyzer = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    face_analyzer.prepare(ctx_id=0, det_size=(640, 640))

    print("[INFO] Loading Face Swapper ONNX Model...")
    swapper = insightface.model_zoo.get_model(model_path, download=False)

    # Read media source files
    source_img = cv2.imread(source_img_path)
    target_img = cv2.imread(target_img_path)

    if source_img is None or target_img is None:
        error_msg = "Failed to read source or target images. Check file paths."
        print(f"[ERROR] {error_msg}")
        log_app_usage("face_swap_defender", "process_failed", details=json.dumps({"reason": error_msg}))
        return

    # Extract face embedded landmarks
    source_faces = face_analyzer.get(source_img)
    target_faces = face_analyzer.get(target_img)

    if not source_faces or not target_faces:
        error_msg = "No faces detected in the provided images."
        print(f"[ERROR] {error_msg}")
        log_app_usage("face_swap_defender", "process_failed", details=json.dumps({"reason": error_msg}))
        return

    source_face = source_faces[0]
    target_face = target_faces[0]

    print("[INFO] Performing Face Swap... (GPU Mode / CUDA Active)")
    result_img = swapper.get(target_img, target_face, source_face, paste_back=True)

    print("[INFO] Injecting Invisible Forensic Watermark...")
    safe_result_img = add_invisible_watermark(result_img)

    # Save secured image output
    cv2.imwrite(output_path, safe_result_img)
    print(f"[SUCCESS] Process completed successfully: {output_path}")

    # Track successful execution logs
    log_app_usage(
        "face_swap_defender",
        "process_completed",
        details=json.dumps({
            "status": "success",
            "output_file": os.path.basename(output_path)
        })
    )


if __name__ == "__main__":
    # Resolve root directory based on the running environment
    if IS_COLAB:
        current_dir = "/content"
        print("[INFO] Running on Google Colab environment.")
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct absolute paths for resources cleanly
    source_file = os.path.join(current_dir, "source.jpg")
    target_file = os.path.join(current_dir, "target.jpg")
    output_file = os.path.join(current_dir, "swapped_result.jpg")
    model_file = os.path.join(current_dir, "inswapper_128.onnx")

    # Trigger core pipeline
    execute_face_swap(source_file, target_file, output_file, model_file)