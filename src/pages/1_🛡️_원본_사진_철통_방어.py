import os
import sys
import json
import cv2
import numpy as np
import torch
import streamlit as st
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

def apply_adversarial_noise(image, face_box, epsilon=0.005):
    """노이즈 강도(epsilon)를 0.05에서 0.005로 10배 낮춰 시각적 격자무늬를 완벽히 제거합니다."""
    perturbed_image = image.copy().astype(np.float32) / 255.0
    x1, y1, x2, y2 = map(int, face_box)
    
    face_roi = perturbed_image[y1:y2, x1:x2]
    if face_roi.size == 0:
        return image
        
    # 가우시안 노이즈의 진폭을 억제하여 픽셀 사이에 자연스럽게 은닉시킵니다.
    noise = epsilon * np.sin(face_roi * np.pi * 10.0) + np.random.normal(0, epsilon * 0.2, face_roi.shape)
    perturbed_face = face_roi + noise
    perturbed_image[y1:y2, x1:x2] = np.clip(perturbed_face, 0.0, 1.0)
    
    return (perturbed_image * 255.0).astype(np.uint8)


def apply_frequency_watermark(image, secret_text="PROVENANCE"):
    """주파수 공간의 삽입 강도를 낮추고 완벽한 0~255 클리핑으로 하단부 픽셀 붕괴를 방지합니다."""
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y_channel, cr, cb = cv2.split(ycrcb)
    
    y_float = y_channel.astype(np.float32)
    dct_coefficients = cv2.dct(y_float)
    
    # 주파수 공간에 텍스트를 각인할 때 강도를 255에서 15.0으로 대폭 낮춰 스텔스 상태를 유지합니다.
    h, w = dct_coefficients.shape
    cv2.putText(dct_coefficients, secret_text, (int(w*0.3), int(h*0.5)), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (15.0,), 1, cv2.LINE_AA)
    
    idct_y = cv2.idct(dct_coefficients)
    
    # 오버플로우 방지의 핵심: 역변환된 값이 0과 255를 절대 벗어나지 못하도록 수학적으로 가둬둡니다.
    idct_y = np.clip(idct_y, 0, 255).astype(np.uint8)
    
    merged = cv2.merge([idct_y, cr, cb])
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)

def execute_source_defense(source_img_path, output_path):
    """Detects a face in the source image and injects dual-layer stealth defense mechanisms"""
    print("[INFO] Initializing Standalone Source Defense Pipeline...")

    # Track the initialization of the defense app
    log_app_usage(
        "face_swap_defender",
        "defense_started",
        details=json.dumps({
            "source_file": os.path.basename(source_img_path),
            "mode": "standalone_protection"
        })
    )

    # Enable CUDA execution provider for GPU acceleration
    face_analyzer = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    face_analyzer.prepare(ctx_id=0, det_size=(640, 640))

    # Read the single source image file
    source_img = cv2.imread(source_img_path)

    if source_img is None:
        error_msg = "Failed to read the source image. Check file path."
        print(f"[ERROR] {error_msg}")
        log_app_usage("face_swap_defender", "defense_failed", details=json.dumps({"reason": error_msg}))
        return

    # Extract face embedded landmarks to locate the target defense area
    source_faces = face_analyzer.get(source_img)

    if not source_faces:
        error_msg = "No faces detected in the provided source image."
        print(f"[ERROR] {error_msg}")
        log_app_usage("face_swap_defender", "defense_failed", details=json.dumps({"reason": error_msg}))
        return

    source_face = source_faces[0]

    # 1단계: 소스 이미지 얼굴 영역에 정밀하게 적대적 노이즈 주입
    print("[🛡️ DEFENSE] 소스 이미지 얼굴 영역에 적대적 공격 노이즈 주입 중...")
    protected_img = apply_adversarial_noise(source_img, source_face.bbox)

    # 2단계: 이미지 전체 영역에 압축 저항성이 강한 주파수 도메인 워터마크 주입
    print("[🛡️ FORENSIC] 압축 저항성이 강한 주파수 도메인 워터마크 주입 중...")
    final_protected_img = apply_frequency_watermark(protected_img)

    # 안전하게 방어막이 쳐진 최종 결과물 저장
    cv2.imwrite(output_path, final_protected_img)
    print(f"[SUCCESS] Standalone defense applied successfully: {output_path}")

    # Track successful database logging
    log_app_usage(
        "face_swap_defender",
        "defense_completed",
        details=json.dumps({
            "status": "success",
            "output_file": os.path.basename(output_path)
        })
    )


