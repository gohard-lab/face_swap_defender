import cv2
import numpy as np
import os
import json
import streamlit as st
from tracker_hub import log_app_usage

def process_attack_purification(img):
    """Simulates Facebook compression and advanced blurring to wash out noise"""
    # 1단계: 페이스북 화질 저하 및 압축 시뮬레이션
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 85]
    _, encoded_img = cv2.imencode('.jpg', img, encode_param)
    fb_compressed = cv2.imdecode(encoded_img, cv2.IMREAD_COLOR)

    # 2단계: 고주파 방어 노이즈를 지우기 위한 공간 필터링 결합
    smoothed = cv2.GaussianBlur(fb_compressed, (3, 3), 0)
    final_washed = cv2.bilateralFilter(smoothed, d=5, sigmaColor=75, sigmaSpace=75)
    return final_washed

def main():
    st.title("🥷 적대적 노이즈 세탁 시스템 (Attacker Purifier)")
    st.write("방어막이 쳐진 사진을 업로드하여 플랫폼 압축과 필터링 공격을 가합니다.")

    # 1. 화면 진입 로그를 데이터 트래커에 기록
    log_app_usage(
        "attacker_purifier_ui", 
        "page_opened", 
        details=json.dumps({"interface": "streamlit_hacker", "status": "ready"})
    )

    uploaded_file = st.file_uploader("공격할 방어막 이미지(Protected Image)를 선택하세요", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 파일 업로드 흔적 추적 로그
        log_app_usage(
            "attacker_purifier_ui", 
            "file_uploaded", 
            details=json.dumps({"file_name": uploaded_file.name})
        )

        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        protected_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        with st.spinner("플랫폼 압축 및 노이즈 무력화 공격 진행 중..."):
            # 무력화 필터 가동
            washed_img = process_attack_purification(protected_img)
            
            # 공격 성공 흔적 추적 로그
            log_app_usage(
                "attacker_purifier_ui", 
                "attack_completed", 
                details=json.dumps({"status": "bypass_success", "target": uploaded_file.name})
            )

        # 🔬 시청자 시각 연출을 위한 전/후 사진 나란히 배치 (Before & After)
        st.write("### 💥 방어막 무력화 전/후 비교 시연")
        col1, col2 = st.columns(2)

        with col1:
            st.image(protected_img, channels="BGR", caption="[이전] 스텔스 방어막이 살아있는 상태")

        with col2:
            st.image(washed_img, channels="BGR", caption="[이후] 압축 및 필터 공격으로 세탁된 상태")
            
            # 세탁된 이미지 다운로드 버튼 제공
            _, img_encoded = cv2.imencode('.jpg', washed_img)
            st.download_button(
                label="🔓 세탁된 이미지 다운로드",
                data=img_encoded.tobytes(),
                file_name="washed_hacked_result.jpg",
                mime="image/jpeg",
                on_click=lambda: log_app_usage("attacker_purifier_ui", "download_clicked", details=json.dumps({"action": "download_washed"}))
            )

if __name__ == "__main__":
    main()