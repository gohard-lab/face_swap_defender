import streamlit as st
import cv2
import numpy as np
import json
from tracker_hub import log_app_usage

# 스트림릿 페이지 기본 설정
st.set_page_config(page_title="Deepfake Watermark Detector", layout="wide")

def detect_frequency_watermark(image):
    """중저주파 영역(DCT)에 숨겨진 디지털 지문을 시각적으로 추출합니다."""
    ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y_channel, _, _ = cv2.split(ycrcb)
    
    y_float = y_channel.astype(np.float32)
    dct_coefficients = cv2.dct(y_float)
    
    # 주파수 에너지를 시각적으로 극대화하여 화려한 스펙트럼 맵으로 변환
    magnitude = np.abs(dct_coefficients)
    log_magnitude = np.log(magnitude + 1)
    visualized_fingerprint = cv2.normalize(log_magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    
    # 시각적 효과를 위해 컬러맵 적용 (시퍼런 배경에 데이터가 빛나는 연출)
    colormap_result = cv2.applyColorMap(visualized_fingerprint, cv2.COLORMAP_JET)
    return colormap_result

def main():
    st.title("🔍 딥페이크 방어막 탐지기 (Forensic Scanner)")
    st.write("인간의 눈에 보이지 않는 중저주파 영역의 디지털 지문을 스캔합니다.")

    # 앱 실행 시 수파베이스 트래커에 로그 기록
    log_app_usage("watermark_detector", "app_opened", details=json.dumps({"action": "Detector UI loaded"}))

    uploaded_file = st.file_uploader("검사할 이미지를 업로드하세요 (방어막이 적용된 깨끗한 사진)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 업로드된 파일을 오픈CV 형식으로 변환
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        st.write("### 🔬 분석 결과")
        col1, col2 = st.columns(2)

        with col1:
            st.image(image, channels="BGR", caption="입력된 이미지 (인간의 시야)")

        with col2:
            with st.spinner('주파수 도메인을 스캔하는 중...'):
                fingerprint_img = detect_frequency_watermark(image)
                st.image(fingerprint_img, channels="BGR", caption="추출된 주파수 지문 지도 (AI의 시야)")
                
                # 검사 성공 로그 기록
                log_app_usage("watermark_detector", "scan_completed", details=json.dumps({"status": "success", "file_name": uploaded_file.name}))

if __name__ == "__main__":
    main()