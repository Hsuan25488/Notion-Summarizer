import streamlit as st
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from datetime import datetime
import urllib3
import re

# 基本設定
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# 自動挑選模型
try:
    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    chosen_model = next((m for m in available_models if "flash" in m), available_models[0])
    model = genai.GenerativeModel(chosen_model)
except Exception as e:
    st.error(f"模型初始化失敗：{e}"); st.stop()

# Notion 寫入函數
def add_to_notion(title, issues, keywords, url):
    headers = {
        "Authorization": f"Bearer {st.secrets['NOTION_TOKEN']}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    # 處理標籤格式
    issue_list = [i.strip() for i in re.split(r'[，,、]', issues.replace('[','').replace(']','')) if i.strip()]
    
    data = {
        "parent": { "database_id": st.secrets["DATABASE_ID"] },
        "properties": {
            "Title": { "title": [{ "text": { "content": title } }] },
            "Issue": { "multi_select": [{"name": i[:25]} for i in issue_list] }, # Notion 標籤長度限制
            "Keywords": { "rich_text": [{ "text": { "content": keywords } }] },
            "Files & media": { "url": url },
            "State": { "select": { "name": "Writing" } },
            "Created time": { "date": { "start": datetime.now().strftime("%Y-%m-%d") } }
        }
    }
    return requests.post("https://api.notion.com/v1/pages", headers=headers, json=data)

# UI 介面
st.title("⚡️ Notion 文章摘要助手 (穩定版)")
ISSUE_TAGS = ['碳排', '規範/法令', 'E Environment', 'Climate', '碳權 / 費', 'S 社會', 'G Corporate Governance', 'CSR', 'ESG', 'Risk', 'Investment']
url_input = st.text_input("🔗 請貼上文章網址：")

if st.button("🚀 開始分析並同步"):
    if url_input:
        with st.spinner('📡 處理中...'):
            try:
                # 爬取
                res = requests.get(url_input, headers={"User-Agent": "Mozilla/5.0"}, timeout=15, verify=False)
                res.encoding = 'utf-8'
                soup = BeautifulSoup(res.text, 'html.parser')
                content = soup.get_text(strip=True)[:2000]
                title = soup.title.string.split('|')[0].strip() if soup.title else "未命名文章"
                
                # AI 生成 (強化指令防止格式錯誤)
                prompt = f"請閱讀文章並精煉摘要。必須嚴格遵守以下格式回傳：\n標籤：[從 {ISSUE_TAGS} 挑選]\n摘要：[一句話]\n\n文章內容：{content}"
                ai_res = model.generate_content(prompt).text
                
                # 容錯解析法：用關鍵字抓取，不再死板地用行數分
                issue_match = re.search(r"標籤：(.*)", ai_res)
                keyword_match = re.search(r"摘要：(.*)", ai_res)
                
                issues = issue_match.group(1).strip() if issue_match else "未分類"
                keywords = keyword_match.group(1).strip() if keyword_match else ai_res[:100]

                st.info(f"📝 **預覽**：\n{keywords}")
                
                # 同步
                notion_res = add_to_notion(title, issues, keywords, url_input)
                if notion_res.status_code == 200:
                    st.success("✅ 已成功同步至 Notion！")
                    st.balloons()
                else:
                    st.error(f"❌ 同步失敗：{notion_res.text}")
                        
            except Exception as e:
                st.error(f"💥 發生錯誤：{e}")
    else:
        st.warning("⚠️ 請輸入網址")
