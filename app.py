import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from streamlit_mic_recorder import speech_to_text

st.set_page_config(page_title="فحص اللوحات", layout="wide")

st.markdown("""
    <style>
    body, div, h1, h2, h3, p { text-align: right; direction: rtl; }
    .status-box { font-size: 32px !important; font-weight: bold; text-align: center; padding: 25px; border-radius: 15px; margin-top: 15px; }
    .found-box { background-color: #f8d7da; color: #721c24; border: 3px solid #f5c6cb; }
    .not-found-box { background-color: #d4edda; color: #155724; border: 3px solid #c3e6cb; }
    </style>
""", unsafe_allow_html=True)

st.title("📋 فحص اللوحات السريع")
st.markdown("---")

uploaded_file = st.file_uploader("اختر ملف الإكسيل (Excel)", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    column_name = st.selectbox("اختر عمود اللوحات:", df.columns)
    
    # تنظيف وقراءة اللوحات
    existing_plates = df[column_name].astype(str).str.strip().tolist()
    
    st.success(f"تم تحميل الملف! عدد اللوحات: {len(existing_plates)}")
    st.markdown("---")

    # خيار الإملاء الصوتي
    st.subheader("🎤 إملاء اللوحة:")
    spoken_text = speech_to_text(language='ar-SA', start_prompt="🔴 اضغط للبدء والتحدث", stop_prompt="🟩 إيقاف", key='speech')

    if 'current_text' not in st.session_state:
        st.session_state['current_text'] = ""

    if spoken_text:
        st.session_state['current_text'] = spoken_text

    # خانة النص (يمكن استخدام ميكروفون لوحة المفاتيح فيها للإملاء المتواصل السريع)
    input_plate = st.text_input("اللوحة المنطوقة (أو املاء مستمر عبر ميكروفون الكيبورد):", value=st.session_state['current_text'])

    if input_plate:
        input_cleaned = input_plate.strip()

        # الفحص المباشر
        if input_cleaned in existing_plates:
            # تشغيل اهتزاز وصوت تنبيه للجوال عند وجود اللوحة
            st.components.v1.html("""
                <script>
                    if ("vibrate" in navigator) {
                        navigator.vibrate([300, 100, 300]); // اهتزاز
                    }
                    var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    var osc = audioCtx.createOscillator();
                    osc.type = 'sine';
                    osc.frequency.setValueAtTime(880, audioCtx.currentTime);
                    osc.connect(audioCtx.destination);
                    osc.start();
                    osc.stop(audioCtx.currentTime + 0.3);
                </script>
            """, height=0)
            
            st.markdown(f'<div class="status-box found-box">⚠️ اللوحة ({input_cleaned}) : موجودة</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-box not-found-box">✅ اللوحة ({input_cleaned}) : غير موجودة</div>', unsafe_allow_html=True)
