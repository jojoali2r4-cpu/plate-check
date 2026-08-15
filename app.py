import streamlit as st
import pandas as pd

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

# قراءة اللوحات من ملف Excel
plates = []

if uploaded_file is not None:
    try:
        df = pd.read_excel(
            uploaded_file,
            sheet_name="بيانات"
        )

        if "اللوحه" not in df.columns:
            st.error("لم يتم العثور على عمود «اللوحه» في الملف.")
        else:
            plates = (
                df["اللوحه"]
                .dropna()
                .astype(str)
                .str.replace(" ", "", regex=False)
                .tolist()
            )

            st.success(f"تم تحميل {len(plates)} لوحة بنجاح.")

    except Exception as e:
        st.error(f"حدث خطأ أثناء قراءة الملف: {e}")

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

# نتائج المطابقة
st.subheader("📋 اللوحات المتطابقة")

if "matches" not in st.session_state:
    st.session_state.matches = []

if st.session_state.matches:
    st.table(st.session_state.matches)
else:
    st.info("لا توجد مطابقات حتى الآن.")
