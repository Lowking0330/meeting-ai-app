import streamlit as st
import os
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from docx import Document
from docx.shared import Pt
from io import BytesIO

# --- 1. 頁面設定 ---
st.set_page_config(page_title="AI 超級會議秘書", page_icon="🚀", layout="wide") # 改成寬版面

# --- 2. API 設定 (同前) ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

with st.sidebar:
    st.header("⚙️ 設定")
    if not api_key:
        api_key = st.text_input("Google API Key", type="password")
    st.info("💡 功能升級：\n1. 自動繪製心智圖\n2. 撰寫跟進 Email\n3. Word 匯出")

if not api_key:
    st.warning("請設定 API Key")
    st.stop()

# --- 3. 初始化 Gemini ---
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.0-flash-001')

# --- 4. Word 轉檔函式 (同前) ---
def generate_docx(content):
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Microsoft JhengHei'
    style.font.size = Pt(12)
    
    for line in content.split('\n'):
        line = line.strip()
        if not line: continue
        if line.startswith('# '): doc.add_heading(line[2:], 0)
        elif line.startswith('## '): doc.add_heading(line[3:], 1)
        elif line.startswith('### '): doc.add_heading(line[4:], 2)
        elif line.startswith('- ') or line.startswith('* '): 
            doc.add_paragraph(line[2:], style='List Bullet')
        else: doc.add_paragraph(line)
            
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

# --- 5. 主介面 ---
st.title("🚀 AI 超級會議秘書")
st.caption("全能版：錄音/上傳 + 逐字稿 + Word + 心智圖 + Email 草稿")

col1, col2 = st.columns([1, 2]) # 左窄右寬

with col1:
    st.subheader("1. 輸入音訊")
    tab1, tab2 = st.tabs(["🎙️ 錄音", "📂 上傳"])
    audio_source = None
    source_name = ""
    
    with tab1:
        mic = st.audio_input("開始錄音")
        if mic: 
            audio_source = mic
            source_name = "rec.wav"
            
    with tab2:
        up = st.file_uploader("上傳 MP3/M4A", type=["mp3","wav","m4a"])
        if up: 
            audio_source = up
            source_name = up.name

# --- 6. 核心處理 ---
if audio_source:
    with col1:
        st.success("音訊就緒")
        start_btn = st.button("🚀 開始全能分析", type="primary")

    if start_btn:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(source_name)[1] or ".wav") as tmp:
            tmp.write(audio_source.getvalue())
            tmp_path = tmp.name

        try:
            with st.spinner("🧠 AI 正在大腦風暴中 (分析、畫圖、寫信)..."):
                # A. 上傳
                upload_file = genai.upload_file(tmp_path, mime_type=audio_source.type)
                
                # B. 超級 Prompt (一次做完所有事)
                prompt = """
                你是一位頂級會議秘書。請針對這段錄音完成以下任務。
                
                【輸出規則】
                請使用 XML 標籤將不同區塊分開，以便程式讀取。
                使用繁體中文 (台灣)。

                任務 1：<transcript>
                生成完整逐字稿，區分講者 (如 [講者1])，講者間需換行。
                </transcript>

                任務 2：<summary>
                會議紀要 Markdown 格式：
                # 會議紀錄
                ## 🎯 主旨
                ## 🔑 決策
                ## ✅ 待辦事項 (列點)
                </summary>

                任務 3：<mindmap>
                請生成 Mermaid.js 的心智圖語法 (graph TD)。
                不需包含 ```mermaid 標籤，只要語法內容。
                結構要包含：會議主題 -> 關鍵議題 -> 細項。
                </mindmap>

                任務 4：<email>
                撰寫一封給「所有與會者」的跟進 Email 草稿。
                語氣專業、友善，包含感謝語與待辦事項總結。
                </email>
                """
                
                response = model.generate_content([prompt, upload_file])
                text = response.text
                
                # C. 解析內容 (簡單的字串切割)
                # 這裡用簡單的 split 處理，實際產品可用 Regex
                def extract_tag(content, tag):
                    try:
                        return content.split(f"<{tag}>")[1].split(f"</{tag}>")[0].strip()
                    except:
                        return ""

                transcript = extract_tag(text, "transcript")
                summary = extract_tag(text, "summary")
                mindmap_code = extract_tag(text, "mindmap")
                email_draft = extract_tag(text, "email")

                # D. 顯示結果 (右側欄位)
                with col2:
                    st.divider()
                    
                    # 分頁顯示不同視角
                    res_tab1, res_tab2, res_tab3, res_tab4 = st.tabs(["📊 心智圖", "📝 正式報告", "✉️ Email 草稿", "💬 逐字稿"])
                    
                    with res_tab1:
                        st.subheader("會議結構可視化")
                        if mindmap_code:
                            # 清理一下可能殘留的 markdown 標籤
                            mindmap_code = mindmap_code.replace("```mermaid", "").replace("```", "")
                            st.mermaid(mindmap_code)
                        else:
                            st.warning("無法生成心智圖")

                    with res_tab2:
                        st.subheader("會議紀要")
                        st.markdown(summary)
                        # 合併摘要與逐字稿供下載
                        full_doc = summary + "\n\n---\n\n" + transcript
                        docx = generate_docx(full_doc)
                        st.download_button("📥 下載 Word 報告", docx, "minutes.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

                    with res_tab3:
                        st.subheader("跟進郵件草稿")
                        st.text_area("您可以直接複製以下內容：", email_draft, height=300)

                    with res_tab4:
                        st.subheader("完整對話")
                        st.text_area("逐字稿", transcript, height=400)

        except Exception as e:
            st.error(f"錯誤: {e}")
        finally:
            if os.path.exists(tmp_path): os.remove(tmp_path)
