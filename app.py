import streamlit as st

st.set_page_config(
    page_title="نظام فحص لوحات السيارات",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 نظام فحص لوحات السيارات")
st.write("ارفعي ملف اللوحات ثم ابدئي التسجيل الصوتي.")

# رفع ملف Excel
uploaded_file = st.file_uploader(
    "📁 ارفعي ملف اللوحات",
    type=["xlsx", "xls"]
)

st.divider()

# أزرار التسجيل
col1, col2 = st.columns(2)

with col1:
    start_recording = st.button(
        "🎙️ بدء التسجيل",
        use_container_width=True
    )

with col2:
    stop_recording = st.button(
        "⏹️ إيقاف التسجيل",
        use_container_width=True
    )

st.divider()

st.subheader("📋 اللوحات المتطابقة")

if "matches" not in st.session_state:
    st.session_state.matches = []

if st.session_state.matches:
    st.table(st.session_state.matches)
else:
    st.info("لا توجد مطابقات حتى الآن.")
