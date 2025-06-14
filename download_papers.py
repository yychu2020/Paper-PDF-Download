import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from habanero import Crossref
from googletrans import Translator

# 设置保存路径
SAVE_FOLDER = "D:/BaiduSyncdisk/参考文献"
os.makedirs(SAVE_FOLDER, exist_ok=True)

# 获取文章元数据
def get_metadata(doi):
    cr = Crossref()
    metadata = cr.works(ids=doi)
    item = metadata['message']

    year = item['issued']['date-parts'][0][0]
    first_author = item['author'][0]['family']
    journal = item['short-container-title'][0] if item['short-container-title'] else item['container-title'][0]
    title_en = item['title'][0]
    return year, first_author, journal, title_en

# 翻译英文标题为中文
def translate_title(title_en):
    translator = Translator()
    try:
        translated = translator.translate(title_en, src='en', dest='zh-cn')
        return translated.text
    except:
        return title_en  # 翻译失败则保留英文

# 清理非法文件名字符
def sanitize_filename(s):
    return re.sub(r'[\\/*?:"<>|]', '', s)

# 下载 PDF 文件
def download_pdf(pdf_url, filename):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(pdf_url, headers=headers, timeout=20)
        if 'pdf' not in r.headers.get('Content-Type', ''):
            print(f"⚠️ 不是 PDF 文件：{pdf_url}")
            return False
        save_path = os.path.join(SAVE_FOLDER, filename)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        print(f"✅ 已保存：{save_path}")
        return True
    except Exception as e:
        print(f"❌ 下载失败：{pdf_url}，错误：{e}")
        return False

# 从页面中提取 DOI 或 PDF 链接
def extract_doi_and_pdf(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # 尝试提取 DOI
    doi_match = re.search(r'10.\d{4,9}/[-._;()/:A-Z0-9]+', html, re.IGNORECASE)
    doi = doi_match.group(0) if doi_match else None

    # 尝试提取 PDF 链接
    pdf_url = None
    for a in soup.find_all('a', href=True):
        href = a['href']
        if ".pdf" in href.lower():
            pdf_url = urljoin(base_url, href)
            break

    return doi, pdf_url

# 主处理函数
def process_article_page(url):
    print(f"\n📘 正在处理页面：{url}")
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        html = response.text
        base_url = response.url  # 最终跳转后页面

        doi, pdf_url = extract_doi_and_pdf(html, base_url)

        if not doi:
            print("❌ 未提取到 DOI，无法获取元数据。跳过。")
            return

        # 获取元数据
        year, first_author, journal, title_en = get_metadata(doi)
        title_zh = translate_title(title_en)
        clean_title = sanitize_filename(title_zh)

        filename = f"{year}{first_author}-{journal}-{clean_title}.pdf"

        if not pdf_url:
            print("⚠️ 未找到 PDF 链接，无法下载")
            return

        download_pdf(pdf_url, filename)

    except Exception as e:
        print(f"❌ 页面处理失败：{e}")

# 主入口
if __name__ == "__main__":
    input_urls = [
        "https://www.nature.com/articles/s41524-025-01675-6",
     #   "https://www.nature.com/articles/s41586-020-2649-2",
     #   "https://science.org/doi/10.1126/science.abd4559",
        # 更多 HTML 页面链接...
    ]

    for url in input_urls:
        process_article_page(url)
        time.sleep(1)