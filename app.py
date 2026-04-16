import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import urllib3

# 隱藏跳過 SSL 檢查時產生的警告訊息
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 【防 404 終極絕招】讓程式自己去問 Google：「我的金鑰可以用哪一個模型？」
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    if not available_models:
        st.error("你的 API 金鑰目前沒有可用於生成內容的模型權限。請檢查 Google AI Studio 設定。")
        st.stop()
    
    # 優先選擇 flash，沒有的話就選 pro，再沒有就隨便挑清單裡第一個能用的
    chosen_model = available_models[0]
    for m in available_models:
        if "gemini-1.5-flash" in m:
            chosen_model = m
            break
        elif "gemini-pro" in m:
            chosen_model = m
            break
            
    model = genai.GenerativeModel(chosen_model)
except Exception as e:
    st.error(f"獲取模型清單失敗，請確認 API 金鑰是否正確。錯誤：{e}")
    st.stop()

ISSUE_TAGS = ['碳排', 'Fashion', 'Industry', '規範/法令', 'Announcement', 'E Environment', 'Climate', '碳權 / 費', '政治', 'S 社會', 'G Corporate Governance', 'CSR', 'ESG', 'Risk', 'Investment', 'Economics', 'Carbon']

st.title("⚡️ Notion 文章摘要自動生成器 (AI 自動尋路版)")
url = st.text_input("請貼上文章網址：")

@st.cache_data(show_spinner=False)
def process_article(article_url):
    # 戴上面具，突破網站防爬蟲機制
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 無敵星星：跳過安全憑證檢查 (解決 HBR 等網站的憑證阻擋)
    response = requests.get(article_url, headers=headers, timeout=15, verify=False)
    response.encoding = 'utf-8' 
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
        # 這裡會顯示程式最終到底成功召喚了哪一個模型
        with st.spinner(f'⚡️ 正在使用 {chosen_model.replace("models/", "")} 飆速分析中...'):
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
