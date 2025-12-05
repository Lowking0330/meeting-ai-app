import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile

# --- 1. 設定頁面 ---
st.set_page_config(page_title="AI 會議秘書 (Gemini版)", page_icon="⚡")

# --- 2. 設定 API Key ---
# 嘗試從 Secrets 或環境變數讀取
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

# 側邊欄供手動輸入 (備用)
with st.sidebar:
    st.header("⚙️ 設定")
    if not api_key:
        api_key = st.text_input("輸入 Google Gemini API Key", type="password")
    st.info("💡 使用 Google Gemini 1.5 Flash 模型 (免費版)")

# --- 3. 初始化 Gemini ---
if not api_key:
    st.warning("請先設定 Google API Key 才能使用！")
    st.stop()

genai.configure(api_key=api_key)

# --- 🔍 自我診斷區塊 (新增) ---
# 這段程式會列出目前環境真正能用的所有模型，並印在側邊欄
with st.sidebar:
    st.markdown("### 🛠️ 模型診斷")
    try:
        available_models = [m.name for m in genai.list_models()]
        st.write("目前可用模型清單：")
        st.code(available_models)
        
        # 自動選擇一個可用的模型
        if "models/gemini-1.5-flash" in available_models:
            target_model = "gemini-1.5-flash"
            st.success("✅ 成功偵測到 Flash 模型")
        elif "models/gemini-1.5-flash-001" in available_models:
            target_model = "gemini-1.5-flash-001"
            st.success("✅ 使用 001 版本")
        else:
            target_model = "gemini-pro" # 萬一真的沒有，回退到舊版
            st.warning("⚠️ 找不到 Flash，暫時使用 gemini-pro")
            
    except Exception as e:
        st.error(f"無法取得模型清單: {e}")
        target_model = "gemini-1.5-flash" # 預設值

# ... (後面接原本的 st.title 和錄音功能，但在 model = ... 那行要改成下面這樣) ...

# 在後面使用模型時，請將原本的 model = ... 改成：
model = genai.GenerativeModel(target_model)
