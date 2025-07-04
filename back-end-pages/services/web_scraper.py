"""
网页内容抓取服务
支持解析网页URL并提取有用的文本内容
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
import re
from urllib.parse import urljoin, urlparse
from utils.logger import setup_logger

logger = setup_logger(__name__)

class WebScraper:
    """网页内容抓取器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    async def scrape_url(self, url: str) -> Dict[str, str]:
        """
        抓取网页内容
        
        Args:
            url: 网页URL
            
        Returns:
            包含标题、内容、描述等信息的字典
        """
        try:
            # 验证URL格式
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError("无效的URL格式")
            
            # 统一优化所有网站的访问体验
            domain = parsed_url.netloc.lower()
            
            # 更新请求头，模拟更真实的浏览器环境（适用于所有网站）
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Not/A)Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # 发送请求
            try:
                response = self.session.get(url, timeout=15)  # 统一增加超时时间
                response.raise_for_status()
                response.encoding = response.apparent_encoding or 'utf-8'
            except requests.exceptions.HTTPError as http_err:
                if response.status_code == 521:
                    raise Exception(f"网站限制了访问，可能启用了爬虫防护。建议直接从浏览器打开该链接并手动复制内容")
                elif response.status_code == 403:
                    raise Exception(f"访问被拒绝(403)，该网站可能禁止了自动抓取")
                else:
                    raise Exception(f"HTTP错误: {response.status_code}")
            except requests.exceptions.ConnectionError:
                raise Exception(f"连接错误，无法访问该网站")
            except requests.exceptions.Timeout:
                raise Exception(f"请求超时，网站响应时间过长")
            except requests.exceptions.TooManyRedirects:
                raise Exception(f"重定向过多，无法访问最终页面")
            except requests.exceptions.RequestException as req_err:
                raise Exception(f"请求错误: {str(req_err)}")
                
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取标题
            title = self._extract_title(soup)
            
            # 提取描述
            description = self._extract_description(soup)
            
            # 提取主要内容
            content = self._extract_content(soup)
            
            # 如果提取的内容太短，可能是网站有反爬机制
            if isinstance(content, str) and len(content) < 100 and (not description or not isinstance(description, str) or len(description) < 10):
                logger.warning(f"提取的内容过短，可能是网站有反爬机制: {url}")
                content = content + "\n\n注意：内容提取可能不完整，该网站可能限制了自动内容抓取。建议直接从浏览器打开链接并手动复制内容。"
            
            # 提取关键词
            keywords = self._extract_keywords(soup)
            
            result = {
                'url': url,
                'title': title,
                'description': description,
                'content': content,
                'keywords': keywords,
                'domain': parsed_url.netloc
            }
            
            logger.info(f"成功抓取网页: {url}, 标题: {title}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"网络请求失败: {url}, 错误: {e}")
            
            # 为所有网站提供统一的友好错误信息
            err_msg = str(e)
            if "timeout" in err_msg.lower():
                raise Exception(f"请求超时，网站响应时间过长。请稍后重试或直接从浏览器打开。")
            elif "connection" in err_msg.lower():
                raise Exception(f"连接错误，无法访问该网站。请检查网络或直接从浏览器打开。")
            else:
                raise Exception(f"无法访问网页: {err_msg}。建议直接从浏览器打开并手动复制内容。")
                
        except Exception as e:
            logger.error(f"网页解析失败: {url}, 错误: {e}")
            raise Exception(f"网页解析失败: {str(e)}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取页面标题"""
        # 尝试多种方式获取标题
        title_sources = [
            soup.find('title'),
            soup.find('meta', {'property': 'og:title'}),
            soup.find('meta', {'name': 'title'}),
            soup.find('h1')
        ]
        
        for source in title_sources:
            if source:
                if source.name == 'title':
                    title = source.get_text(strip=True)
                elif source.name == 'meta':
                    title = source.get('content', '').strip()
                else:
                    title = source.get_text(strip=True)
                    
                if title:
                    return title[:200]  # 限制长度
                    
        return "未知标题"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """提取页面描述"""
        # 尝试多种方式获取描述
        desc_sources = [
            soup.find('meta', {'name': 'description'}),
            soup.find('meta', {'property': 'og:description'}),
            soup.find('meta', {'name': 'twitter:description'})
        ]
        
        for source in desc_sources:
            if source:
                desc = source.get('content', '').strip()
                if desc:
                    return desc[:500]  # 限制长度
                    
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取页面主要内容"""
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # 尝试找到主要内容容器
        main_content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '#content',
            '.container'
        ]
        
        content_element = None
        for selector in main_content_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                break
        
        # 如果没找到特定容器，使用body
        if not content_element:
            content_element = soup.find('body')
        
        if not content_element:
            content_element = soup
        
        # 提取文本内容
        text_content = content_element.get_text(separator='\n', strip=True)
        
        # 清理文本
        lines = text_content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 10:  # 过滤太短的行
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # 限制内容长度
        if len(content) > 5000:
            content = content[:5000] + "..."
        
        return content
    
    def _extract_keywords(self, soup: BeautifulSoup) -> str:
        """提取关键词"""
        keywords_tag = soup.find('meta', {'name': 'keywords'})
        if keywords_tag:
            content = keywords_tag.get('content', '')
            if content and isinstance(content, str):
                return content.strip()[:200]
        return ""
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False 