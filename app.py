import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="AI 會議全能秘書", 
    page_icon="🤖",
    layout="centered"
)

# --- 2. 設定與驗證 API Key ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

# 側邊欄狀態
with st.sidebar:
    st.header("⚙️ 系統設定")
    if not api_key:
        api_key = st.text_input("請輸入 Google API Key", type="password")
    else:
        st.success("✅ API Key 已載入")
    
    st.info("🤖 模型：gemini-2.0-flash-001\n✨ 功能：錄音/上傳 + 逐字稿")

if not api_key:
    st.warning("請先設定 Google API Key 才能開始使用。")
    st.stop()

# --- 3. 初始化 Google Gemini ---
try:
    genai.configure(api_key=api_key)
    MODEL_VERSION = 'gemini-2.0-flash-001' # 鎖定這個穩定版本
    model = genai.GenerativeModel(MODEL_VERSION)
except Exception as e:
    st.error(f"模型初始化失敗: {e}")
    st.stop()

# --- 4. 主程式介面 ---
st.title("🤖 AI 會議全能秘書")
st.caption(f"支援 MP3 上傳 | 自動逐字稿 | 會議摘要 | Powered by {MODEL_VERSION}")

# 建立分頁 (Tabs) 來切換功能
tab1, tab2 = st.tabs(["🎙️ 現場錄音", "📂 上傳音檔 (MP3/M4A)"])

# 變數初始化
audio_source = None # 存放音訊資料
source_name = ""    # 識別來源名稱

# --- Tab 1: 現場錄音 ---
with tab1:
    mic_audio = st.audio_input("點擊麥克風開始錄音")
    if mic_audio:
        audio_source = mic_audio
        source_name = "mic_recording.wav"

# --- Tab 2: 上傳檔案 ---
with tab2:
    uploaded_file = st.file_uploader("拖或者是選擇音訊檔案", type=["mp3", "wav", "m4a", "aac"])
    if uploaded_file:
        st.audio(uploaded_file) # 顯示播放器確認
        audio_source = uploaded_file
        source_name = uploaded_file.name

# --- 5. 核心處理邏輯 ---
if audio_source:
    st.divider()
    st.write(f"✅ 已取得音訊來源，準備分析...")
    
    if st.button("🚀 開始 AI 分析 (生成摘要 + 逐字稿)", type="primary"):
        
        # 建立暫存檔 (Gemini 需要實體檔案)
        # 根據來源檔名判斷副檔名 (預設 .wav)
        suffix = os.path.splitext(source_name)[1]
        if not suffix: suffix = ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_source.getvalue())
            tmp_file_path = tmp_file.name

        try:
            with st.spinner(f"正在傳送音訊並進行深度分析 (Gemini 2.0)..."):
                
                # A. 上傳檔案
                upload_file = genai.upload_file(path=tmp_file_path, mime_type=audio_source.type)
                
                # B. 設定更強大的 Prompt (要求逐字稿)
                prompt = """
                你是一位專業的台灣會議秘書。請仔細聆聽這段音訊，並完成以下兩項任務：

                任務一：【完整逐字稿】
                請盡可能精確地將對話轉錄為文字。
                - 如果能辨識不同說話者，請用 [講者1]、[講者2] 標示。
                - 使用繁體中文 (台灣)。

                任務二：【會議紀要】
                根據逐字稿內容，整理出結構化的會議紀錄。

                請嚴格依照以下 Markdown 格式輸出 (不要省略任何部分)：

                # 📝 會議全記錄

                ## Part 1: 💬 完整逐字稿
                (在此處列出完整的對話內容...)

                ---

                ## Part 2: 📅 會議紀要

                ### 🎯 會議主旨
                (一句話總結)

                ### 🔑 關鍵決策
                * (列點說明)

                ### ✅ 待辦事項 (Action Items)
                | 負責人 | 待辦事項 | 期限 |
                | :--- | :--- | :--- |
                | ... | ... | ... |
                """
                
                # C. 生成內容
                response = model.generate_content([prompt, upload_file])
                
                # D. 顯示結果
                st.markdown(response.text)
                
                # E. 下載按鈕 (下載包含逐字稿+摘要的完整檔案)
                st.download_button(
                    label="📥 下載完整會議記錄 (.md)",
                    data=response.text,
                    file_name="meeting_full_record.md",
                    mime="text/markdown"
                )

        except Exception as e:
            st.error(f"分析過程發生錯誤: {e}")
        
        finally:
            # 清理暫存
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
