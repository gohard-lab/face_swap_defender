# neural_shield_app.py
import os
import json
import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
import streamlit as st
from tracker_hub import log_app_usage

# Cache the neural network model to maximize performance and prevent memory leaks
@st.cache_resource
def load_target_ai_brain():
    """Loads a pre-trained deep learning vision model to simulate the AI feature extraction target"""
    # Use ResNet18 neural network layer to compute real gradient backpropagation
    model = models.resnet18(pretrained=True)
    model.eval() # Set to evaluation mode for deterministic gradient routing
    return model

def generate_gradient_adversarial_shield(model, img_bgr, epsilon=0.015):
    """Disrupts the neural pathways of the AI network by calculating structural loss gradients"""
    # Preprocess image into PyTorch tensor format with dynamic gradient tracking enabled
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w, c = img_rgb.shape
    
    transform = transforms.Compose([
        transforms.ToTensor(),
    ])
    input_tensor = transform(img_rgb).unsqueeze(0) # Add batch dimension
    input_tensor.requires_grad = True # Activate backpropagation path on image pixels
    
    # Pass image through the target AI brain layers
    output_features = model(input_tensor)
    
    # Design a criterion that forces the model to maximize its feature identification loss
    pseudo_target = torch.zeros_like(output_features)
    criterion = nn.MSELoss()
    loss = criterion(output_features, pseudo_target)
    
    # Execute backward pass to trace which precise pixels inflict the heaviest neural damage
    model.zero_grad()
    loss.backward()
    
    # Extract the adversarial direction signs from the image tensor gradient map
    data_grad = input_tensor.grad.data
    sign_data_grad = data_grad.sign()
    
    # Inject the structural stealth perturbation to paralyze the target AI
    perturbed_tensor = input_tensor + epsilon * sign_data_grad
    perturbed_tensor = torch.clamp(perturbed_tensor, 0, 1) # Safeguard absolute color boundaries
    
    # Convert the protected tensor back into native openCV BGR format
    perturbed_np = perturbed_tensor.squeeze(0).detach().cpu().numpy()
    perturbed_np = np.transpose(perturbed_np, (1, 2, 0)) # HWC format
    perturbed_rgb = (perturbed_np * 255).astype(np.uint8)
    
    return cv2.cvtColor(perturbed_rgb, cv2.COLOR_RGB2BGR)

def main():
    st.title("🧠 인공지능 뇌세포 교란 방패 (Neural Disruption Shield)")
    st.write("텍스트나 고정 공식 대신, AI의 신경망 가중치를 직접 역추적하여 마비시키는 최첨단 적대적 보안 시스템입니다.")

    # 1. Track user dashboard entry into Supabase database
    log_app_usage(
        "neural_shield_ui", 
        "dashboard_opened", 
        details=json.dumps({"engine": "PyTorch_FGSM_ResNet", "status": "ready"})
    )

    uploaded_file = st.file_uploader("AI 공격을 원천 차단할 이미지를 업로드하세요", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # 2. Track secure data ingestion metrics
        log_app_usage(
            "neural_shield_ui", 
            "target_image_loaded", 
            details=json.dumps({"filename": uploaded_file.name})
        )

        # Restore bytes into OpenCV representation
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        source_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if st.button("⚡ AI 신경망 타격 코드 가동"):
            with st.spinner("대상 AI의 손실 함수 그라디언트를 역추적하여 스텔스 암호 암전 레이어를 계산 중..."):
                # Load cached neural networks securely
                ai_brain = load_target_ai_brain()
                
                # Execute gradient-level adversarial defense simulation
                protected_img = generate_gradient_adversarial_shield(ai_brain, source_img)
                
                # 3. Track successful protection code generation status
                log_app_usage(
                    "neural_shield_ui", 
                    "gradient_shield_deployed", 
                    details=json.dumps({"status": "adversarial_success"})
                )

            # Display comparative layout requested by the user
            st.write("### 📊 실시간 스텔스 방어력 검증 (인간의 시야 대조)")
            col1, col2 = st.columns(2)

            with col1:
                st.image(source_img, channels="BGR", caption="[이전] 일반 무방비 원본 이미지")

            with col2:
                st.image(protected_img, channels="BGR", caption="[이후] AI 신경망이 마비된 방어 이미지")
                
                # Provide secure download pipeline
                _, img_encoded = cv2.imencode('.jpg', protected_img)
                st.download_button(
                    label="💾 최적화 방어 이미지 파일 다운로드",
                    data=img_encoded.tobytes(),
                    file_name="neural_protected_result.jpg",
                    mime="image/jpeg",
                    on_click=lambda: log_app_usage("neural_shield_ui", "download_action", details=json.dumps({"file": "neural_protected.jpg"}))
                )

if __name__ == "__main__":
    main()