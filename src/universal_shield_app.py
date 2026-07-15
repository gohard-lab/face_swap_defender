# universal_face_swap_defender.py
import os
import json
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import streamlit as st
import insightface
from insightface.app import FaceAnalysis
from tracker_hub import log_app_usage

@st.cache_resource
def load_all_ai_brains(model_path):
    """Loads both the defense ensemble models and the target face swapper models into memory"""
    # 1. Load Ensemble Defense Networks
    brain_a = models.resnet18(pretrained=True)
    brain_b = models.mobilenet_v2(pretrained=True)
    brain_a.eval()
    brain_b.eval()
    
    # 2. Load Deepfake Face Swap Networks
    analyzer = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    analyzer.prepare(ctx_id=0, det_size=(640, 640))
    swapper = insightface.model_zoo.get_model(model_path, download=False)
    
    return brain_a, brain_b, analyzer, swapper

def generate_universal_ensemble_shield(model_a, model_b, img_bgr, epsilon=0.02):
    """Calculates a joint optimization gradient that disrupts multiple AI network architectures"""
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    input_tensor = transform(img_rgb).unsqueeze(0)
    input_tensor.requires_grad = True
    
    # Calculate cross-model collective gradient loss
    output_a = model_a(input_tensor)
    output_b = model_b(input_tensor)
    criterion = nn.MSELoss()
    loss = criterion(output_a, torch.zeros_like(output_a)) + criterion(output_b, torch.zeros_like(output_b))
    
    model_a.zero_grad()
    model_b.zero_grad()
    loss.backward()
    
    # Apply universal perturbation signs to paralyze AI frameworks
    sign_data_grad = input_tensor.grad.data.sign()
    perturbed_tensor = input_tensor + epsilon * sign_data_grad
    perturbed_tensor = torch.clamp(perturbed_tensor, 0, 1)
    
    perturbed_np = perturbed_tensor.squeeze(0).detach().cpu().numpy()
    perturbed_np = np.transpose(perturbed_np, (1, 2, 0))
    perturbed_final = (perturbed_np * 255).astype(np.uint8)
    
    return cv2.cvtColor(perturbed_final, cv2.COLOR_RGB2BGR)

def main():
    st.title("🎭 보편적 방어막 및 딥페이크 통합 검증 시스템")
    st.write("소스 이미지에 다중 AI 교란 방어막을 실시간 주입한 후, 즉시 딥페이크 합성 결과까지 검증합니다.")

    # Track application entry event into database
    log_app_usage(
        "universal_swap_integrated", 
        "app_opened", 
        details=json.dumps({"status": "ready", "mode": "all_in_one"})
    )

    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_file = os.path.join(current_dir, "inswapper_128.onnx")

    # Double upload columns layout
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        source_file = st.file_uploader("1. 소스 이미지 (내 얼굴)", type=["jpg", "jpeg", "png"])
    with col_up2:
        target_file = st.file_uploader("2. 타겟 이미지 (합성할 대상 몸)", type=["jpg", "jpeg", "png"])

    if source_file is not None and target_file is not None:
        # Load all heavyweight models cleanly using cache mechanics
        brain_a, brain_b, face_analyzer, swapper = load_all_ai_brains(model_file)

        src_bytes = np.asarray(bytearray(source_file.read()), dtype=np.uint8)
        source_img = cv2.imdecode(src_bytes, cv2.IMREAD_COLOR)

        tgt_bytes = np.asarray(bytearray(target_file.read()), dtype=np.uint8)
        target_img = cv2.imdecode(tgt_bytes, cv2.IMREAD_COLOR)

        if st.button("🚀 원클릭 방어막 주입 및 딥페이크 합성 가동"):
            log_app_usage(
                "universal_swap_integrated", 
                "pipeline_triggered", 
                details=json.dumps({"source": source_file.name, "target": target_file.name})
            )

            with st.spinner("1단계: 복수 AI 가중치 교집합 급소 추적 및 보편적 방어막 주입 중..."):
                # Step 1: Automatically inject optimization shield on the source face
                protected_source = generate_universal_ensemble_shield(brain_a, brain_b, source_img)

            with st.spinner("2단계: 방어막이 쳐진 사진으로 실시간 딥페이크 합성 연산 중..."):
                # Step 2: Extract landmarks and execute face swapping sequentially
                source_faces = face_analyzer.get(protected_source)
                target_faces = face_analyzer.get(target_img)

                if not source_faces or not target_faces:
                    st.error("이미지에서 특징점을 찾을 수 없습니다.")
                    return

                # Perform deepfake swap directly using the protected face asset
                result_img = swapper.get(target_img, target_faces[0], source_faces[0], paste_back=True)

            # Track successful processing pipelines
            log_app_usage("universal_swap_integrated", "pipeline_success", details=json.dumps({"result": "displayed"}))

            # Render the 3-column comparative dashboard requested by the user
            st.write("### 📊 원스톱 프로세스 모니터링 (SOURCE / TARGET / RESULT)")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.image(source_img, channels="BGR", caption="[SOURCE] 순수 원본 소스")
            with col2:
                st.image(target_img, channels="BGR", caption="[TARGET] 합성 대상 타겟")
            with col3:
                st.image(result_img, channels="BGR", caption="[RESULT] 최종 딥페이크 결과")

                # Provide seamless download asset
                _, img_encoded = cv2.imencode('.jpg', result_img)
                st.download_button(
                    label="💾 결과 이미지 저장",
                    data=img_encoded.tobytes(),
                    file_name="universal_swap_result.jpg",
                    mime="image/jpeg"
                )

if __name__ == "__main__":
    main()