import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

ISSUE_TAGS = ['碳排', 'Fashion', 'Industry', '規範/法令', 'Announcement', 'E Environment', 'Climate', '碳權 / 費', '政治', 'S 社會', 'G Corporate Governance', 'CSR', 'ESG', 'Risk', 'Investment', 'Economics', 'Carbon']

st.title("Notion 文章摘要自動生成器")
url = st.text_input("請貼上文章網址：")

if st.button("開始處理"):
    if url:
        with st.spinner('正在爬取文章並交由 AI 分析中...'):
            try:
                response = requests.get(url, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                text_content = soup.get_text(strip=True)[:5000]
                title = soup.title.string if soup.title else "未命名文章"
                
                prompt = f"""
                請閱讀以下文章內容，並執行：
                1. 寫出一句話的文章摘要。
                2. 從以下標籤清單中選出最符合的標籤（可複選），若都不符合請建議一個新標籤：{ISSUE_TAGS}。
                
                文章內容：
                {text_content}
                
                請嚴格依據以下格式輸出，不要包含其他廢話：
                標籤：[填入標籤]
                摘要：[填入一句話摘要]
                """
                
                ai_response = model.generate_content(prompt).text
                
                lines = ai_response.strip().split('\n')
                issues = lines[0].replace('標籤：', '').strip()
                keywords = lines[1].replace('摘要：', '').strip()
                
                current_time = datetime.now().strftime("%Y-%m-%d")
                
                markdown_table = f"""
| State | Issue | Keywords | Title | Link what | Last edited time | Files & media | Created time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Writing | {issues} | {keywords} | {title} |  | {current_time} | {url} | {current_time} |
                """
                
                st.success("處理完成！請複製下方表格：")
                st.code(markdown_table, language="markdown")
                
            except Exception as e:
                st.error(f"處理失敗，可能是網站阻擋爬蟲。錯誤訊息：{e}")
    else:
        st.warning("請先輸入網址！")
