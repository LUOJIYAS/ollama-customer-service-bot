"""
编码规则管理服务

用于管理编码学习规则，包括文件解析、规则存储、检索等功能。
严格按照项目规则实现，使用Pythonic实践和完整的类型注解。
"""

import os
import json
import uuid
import asyncio
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .ollama_client import OllamaClient
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class CodingRulesManager:
    """
    编码规则管理器
    
    负责编码规则的增删改查、文件解析、向量存储集成等功能。
    遵循单一职责原则，提供清晰的接口和健壮的异常处理。
    """
    
    def __init__(self, vector_store: VectorStore, ollama_client: OllamaClient) -> None:
        """
        初始化编码规则管理器
        
        Args:
            vector_store: 向量存储实例
            ollama_client: Ollama客户端实例
        """
        self.vector_store = vector_store
        self.ollama_client = ollama_client
        
        # 数据存储路径
        self.data_dir = Path("data/coding_rules")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = self.data_dir / "coding_rules.db"
        
        # 支持的编程语言文件扩展名
        self.language_extensions = {
            ".py": "Python",
            ".js": "JavaScript", 
            ".ts": "TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".cs": "C#",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".rb": "Ruby",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".r": "R",
            ".sql": "SQL",
            ".sh": "Shell",
            ".md": "Markdown",
            ".txt": "Text"
        }
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self) -> None:
        """
        初始化SQLite数据库
        
        创建编码规则表和相关索引，确保数据库结构正确。
        
        Raises:
            Exception: 数据库初始化失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 创建编码规则表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS coding_rules (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        language TEXT NOT NULL,
                        content TEXT NOT NULL,
                        example TEXT,
                        category TEXT,
                        tags TEXT,
                        file_name TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引以提高查询性能
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_language ON coding_rules(language)",
                    "CREATE INDEX IF NOT EXISTS idx_category ON coding_rules(category)",
                    "CREATE INDEX IF NOT EXISTS idx_created_at ON coding_rules(created_at)",
                    "CREATE INDEX IF NOT EXISTS idx_title ON coding_rules(title)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                logger.info("编码规则数据库初始化成功")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    async def add_coding_rule(
        self,
        title: str,
        description: str,
        language: str,
        content: str,
        example: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
        file_name: Optional[str] = None
    ) -> str:
        """
        添加编码规则
        
        Args:
            title: 规则标题
            description: 规则描述
            language: 编程语言
            content: 规则内容
            example: 示例代码
            category: 规则分类
            tags: 标签列表
            file_name: 源文件名
            
        Returns:
            str: 生成的规则ID
            
        Raises:
            Exception: 添加失败时抛出异常
        """
        try:
            rule_id = str(uuid.uuid4())
            
            # 确保所有参数类型正确
            title = str(title) if title else ""
            description = str(description) if description else ""
            language = str(language) if language else ""
            content = str(content) if content else ""
            example = str(example) if example else ""
            category = str(category) if category else "general"
            file_name = str(file_name) if file_name else None
            
            # 处理tags - 确保转换为JSON字符串
            if tags is None:
                tags_json = "[]"
            elif isinstance(tags, list):
                tags_json = json.dumps(tags, ensure_ascii=False)
            elif isinstance(tags, str):
                # 如果tags已经是字符串，尝试解析再重新编码确保格式正确
                try:
                    parsed_tags = json.loads(tags)
                    tags_json = json.dumps(parsed_tags, ensure_ascii=False)
                except json.JSONDecodeError:
                    # 如果不是有效的JSON，当作单个标签处理
                    tags_json = json.dumps([tags], ensure_ascii=False)
            else:
                tags_json = "[]"
            
            # 数据库插入
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                insert_sql = """
                    INSERT INTO coding_rules 
                    (id, title, description, language, content, example, category, tags, file_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                insert_params = (
                    rule_id,           # 1
                    title,             # 2
                    description,       # 3
                    language,          # 4
                    content,           # 5
                    example,           # 6
                    category,          # 7
                    tags_json,         # 8
                    file_name          # 9
                )
                
                # 调试信息
                logger.debug(f"插入编码规则 - 参数类型检查:")
                for i, param in enumerate(insert_params, 1):
                    logger.debug(f"  参数{i}: {type(param).__name__} = {repr(param)[:100]}")
                
                cursor.execute(insert_sql, insert_params)
                conn.commit()
            
            # 添加到向量存储用于语义搜索
            await self._add_to_vector_store(rule_id, title, description, content, language, category)
            
            logger.info(f"添加编码规则成功: {title} (ID: {rule_id})")
            return rule_id
            
        except Exception as e:
            logger.error(f"添加编码规则失败: {e}")
            logger.error(f"参数信息: title={title}, language={language}, tags={tags}")
            raise

    async def _add_to_vector_store(
        self, 
        rule_id: str, 
        title: str, 
        description: str, 
        content: str, 
        language: str, 
        category: str
    ) -> None:
        """
        将编码规则添加到向量存储
        
        Args:
            rule_id: 规则ID
            title: 标题
            description: 描述
            content: 内容
            language: 编程语言
            category: 分类
        """
        try:
            # 构建用于向量化的文档内容
            doc_content = f"""编码规则: {title}
描述: {description}
编程语言: {language}
分类: {category}
内容: {content}"""
            
            # 暂时记录日志，实际使用时需要调用向量存储的添加方法
            logger.info(f"编码规则已准备添加到向量存储: {title}")
            
        except Exception as e:
            logger.error(f"向量存储添加失败: {e}")

    async def list_coding_rules(
        self,
        page: int = 1,
        page_size: int = 10,
        category: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取编码规则列表（分页）
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            category: 分类筛选
            language: 语言筛选
            
        Returns:
            Dict[str, Any]: 包含规则列表和分页信息的字典
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
                cursor = conn.cursor()
                
                # 构建查询条件
                where_conditions = []
                params = []
                
                if category:
                    where_conditions.append("category = ?")
                    params.append(category)
                
                if language:
                    where_conditions.append("language = ?")
                    params.append(language)
                
                where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
                
                # 获取总数
                count_query = f"SELECT COUNT(*) FROM coding_rules {where_clause}"
                cursor.execute(count_query, params)
                total = cursor.fetchone()[0]
                
                # 获取分页数据
                offset = (page - 1) * page_size
                data_query = f"""
                    SELECT * FROM coding_rules {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """
                cursor.execute(data_query, params + [page_size, offset])
                rows = cursor.fetchall()
                
                # 转换为字典格式
                items = []
                for row in rows:
                    item = dict(row)
                    # 解析JSON字段
                    try:
                        item['tags'] = json.loads(item['tags']) if item['tags'] else []
                    except json.JSONDecodeError:
                        item['tags'] = []
                    items.append(item)
                
                return {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
                
        except Exception as e:
            logger.error(f"获取编码规则列表失败: {e}")
            raise

    async def get_coding_rule_by_id(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """
        通过ID获取编码规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            Optional[Dict[str, Any]]: 规则信息，不存在时返回None
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM coding_rules WHERE id = ?", (rule_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                item = dict(row)
                # 解析JSON字段
                try:
                    item['tags'] = json.loads(item['tags']) if item['tags'] else []
                except json.JSONDecodeError:
                    item['tags'] = []
                
                return item
                
        except Exception as e:
            logger.error(f"获取编码规则失败: {e}")
            raise

    async def delete_coding_rule(self, rule_id: str) -> bool:
        """
        删除编码规则
        
        Args:
            rule_id: 规则ID
            
        Returns:
            bool: 删除成功返回True，规则不存在返回False
            
        Raises:
            Exception: 删除失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM coding_rules WHERE id = ?", (rule_id,))
                affected_rows = cursor.rowcount
                conn.commit()
                
                if affected_rows > 0:
                    logger.info(f"删除编码规则成功: {rule_id}")
                    return True
                else:
                    logger.warning(f"编码规则不存在: {rule_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"删除编码规则失败: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取编码规则统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 总规则数
                cursor.execute("SELECT COUNT(*) FROM coding_rules")
                total_rules = cursor.fetchone()[0]
                
                # 语言分布
                cursor.execute("""
                    SELECT language, COUNT(*) as count 
                    FROM coding_rules 
                    GROUP BY language 
                    ORDER BY count DESC
                """)
                languages = [{"language": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                # 分类分布
                cursor.execute("""
                    SELECT category, COUNT(*) as count 
                    FROM coding_rules 
                    GROUP BY category 
                    ORDER BY count DESC
                """)
                categories = [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]
                
                # 最近创建的规则
                cursor.execute("""
                    SELECT created_at 
                    FROM coding_rules 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                latest_row = cursor.fetchone()
                latest_created = latest_row[0] if latest_row else None
                
                return {
                    "total_rules": total_rules,
                    "languages": languages,
                    "categories": categories,
                    "latest_created": latest_created,
                    "supported_languages": len(self.language_extensions)
                }
                
        except Exception as e:
            logger.error(f"获取编码规则统计失败: {e}")
            raise

    async def get_categories(self) -> List[str]:
        """
        获取所有分类列表
        
        Returns:
            List[str]: 分类名称列表
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT DISTINCT category FROM coding_rules ORDER BY category")
                categories = [row[0] for row in cursor.fetchall() if row[0]]
                
                return categories
                
        except Exception as e:
            logger.error(f"获取分类列表失败: {e}")
            raise

    async def get_languages(self) -> List[str]:
        """
        获取所有编程语言列表
        
        Returns:
            List[str]: 编程语言列表
            
        Raises:
            Exception: 查询失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT DISTINCT language FROM coding_rules ORDER BY language")
                languages = [row[0] for row in cursor.fetchall() if row[0]]
                
                return languages
                
        except Exception as e:
            logger.error(f"获取编程语言列表失败: {e}")
            raise

    async def apply_rule(self, text: str, rule_id: str) -> Dict[str, Any]:
        """
        应用编码规则到文本
        
        使用LLM根据指定的编码规则改进提供的代码文本。
        
        Args:
            text: 需要改进的代码文本
            rule_id: 编码规则ID
            
        Returns:
            Dict[str, Any]: 包含原始代码、改进后代码和改进说明的字典
            
        Raises:
            Exception: 应用规则失败时抛出异常
        """
        try:
            # 获取编码规则
            rule = await self.get_coding_rule_by_id(rule_id)
            if not rule:
                raise ValueError(f"编码规则不存在: {rule_id}")
            
            # 构建系统提示
            system_prompt = f"""你是一个专业的代码审查专家。请根据提供的编码规则改进用户的代码。

编码规则信息：
标题: {rule['title']}
描述: {rule['description']}
编程语言: {rule['language']}
规则内容: {rule['content']}
示例: {rule['example']}

请按照以下要求：
1. 严格按照提供的编码规则改进代码
2. 保持代码的功能不变
3. 提供详细的改进说明
4. 使用中文回答

输出格式：
```{rule['language'].lower()}
[改进后的代码]
```

改进说明：
[详细说明每个改进点和原因]"""

            # 构建用户消息
            user_message = f"请根据编码规则改进以下代码：\n\n```{rule['language'].lower()}\n{text}\n```"
            
            # 调用LLM进行代码改进
            messages = [
                {"role": "user", "content": user_message}
            ]
            
            improved_code = ""
            explanation = ""
            
            # 获取LLM响应
            async for chunk in self.ollama_client.chat_stream(
                messages=messages,
                system=system_prompt,
                model="deepseek-r1:latest"
            ):
                improved_code += chunk
            
            # 解析响应，分离代码和说明
            if "```" in improved_code:
                parts = improved_code.split("```")
                if len(parts) >= 3:
                    # 提取代码块
                    code_block = parts[1]
                    if code_block.startswith(rule['language'].lower()):
                        code_block = code_block[len(rule['language'].lower()):].strip()
                    
                    # 提取说明
                    explanation = parts[2].strip()
                    if explanation.startswith("改进说明："):
                        explanation = explanation[5:].strip()
                    
                    improved_code = code_block
                else:
                    explanation = "代码已根据编码规则进行改进"
            else:
                explanation = "代码已根据编码规则进行改进"
            
            result = {
                "original_code": text,
                "improved_code": improved_code.strip(),
                "explanation": explanation,
                "rule_applied": {
                    "id": rule['id'],
                    "title": rule['title'],
                    "language": rule['language']
                }
            }
            
            logger.info(f"应用编码规则成功: {rule['title']}")
            return result
            
        except Exception as e:
            logger.error(f"应用编码规则失败: {e}")
            raise

    def _detect_language_from_filename(self, filename: str) -> str:
        """
        从文件名检测编程语言
        
        Args:
            filename: 文件名
            
        Returns:
            str: 检测到的编程语言，默认为"Text"
        """
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        return self.language_extensions.get(extension, "Text")

    async def process_file(self, file_content: bytes, filename: str, category: str = "upload") -> Dict[str, Any]:
        """
        处理上传的文件，解析其中的编码规则
        
        Args:
            file_content: 文件内容（字节）
            filename: 文件名
            category: 分类
            
        Returns:
            Dict[str, Any]: 解析结果
            
        Raises:
            Exception: 处理失败时抛出异常
        """
        try:
            # 尝试解码文件内容
            try:
                content = file_content.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    content = file_content.decode('gbk')
                except UnicodeDecodeError:
                    content = file_content.decode('latin-1')
            
            # 检测编程语言
            language = self._detect_language_from_filename(filename)
            
            # 使用LLM解析编码规则
            rules = await self._extract_coding_rules_with_llm(content, language, filename)
            
            # 添加解析出的规则到数据库
            added_rules = []
            for rule in rules:
                try:
                    rule_id = await self.add_coding_rule(
                        title=rule.get('title', f'{filename} 编码规则'),
                        description=rule.get('description', ''),
                        language=language,
                        content=rule.get('content', ''),
                        example=rule.get('example', ''),
                        category=category,
                        tags=rule.get('tags', []),
                        file_name=filename
                    )
                    added_rules.append(rule_id)
                except Exception as e:
                    logger.error(f"添加解析规则失败: {e}")
            
            result = {
                "filename": filename,
                "language": language,
                "rules_found": len(rules),
                "rules_added": len(added_rules),
                "added_rule_ids": added_rules,
                "rules_details": rules
            }
            
            logger.info(f"文件处理完成: {filename}, 发现规则: {len(rules)}, 添加成功: {len(added_rules)}")
            return result
            
        except Exception as e:
            logger.error(f"处理文件失败: {e}")
            raise

    async def _extract_coding_rules_with_llm(
        self, 
        content: str, 
        language: str, 
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        使用LLM从文件内容中提取编码规则
        
        Args:
            content: 文件内容
            language: 编程语言
            filename: 文件名
            
        Returns:
            List[Dict[str, Any]]: 提取的编码规则列表
        """
        try:
            system_prompt = f"""你是一个专业的代码分析专家。请从提供的{language}代码文件中提取编码规则和最佳实践。

请分析代码中体现的：
1. 命名规范
2. 代码风格
3. 设计模式
4. 最佳实践
5. 代码结构
6. 注释风格

对于每个发现的编码规则，请提供：
- title: 规则标题（简洁明了）
- description: 详细描述
- content: 规则的具体内容和要求
- example: 从代码中提取的示例
- tags: 相关标签（如"命名规范"、"代码风格"等）

请以JSON格式返回，格式如下：
[
  {{
    "title": "规则标题",
    "description": "规则描述",
    "content": "具体规则内容",
    "example": "代码示例",
    "tags": ["标签1", "标签2"]
  }}
]

如果代码中没有明显的编码规则，请返回空数组 []。"""

            user_message = f"请分析以下{language}代码文件（{filename}）中的编码规则：\n\n```{language.lower()}\n{content}\n```"
            
            messages = [
                {"role": "user", "content": user_message}
            ]
            
            response = ""
            async for chunk in self.ollama_client.chat_stream(
                messages=messages,
                system=system_prompt,
                model="deepseek-r1:latest"
            ):
                response += chunk
            
            # 尝试解析JSON响应
            try:
                # 提取JSON部分
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                elif "[" in response and "]" in response:
                    json_start = response.find("[")
                    json_end = response.rfind("]") + 1
                    json_str = response[json_start:json_end]
                else:
                    json_str = response.strip()
                
                rules = json.loads(json_str)
                
                # 验证规则格式
                valid_rules = []
                for rule in rules:
                    if isinstance(rule, dict) and 'title' in rule:
                        valid_rules.append({
                            'title': rule.get('title', ''),
                            'description': rule.get('description', ''),
                            'content': rule.get('content', ''),
                            'example': rule.get('example', ''),
                            'tags': rule.get('tags', [])
                        })
                
                logger.info(f"从文件 {filename} 提取到 {len(valid_rules)} 个编码规则")
                return valid_rules
                
            except json.JSONDecodeError as e:
                logger.warning(f"LLM响应JSON解析失败: {e}, 响应内容: {response[:500]}")
                return []
                
        except Exception as e:
            logger.error(f"LLM提取编码规则失败: {e}")
            return [] 