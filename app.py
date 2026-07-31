import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from streamlit_mic_recorder import speech_to_text

st.set_page_config(page_title="فحص اللوحات", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .big-text { font-size: 26px !important; font-weight: bold; padding: 15px; border-radius: 10px; margin-bottom: 10px; }
    .success-box { background-color: #d4edda; color: #155724; }
    .danger-box { background-color: #f8d7da; color: #721c24; }
    .warning-box { background-color: #fff3cd; color: #856404; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 نظام فحص وإملاء اللوحات")
st.markdown("---")

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر العمود الذي فيه أرقام/أسماء اللوحات:", df.columns)
    existing_plates = df[column_name].astype(str).str.strip().tolist()
    
    st.success(f"تم تحميل الملف! عدد اللوحات: {len(existing_plates)}")
    st.markdown("---")

    st.subheader("🎤 الإملاء الصوتي:")
    spoken_text = speech_to_text(language='ar-SA', start_prompt="🔴 اضغط للبدء والتحدث", stop_prompt="🟩 اضغط لإيقاف التسجيل", key='speech')

    if 'current_text' not in st.session_state:
        st.session_state['current_text'] = ""

    if spoken_text:
        st.session_state['current_text'] = spoken_text

    input_plate = st.text_input("اللوحة المنطوقة (عدليها هنا إذا انكتبت غلط):", value=st.session_state['current_text'])

    if input_plate:
        input_cleaned = input_plate.strip()
        st.markdown(f'<div class="big-text warning-box">اللوحة الحالية: {input_cleaned}</div>', unsafe_allow_html=True)

        if input_cleaned in existing_plates:
            st.markdown(f'<div class="big-text danger-box">⚠️ تنبيه: اللوحة ({input_cleaned}) مكررة وموجودة بالملف!</div>', unsafe_allow_html=True)
        else:
            matches = process.extract(input_cleaned, existing_plates, scorer=fuzz.ratio, limit=3)
            high_similarity = [m for m in matches if m[1] >= 80]
            
            if high_similarity:
                st.markdown(f'<div class="big-text warning-box">⚠️ تنبيه: اللوحة غير متطابقة تماماً لكن يوجد شبيه بها:</div>', unsafe_allow_html=True)
                for m_text, score, _ in high_similarity:
                    st.write(f"- **{m_text}** (نسبة التشابه: {int(score)}%)")
            else:
                st.markdown(f'<div class="big-text success-box">✅ اللوحة ({input_cleaned}) جديدة وغير مكررة.</div>', unsafe_allow_html=True)
