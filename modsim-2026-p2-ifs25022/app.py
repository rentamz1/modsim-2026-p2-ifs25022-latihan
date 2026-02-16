import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# ===============================
# CONFIG & STYLING
# ===============================
st.set_page_config(page_title="Pro Insights: Questionnaire", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# ===============================
# DATA PROCESSING ENGINE
# ===============================
def load_and_process(file_source):
    # Membaca data (bisa berupa path string atau file uploader)
    df = pd.read_excel(file_source)
    q_cols = [c for c in df.columns if str(c).startswith("Q")]
    
    # Mapping Likert
    mapping = {"SS": 5, "S": 4, "CS": 4, "N": 3, "TS": 2, "STS": 1}
    sentiment_map = {"SS": "Positif", "S": "Positif", "CS": "Positif", "N": "Netral", "TS": "Negatif", "STS": "Negatif"}
    
    # Create Numeric DF
    df_num = df[q_cols].replace(mapping).apply(pd.to_numeric, errors="coerce")
    return df, q_cols, df_num, sentiment_map

# ===============================
# FILE LOGIC (Otomatis vs Manual)
# ===============================
target_file = "data_kuesioner.xlsx"
data_to_load = None

# 1. Cek Sidebar Uploader Terlebih Dahulu
with st.sidebar:
    st.title("📂 Data Center")
    uploaded_file = st.file_uploader("Upload Excel Kuesioner Baru", type=["xlsx"])
    
    if uploaded_file:
        data_to_load = uploaded_file
        st.success("Menggunakan file yang diunggah.")
    elif os.path.exists(target_file):
        # 2. Jika tidak ada upload, cek apakah file lokal ada
        data_to_load = target_file
        st.info(f"Menggunakan file lokal: **{target_file}**")
    
    st.info("Pastikan kolom pertanyaan diawali dengan huruf 'Q' (contoh: Q1, Q2)")

# ===============================
# DASHBOARD EXECUTION
# ===============================
if data_to_load:
    df, question_cols, df_numeric, sentiment_map = load_and_process(data_to_load)
    
    if not question_cols:
        st.error("Format file salah! Tidak ditemukan kolom yang diawali dengan 'Q'.")
    else:
        # --- HEADER METRICS ---
        st.title("📊 Questionnaire Analytics Dashboard")
        col1, col2, col3 = st.columns(3)
        
        total_resp = len(df)
        total_q = len(question_cols)
        global_avg = df_numeric.mean().mean()

        col1.metric("Total Responden", f"{total_resp} Orang")
        col2.metric("Total Pertanyaan", f"{total_q} Butir")
        col3.metric("Rata-rata Skor Global", f"{global_avg:.2f} / 5.0")
        
        st.divider()

        # --- NAVIGATION TABS ---
        tab1, tab2, tab3 = st.tabs(["📌 Ringkasan Umum", "🔍 Detail Pertanyaan", "🎯 Analisis Sentimen"])

        with tab1:
            c1, c2 = st.columns([6, 4])
            all_data = df[question_cols].melt(var_name="Pertanyaan", value_name="Jawaban")
            with c1:
                st.subheader("Distribusi Jawaban")
                fig_bar = px.histogram(all_data, x="Jawaban", color="Jawaban", 
                                       category_orders={"Jawaban": ["SS", "S", "CS", "N", "TS", "STS"]},
                                       color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_bar, use_container_width=True)
            with c2:
                st.subheader("Proporsi (%)")
                fig_pie = px.pie(all_data, names="Jawaban", hole=0.5,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)

        with tab2:
            st.subheader("Skor Rata-rata per Pertanyaan")
            avg_series = df_numeric.mean().sort_values(ascending=True)
            fig_avg = px.bar(avg_series, orientation='h', 
                             labels={'value': 'Skor Rata-rata', 'index': 'Pertanyaan'},
                             color=avg_series.values, color_continuous_scale="RdYlGn")
            st.plotly_chart(fig_avg, use_container_width=True)
            
            st.divider()
            
            if len(question_cols) >= 3:
                st.subheader("Radar Profil Jawaban")
                categories = list(question_cols)
                values = df_numeric.mean().fillna(0).tolist()
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=values + [values[0]], 
                    theta=categories + [categories[0]], 
                    fill='toself', 
                    line_color='#1f77b4'
                ))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])))
                st.plotly_chart(fig_radar, use_container_width=True)

        with tab3:
            st.subheader("Kategorisasi Sentimen")
            sentiment_data = df[question_cols].stack().map(sentiment_map).reset_index()
            sentiment_data.columns = ['Index', 'Pertanyaan', 'Sentimen']
            
            sent_counts = sentiment_data['Sentimen'].value_counts().reset_index()
            sent_counts.columns = ['Sentimen', 'count']
            fig_sent_bar = px.bar(sent_counts, x='Sentimen', y='count', color='Sentimen',
                                  color_discrete_map={"Positif": "#2ecc71", "Netral": "#f1c40f", "Negatif": "#e74c3c"})
            st.plotly_chart(fig_sent_bar, use_container_width=True)

else:
    st.warning(f"File **{target_file}** tidak ditemukan di folder aplikasi. Silakan upload file secara manual di sidebar.")
    st.image("https://illustrations.popsy.co/gray/data-analysis.svg", width=400)