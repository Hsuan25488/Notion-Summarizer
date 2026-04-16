import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime

# 【修復 503 錯誤】強制使用 REST 通道，解決 Streamlit 雲端連線問題
genai.configure(api_key=st.secrets["GEMINI_API_KEY"], transport="rest")
model = genai.GenerativeModel('gemini-1.5-flash')

ISSUE_TAGS = ['碳排', 'Fashion', 'Industry', '規範/法令', 'Announcement', 'E Environment', 'Climate', '碳權 / 費', '政治', 'S 社會', 'G Corporate Governance', 'CSR', 'ESG', 'Risk', 'Investment', 'Economics', 'Carbon']

st.title("⚡️ Notion 摘要生成器+ ")
url = st.text_input("請貼上文章網址：")

@st.cache_data(show_spinner=False)
def process_article(article_url):
    # 【突破防爬蟲】戴上 User-Agent 面具，偽裝成正常的 Chrome 瀏覽器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 加上 headers 發送請求，並設定 15 秒超時限制
    response = requests.get(article_url, headers=headers, timeout=15)
    response.encoding = 'utf-8' # 確保中文不會變成亂碼
    
    soup = BeautifulSoup(response.text, 'html.parser')
    text_content = soup.get_text(strip=True)[:2500] 
    title = soup.title.string if soup.title else "未命名文章"
    
    prompt = f"""
    任務：
    1. 用一句話精煉總結以下文章。
    2. 從清單 {ISSUE_TAGS} 選出最符合的1個或多個標籤。
    
    內文：{text_content}
    
    嚴格輸出格式：
    標籤：[標籤]
    摘要：[一句話]
    """
    
    ai_response = model.generate_content(prompt).text
    lines = ai_response.strip().split('\n')
    issues = lines[0].replace('標籤：', '').strip()
    keywords = lines[1].replace('摘要：', '').strip()
    
    return title, issues, keywords

if st.button("開始處理"):
    if url:
        with st.spinner('⚡️ 飆速爬取與分析中...'):
            try:
                title, issues, keywords = process_article(url)
                current_time = datetime.now().strftime("%Y-%m-%d")
                
                markdown_table = f"""
| State | Issue | Keywords | Title | Link what | Last edited time | Files & media | Created time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Writing | {issues} | {keywords} | {title} |  | {current_time} | {url} | {current_time} |
                """
                
                st.success("處理完成！請複製下方表格：")
                st.code(markdown_table, language="markdown")
                
            except Exception as e:
                st.error(f"處理失敗。錯誤訊息：{e}")
    else:
        st.warning("請先輸入網址！")    ai_response = model.generate_content(prompt).text
    lines = ai_response.strip().split('\n')
    issues = lines[0].replace('標籤：', '').strip()
    keywords = lines[1].replace('摘要：', '').strip()
    
    return title, issues, keywords

if st.button("開始處理"):
    if url:
        with st.spinner('⚡️ 飆速爬取與分析中...'):
            try:
                title, issues, keywords = process_article(url)
                current_time = datetime.now().strftime("%Y-%m-%d")
                
                markdown_table = f"""
| State | Issue | Keywords | Title | Link what | Last edited time | Files & media | Created time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Writing | {issues} | {keywords} | {title} |  | {current_time} | {url} | {current_time} |
                """
                
                st.success("處理完成！請複製下方表格：")
                st.code(markdown_table, language="markdown")
                
            except Exception as e:
                st.error(f"處理失敗。錯誤訊息：{e}")
    else:
        st.warning("請先輸入網址！")
