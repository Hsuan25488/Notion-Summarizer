import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 【修復 429 關鍵】優先尋找 Flash 快捷通道
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    
    # 優先級排序：Flash 最新版 > Flash 1.5 > Pro
    chosen_model = None
    priority_keywords = ["flash-3.1", "flash-1.5", "flash", "gemini-pro"]
    
    for keyword in priority_keywords:
        for m in available_models:
            if keyword in m:
                chosen_model = m
                break
        if chosen_model:
            break
            
    if not chosen_model:
        chosen_model = available_models[0]
        
    model = genai.GenerativeModel(chosen_model)
except Exception as e:
    st.error(f"獲取模型清單失敗：{e}")
    st.stop()

ISSUE_TAGS = ['碳排', 'Fashion', 'Industry', '規範/法令', 'Announcement', 'E Environment', 'Climate', '碳權 / 費', '政治', 'S 社會', 'G Corporate Governance', 'CSR', 'ESG', 'Risk', 'Investment', 'Economics', 'Carbon']

st.title("⚡️ Notion 文章摘要自動生成器 (Flash 快捷版)")
url = st.text_input("請貼上文章網址：")

@st.cache_data(show_spinner=False)
def process_article(article_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(article_url, headers=headers, timeout=15, verify=False)
    response.encoding = 'utf-8' 
    soup = BeautifulSoup(response.text, 'html.parser')
    text_content = soup.get_text(strip=True)[:2500] 
    title = soup.title.string if soup.title else "未命名文章"
    
    prompt = f"請閱讀以下文章並精煉出一句話摘要，並從標籤 {ISSUE_TAGS} 中選出符合的。格式：標籤：[標籤] 摘要：[一句話]。內文：{text_content}"
    
    ai_response = model.generate_content(prompt).text
    lines = ai_response.strip().split('\n')
    issues = lines[0].replace('標籤：', '').strip()
    keywords = lines[1].replace('摘要：', '').strip()
    return title, issues, keywords

if st.button("開始處理"):
    if url:
        # 顯示當前使用的模型，確保它不再去擠 3.1 Pro 的窄門
        with st.spinner(f'🚀 使用 {chosen_model.replace("models/", "")} 飆速處理中...'):
            try:
                title, issues, keywords = process_article(url)
                current_time = datetime.now().strftime("%Y-%m-%d")
                markdown_table = f"| State | Issue | Keywords | Title | Link what | Last edited time | Files & media | Created time |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n| Writing | {issues} | {keywords} | {title} | | {current_time} | {url} | {current_time} |"
                st.success("成功！請複製下方表格至 Notion：")
                st.code(markdown_table, language="markdown")
            except Exception as e:
                st.error(f"處理失敗：{e}")
    else:
        st.warning("請先輸入網址！")
