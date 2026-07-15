import streamlit as st
import json
from tracker_hub import log_app_usage

# Set page configuration for the complete defense suite
st.set_page_config(
    page_title="Deepfake Defender Zone",
    page_icon="🛡️",
    layout="wide"
)

# Track the entry of a new viewer in the database
log_app_usage(
    "viewer_portal",
    "portal_opened",
    details=json.dumps({"user_type": "viewer", "status": "all_features_enabled"})
)

# Dashboard Title
st.title("🛡️ 잡학다식 개발자의 딥페이크 방어 시스템 종합 체험존")
st.write("---")

st.subheader("👋 환영합니다! 해킹과 방어의 세계에 오신 것을 환영합니다!")
st.markdown("""
이곳은 AI 기술을 활용해 나의 소중한 얼굴 정보를 안전하게 지키고, 이를 뚫으려는 공격 기술을 직접 눈으로 확인하는 실험실입니다.
**왼쪽 사이드바 메뉴**를 1단계부터 5단계까지 순서대로 클릭하며 흥미진진한 보안 실험을 체험해 보세요!
""")

st.write("---")

# Five-step interactive course guide
col1, col2 = st.columns(2)

with col1:
    st.info("### 1단계: 🛡️ 원본 사진 철통 방어")
    st.write("나의 소중한 사진에 미세한 노이즈와 디지털 지문을 심어 기본 방어막을 형성합니다.")

    st.warning("### 2단계: 🧼 방어막 세척 공격 테스트")
    st.write("공격자가 내 방어막을 무력화하기 위해 노이즈를 씻어내려는 필터링 공격을 시뮬레이션합니다.")

    st.error("### 3단계: 🧱 강력한 이중 방어막 설치")
    st.write("세척 공격조차 무력화하는 한 단계 진화한 강력한 특수 방어 시스템을 가동합니다.")

with col2:
    st.success("### 4단계: 🎭 초고속 AI 합성 시연")
    st.write("실제 딥페이크 합성 엔진을 돌려 방어막이 씌워진 사진이 어떻게 합성을 방해하는지 눈으로 확인합니다.")

    st.subheader("🔍 5단계: 보이지 않는 지문 탐지")
    st.write("우리 눈에는 보이지 않지만 사진 속에 깊게 각인된 특수 디지털 주파수 지문을 고속 탐지기로 스캔합니다.")