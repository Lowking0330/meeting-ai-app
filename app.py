import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile

# --- 1. 設定頁面 ---
st.set_page_config(page_title="AI 會議秘書 (Gemini 2.0)", page_icon="⚡")

# --- 2. 設定 API Key ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

with st.sidebar:
    st.header("⚙️ 設定")
    if not api_key:
        api_key = st.text_input("輸入 Google Gemini API Key", type="password")
    st.info("💡 目前使用模型：Gemini 2.0 Flash (最新版)")

# --- 3. 初始化 ---
if not api_key:
    st.warning("請先設定 Google API Key 才能使用！")
    st.stop()

try:
    genai.configure(api_key=api_key)
except Exception as e:
    st.error(f"API Key 設定錯誤: {e}")
    st.stop()

# --- 4. 主畫面邏輯 ---
st.title("⚡ AI 會議記錄神器")
st.caption("Powered by Google Gemini 2.0 Flash | 繁體中文優化")

# 錄音介面
audio_value = st.audio_input("點擊下方麥克風開始錄製會議")

if audio_value:
    st.success("錄音完成！AI 正在聽取並整理內容...")
    
    # 建立臨時檔案
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(audio_value.getvalue())
        tmp_file_path = tmp_file.name

    try:
        with st.spinner("🚀 正在上傳音訊並生成摘要 (Gemini 2.0 處理中)..."):
            
            # A. 上傳檔案
            video_file = genai.upload_file(path=tmp_file_path, mime_type="audio/wav")
            
            # B. 設定模型 (使用您清單中有的 2.0 Flash)
            model = genai.GenerativeModel('gemini-2.0-flash')
            
            # C. 設定提示詞
            prompt = """
            你是一位專業的台灣會議秘書。請仔細聆聽這段會議錄音，並用「繁體中文 (台灣)」撰寫會議紀要。
            
            請依照以下結構輸出 Markdown 格式：
            
            ## 📅 會議紀要
            
            ### 🎯 會議主旨
            (一句話總結這場會議在討論什麼)
            
            ### 🔑 關鍵決策
            * (列出達成的共識)
            
            ### 📝 詳細摘要
            (分點說明討論內容，去除贅字，語氣需專業)
            
            ### ✅ 待辦事項 (Action Items)
            | 負責人 | 待辦事項 | 期限 |
            | :--- | :--- | :--- |
            | (若無提到人名則留空) | (具體事項) | (若無提到時間則留空) |
            """
            
            # D. 發送請求
            response = model.generate_content([prompt, video_file])
            
            # 顯示結果
            st.markdown(response.text)
            
            # 提供下載
            st.download_button(
                label="📥 下載會議紀錄",
                data=response.text,
                file_name="meeting_minutes.md",
                mime="text/markdown"
            )

    except Exception as e:
        st.error(f"發生錯誤: {e}")
        
    finally:
        if os.path.exists(tmp_file_path):
            os.remove(tmp_file_path)