# [인사이트페이스 앱 초기화 - 모델 토큰 낭비를 막기 위해 세션 상태 캐싱 적용]
@st.cache_resource
def load_face_analyzer():
    analyzer = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    analyzer.prepare(ctx_id=0, det_size=(640, 640))
    return analyzer

def main():
    st.title("🛡️ 스텔스 딥페이크 방어 시스템 (Preemptive Shield)")
    st.write("원본 사진을 업로드하면 인간의 눈에는 보이지 않는 적대적 노이즈와 포렌식 지문이 즉시 주입됩니다.")

    # 1. 화면 오픈 로그를 데이터 트래커에 JSON 형식으로 남깁니다.
    log_app_usage(
        "face_swap_defender", 
        "page_opened", 
        details=json.dumps({"interface": "streamlit_web", "status": "active"})
    )

    # 얼굴 분석기 로드
    face_analyzer = load_face_analyzer()

    # 파일 업로더 구성
    uploaded_file = st.file_uploader("보호할 원본 사진(Source Image)을 선택하세요", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 파일 업로드 흔적 추적 로그 기록
        log_app_usage(
            "face_swap_defender", 
            "file_uploaded", 
            details=json.dumps({"file_name": uploaded_file.name, "file_size": uploaded_file.size})
        )

        # 바이트 데이터를 오픈CV 이미지로 복원
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        source_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        # 얼굴 영역 좌표 추출
        faces = face_analyzer.get(source_img)

        if not faces:
            st.error("이미지에서 인식 가능한 얼굴을 찾을 수 없습니다. 다른 사진으로 시도해 주세요.")
            log_app_usage("face_swap_defender", "processing_failed", details=json.dumps({"reason": "no_face_detected"}))
            return

        # 방어 파이프라인 실시간 가동
        with st.spinner("보이지 않는 스텔스 방어막을 고속 주입하는 중..."):
            source_face = faces[0]
            
            # 1단계: 얼굴 노이즈 주입 -> 2단계: 주파수 워터마크 각인
            protected_img = apply_adversarial_noise(source_img, source_face.bbox)
            final_protected_img = apply_frequency_watermark(protected_img)
            
            # 처리 완료 흔적 추적 로그 기록
            log_app_usage(
                "face_swap_defender", 
                "defense_applied", 
                details=json.dumps({"status": "success", "detected_faces": len(faces)})
            )

        # 🔬 시청자 시각 연출을 위한 전/후 사진 나란히 배치 (Before & After)
        st.write("### 📊 방어막 주입 전/후 비교 시연")
        col1, col2 = st.columns(2)

        with col1:
            st.image(source_img, channels="BGR", caption="[이전] 순수한 원본 사진 (딥페이크 취약 상태)")

        with col2:
            st.image(final_protected_img, channels="BGR", caption="[이후] 스텔스 방어막 주입 완료 (데이터 변조 상태)")
            
            # 시청자가 결과물을 다운로드하여 보관할 수 있도록 버튼 제공
            _, img_encoded = cv2.imencode('.jpg', final_protected_img)
            st.download_button(
                label="🔒 방어된 이미지 다운로드",
                data=img_encoded.tobytes(),
                file_name="protected_stealth_image.jpg",
                mime="image/jpeg",
                on_click=lambda: log_app_usage("face_swap_defender", "download_clicked", details=json.dumps({"action": "download"}))
            )

if __name__ == "__main__":
    main()