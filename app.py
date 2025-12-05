import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# --- 設定頁面 ---
st.set_page_config(page_title="AI 會議秘書 (手機版)", page_icon="🎙️")

# --- 側邊欄：設定 API Key ---
with st.sidebar:
    st.header("🔐 設定")
    # 嘗試從環境變數讀取，若無則讓使用者輸入
    load_dotenv()
    env_key = os.getenv("OPENAI_API_KEY")
    
    api_key = st.text_input("輸入 OpenAI API Key", value=env_key if env_key else "", type="password")
    
    st.info("💡 電腦端啟動後，請確認手機連上同一個 WiFi，並輸入 Network URL。")

# --- 主畫面 ---
st.title("🎙️ AI 會議記錄神器")
st.caption("繁體中文優化 | 語音轉文字 | 重點摘要")

# --- 檢查 API Key ---
if not api_key:
    st.warning("請先在側邊欄輸入 OpenAI API Key 才能開始！")
    st.stop()

client = OpenAI(api_key=api_key)

# --- 錄音區塊 ---
st.markdown("### 1. 錄製會議")
# 這是 Streamlit 新版功能，手機瀏覽器可直接呼叫麥克風
audio_value = st.audio_input("按下方紅色麥克風按鈕開始/停止")

if audio_value:
    st.success("錄音完成，開始 AI 分析...")
    
    # 建立兩個分頁：摘要結果 / 原始逐字稿
    tab1, tab2 = st.tabs(["📝 會議紀要 (AI)", "💬 原始逐字稿"])

    try:
        # --- 階段 1: Whisper 聽打 ---
        with st.spinner("🎧 正在將語音轉為文字 (Whisper)..."):
            audio_value.name = "input.wav"
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_value,
                language="zh",
                prompt="This is a business meeting in Taiwan. Please transcribe in Traditional Chinese."
            )
            raw_text = transcript.text

        # 顯示逐字稿
        with tab2:
            st.text_area("逐字稿內容", raw_text, height=300)

        # --- 階段 2: GPT-4o 摘要 ---
        with tab1:
            if not raw_text:
                st.error("無法辨識出語音內容，請重試。")
            else:
                with st.spinner("🧠 正在生成結構化筆記 (GPT-4o)..."):
                    system_prompt = """
                    你是一位專業的台灣會議記錄秘書。請閱讀下方的逐字稿，產出一份專業的會議紀要。
                    
                    【處理規則】
                    1. **用語修正**：將大陸用語轉為台灣習慣（例：視頻->影片、質量->品質、項目->專案）。
                    2. **格式要求**：
                       - 🎯 會議目的
                       - 🔑 關鍵決策 (列點)
                       - ✅ 待辦事項 (誰/做什麼/何時)
                    3. **去除廢話**：刪除贅字與重複語句。
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": raw_text}
                        ],
                        temperature=0.3
                    )
                    summary = response.choices[0].message.content
                
                # 顯示漂亮的 Markdown 結果
                st.markdown(summary)
                
                # 下載按鈕
                st.download_button(
                    label="📥 下載會議紀錄",
                    data=summary,
                    file_name="meeting_minutes.md",
                    mime="text/markdown"
                )

    except Exception as e:

        st.error(f"發生錯誤: {e}")
