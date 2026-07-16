import os
import json
import cv2
import numpy as np
import streamlit as st
from tracker_hub import log_app_usage

def apply_robust_optimized_defense(img, base_epsilon=0.02):
    """
    Applies a structure-aware adaptive adversarial perturbation 
    designed to survive image purification filters and JPEG compression.
    """
    # Convert to float32 normalized format for precision gradient math
    img_float = img.astype(np.float32) / 255.0

    # Extract structural edges where the AI models heavily extract feature embeddings
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    
    # [수정 완료] 오픈CV 전용 내장 함수를 사용하여 제곱근 연산 오류를 완벽하게 해결
    magnitude = cv2.magnitude(grad_x, grad_y)
    
    # Normalize edge magnitude to create an adaptive perceptual contrast mask
    edge_mask = cv2.normalize(magnitude, None, 0.0, 1.0, cv2.NORM_MINMAX)
    edge_mask = np.expand_dims(edge_mask, axis=2)

    # Generate high-frequency carrier wave that disrupts AI landmark networks
    h, w, c = img.shape
    x_coords, y_coords = np.meshgrid(np.arange(w), np.arange(h))
    carrier_wave = np.sin(x_coords * 0.5) * np.cos(y_coords * 0.5)
    carrier_wave = np.expand_dims(carrier_wave, axis=2)
    carrier_wave = np.repeat(carrier_wave, c, axis=2)

    # Adaptive noise allocation based on structural edges
    adaptive_noise = base_epsilon * carrier_wave * (1.0 + edge_mask * 2.0)
    
    # Apply perturbation and strictly clip boundaries
    protected_float = img_float + adaptive_noise
    protected_final = np.clip(protected_float, 0.0, 1.0)
    return (protected_final * 255.0).astype(np.uint8)

def main():
    st.title("🛡️ 궁극의 인공지능 방패 (Robust Shield Generator)")
    st.write("소셜 미디어 압축과 공격자의 세탁 필터를 견뎌내는 강인한 방어막을 생성합니다.")

    # 1. 화면 진입 흔적 데이터 트래킹
    log_app_usage(
        "face_swap_defender", 
        "page_opened", 
        details=json.dumps({"interface": "streamlit_robust", "status": "active"})
    )

    # 이미지 파일 업로더 구성
    uploaded_file = st.file_uploader("보호막을 장착할 원본 이미지(Source Image)를 선택하세요", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 2. 파일 업로드 흔적 데이터 트래킹
        log_app_usage(
            "face_swap_defender", 
            "file_uploaded", 
            details=json.dumps({"file_name": uploaded_file.name, "file_size": uploaded_file.size})
        )

        # 업로드된 파일 바이트를 오픈CV 형식으로 복원
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        source_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if st.button("🔒 초정밀 최적화 방어막 주입"):
            with st.spinner("AI 교란 주파수 뼈대를 구조적으로 최적화하는 중..."):
                # 강력한 적응형 방어막 함수 구동
                protected_img = apply_robust_optimized_defense(source_img)
                
                # 3. 방어막 생성 성공 데이터 트래킹
                log_app_usage(
                    "face_swap_defender", 
                    "defense_applied", 
                    details=json.dumps({"status": "success", "image_dimensions": f"{source_img.shape[1]}x{source_img.shape[0]}"})
                )

            # 시청자 시각 연출을 위한 전/후 사진 나란히 배치 (Before & After)
            st.write("### 📊 최적화 방어막 전/후 비교 시연")
            col1, col2 = st.columns(2)

            with col1:
                st.image(source_img, channels="BGR", caption="[이전] 무방비 원본 사진")

            with col2:
                st.image(protected_img, channels="BGR", caption="[이후] 강인한 최적화 방어 사진")
                
                # 결과물 안전 다운로드 기능 연동
                _, img_encoded = cv2.imencode('.jpg', protected_img)
                st.download_button(
                    label="💾 압축 저항성 방어 이미지 다운로드",
                    data=img_encoded.tobytes(),
                    file_name="robust_protected_source.jpg",
                    mime="image/jpeg",
                    on_click=lambda: log_app_usage("face_swap_defender", "download_clicked", details=json.dumps({"action": "download_robust_image"}))
                )

if __name__ == "__main__":
    main()