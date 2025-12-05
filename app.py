import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from docx import Document
from docx.shared import Pt
from io import BytesIO

# --- 1. 頁面基礎設定 ---
st.set_page_config(
    page_title="AI 會議全能秘書", 
    page_icon="📝",
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
    
    st.info("🤖 模型：gemini-2.0-flash-001\n📄 輸出：Word (.docx)")

if not api_key:
    st.warning("請先設定 Google API Key 才能開始使用。")
    st.stop()

# --- 3. 初始化 Google Gemini ---
try:
    genai.configure(api_key=api_key)
    MODEL_VERSION = 'gemini-2.0-flash-001'
    model = genai.GenerativeModel(MODEL_VERSION)
except Exception as e:
    st.error(f"模型初始化失敗: {e}")
    st.stop()

# --- 🛠️ 輔助函式：將文字轉換為 Word 檔 ---
def generate_docx(content):
    doc = Document()
    
    # 設定整份文件的基礎字型 (選用微軟正黑體或一般無襯線體會比較好看)
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Microsoft JhengHei'
    font.size = Pt(12)

    # 簡單的 Markdown 解析器，將文字轉為 Word 格式
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue # 跳過空行 (docx 會自動處理段落間距)
            
        if line.startswith('# '): # 主標題
            doc.add_heading(line.replace('# ', ''), level=0)
        elif line.startswith('## '): # 副標題
            doc.add_heading(line.replace('## ', ''), level=1)
        elif line.startswith('### '): # 小標題
            doc.add_heading(line.replace('### ', ''), level=2)
        elif line.startswith('* ') or line.startswith('- '): # 列點
            p = doc.add_paragraph(line.replace('* ', '').replace('- ', ''), style='List Bullet')
        else: # 一般內文
            doc.add_paragraph(line)
            
    # 將檔案存入記憶體
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 4. 主程式介面 ---
st.title("📝 AI 會議全能秘書")
st.caption(f"支援 MP3 上傳 | 自動逐字稿 | 匯出 Word 檔 | Powered by {MODEL_VERSION}")

# 建立分頁
tab1, tab2 = st.tabs(["🎙️ 現場錄音", "📂 上傳音檔 (MP3/M4A)"])

audio_source = None
source_name = ""

with tab1:
    mic_audio = st.audio_input("點擊麥克風開始錄音")
    if mic_audio:
        audio_source = mic_audio
        source_name = "mic_recording.wav"

with tab2:
    uploaded_file = st.file_uploader("拖或者是選擇音訊檔案", type=["mp3", "wav", "m4a", "aac"])
    if uploaded_file:
        st.audio(uploaded_file)
        audio_source = uploaded_file
        source_name = uploaded_file.name

# --- 5. 核心處理邏輯 ---
if audio_source:
    st.divider()
    st.write(f"✅ 已取得音訊來源，準備分析...")
    
    if st.button("🚀 開始分析並生成 Word 報告", type="primary"):
        
        # 處理檔案
        suffix = os.path.splitext(source_name)[1]
        if not suffix: suffix = ".wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(audio_source.getvalue())
            tmp_file_path = tmp_file.name

        try:
            with st.spinner(f"正在聽打與撰寫報告中 (Gemini 2.0)..."):
                
                # A. 上傳
                upload_file = genai.upload_file(path=tmp_file_path, mime_type=audio_source.type)
                
                # B. 設定 Prompt (針對 Word 輸出優化)
                prompt = """
                你是一位專業的台灣會議秘書。請仔細聆聽音訊，完成「逐字稿」與「會議紀要」。

                請依照以下規則輸出，以便轉換為 Word 文件：

                規則 1 (逐字稿格式)：
                - 務必區分講者，例如 [講者1]、[講者2]。
                - **重要：不同講者的發言之間，請務必換行分段 (空一行)，讓閱讀更清晰。**
                - 格式範例：
                  [講者1]：早安，我們開始會議吧。
                  
                  [講者2]：好的，沒問題。

                規則 2 (待辦事項格式)：
                - 請使用「列點清單」方式呈現待辦事項，**不要使用 Markdown 表格** (因為轉 Word 會跑版)。
                - 格式：- [負責人] 待辦事項 (期限)

                請輸出以下內容結構：

                # 會議全記錄

                ## Part 1: 會議紀要
                ### 🎯 會議主旨
                (內容)

                ### 🔑 關鍵決策
                (列點內容)

                ### ✅ 待辦事項
                (列點內容)

                ## Part 2: 完整逐字稿
                (在此處列出對話內容，請記得講者之間要分段)
                """
                
                # C. 生成
                response = model.generate_content([prompt, upload_file])
                
                # D. 顯示預覽 (Web 上還是顯示 Markdown)
                st.markdown("### 📄 報告預覽")
                st.markdown(response.text)
                
                # E. 轉換為 Word 並提供下載
                docx_file = generate_docx(response.text)
                
                st.download_button(
                    label="📥 下載 Word 報告 (.docx)",
                    data=docx_file,
                    file_name="meeting_minutes.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )

        except Exception as e:
            st.error(f"分析過程發生錯誤: {e}")
        
        finally:
            if os.path.exists(tmp_file_path):
                os.remove(tmp_file_path)
