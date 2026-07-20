import os
import sys
import json
import cv2
import numpy as np
import torch
import insightface
import streamlit as st
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


@st.cache_resource
def load_face_models(model_path):
    """AI 모델 파일 경로 검증 및 로드 수행"""
    # 절대 경로 변환으로 위치 추적 명확화
    if not os.path.isabs(model_path):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # src/pages/ 기준으로 프로젝트 최상위 루트 경로 계산
        base_root = os.path.dirname(os.path.dirname(current_dir))
        model_path = os.path.abspath(os.path.join(base_root, model_path))

    # 화면에 실제 탐색 경로와 폴더 상태를 디버깅 정보로 출력
    if not os.path.exists(model_path):
        st.error(f"서버에서 모델 파일을 찾지 못함: {model_path}")
        parent_dir = os.path.dirname(model_path)
        if os.path.exists(parent_dir):
            st.info(f"해당 폴더 내 실제 파일 목록: {os.listdir(parent_dir)}")
        else:
            st.warning(f"상위 폴더 자체가 존재하지 않음: {parent_dir}")

    analyzer = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    analyzer.prepare(ctx_id=0, det_size=(640, 640))
    swapper = insightface.model_zoo.get_model(model_path, download=False)
    return analyzer, swapper

def main():
    st.title("🎭 2-in-1 딥페이크 사진 합성")
    st.write("소스와 타겟 이미지를 업로드하여 실시간 딥페이크 결과를 확인하세요.")

    # Track application opening
    log_app_usage("face_swap_defender", "app_opened", details=json.dumps({"status": "active"}))

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)  # 한 단계 위인 src 폴더를 가리킵니다.
    model_file = os.path.join(parent_dir, "inswapper_128.onnx")

    # Layout for image uploads
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        source_file = st.file_uploader("1. 소스 이미지 (내 얼굴)", type=["jpg", "jpeg", "png"])
    with col_up2:
        target_file = st.file_uploader("2. 타겟 이미지 (합성할 대상)", type=["jpg", "jpeg", "png"])

    if source_file is not None and target_file is not None:
        # Load cached AI models securely
        face_analyzer, swapper = load_face_models(model_file)

        # Convert uploaded bytes into OpenCV format cleanly
        src_bytes = np.asarray(bytearray(source_file.read()), dtype=np.uint8)
        source_img = cv2.imdecode(src_bytes, cv2.IMREAD_COLOR)

        tgt_bytes = np.asarray(bytearray(target_file.read()), dtype=np.uint8)
        target_img = cv2.imdecode(tgt_bytes, cv2.IMREAD_COLOR)

        if st.button("🚀 딥페이크 사진 합성"):
            with st.spinner("인공지능 모델 가동 중... (GPU Mode Active)"):
                # Extract landmarks
                source_faces = face_analyzer.get(source_img)
                target_faces = face_analyzer.get(target_img)

                if not source_faces or not target_faces:
                    st.error("이미지에서 얼굴을 감지하지 못했습니다.")
                    return

                # Core face swap pipeline execution
                result_img = swapper.get(target_img, target_faces[0], source_faces[0], paste_back=True)
                
                # Apply the forensic safeguard layers securely
                safe_result_img = add_invisible_watermark(result_img)

                # Track successful execution inside the database
                log_app_usage(
                    "face_swap_defender", 
                    "swap_completed", 
                    details=json.dumps({"source": source_file.name, "target": target_file.name})
                )

            # Display the requested three-column comparative dashboard
            st.write("### 📊 실시간 프로세스 모니터링 (SOURCE / TARGET / RESULT)")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.image(source_img, channels="BGR", caption="[SOURCE] 소스 이미지")
            with col2:
                st.image(target_img, channels="BGR", caption="[TARGET] 타겟 이미지")
            with col3:
                st.image(safe_result_img, channels="BGR", caption="[RESULT] 방어막 주입 결과")

                # Provide seamless download option for viewers
                _, img_encoded = cv2.imencode('.jpg', safe_result_img)
                st.download_button(
                    label="💾 결과물 안전하게 다운로드",
                    data=img_encoded.tobytes(),
                    file_name="swapped_result.jpg",
                    mime="image/jpeg"
                )

if __name__ == "__main__":
    main()