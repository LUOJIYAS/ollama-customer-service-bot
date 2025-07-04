"""
机器人管理器

负责智能机器人的创建、管理和嵌入功能。
遵循单一职责原则，提供清晰的接口和健壮的异常处理。
"""

import json
import logging
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class BotManager:
    """
    机器人管理器
    
    负责机器人的增删改查、嵌入代码生成等功能。
    """
    
    def __init__(self) -> None:
        """初始化机器人管理器"""
        # 数据存储路径
        self.data_dir = Path("data/bots")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = self.data_dir / "bots.db"
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self) -> None:
        """
        初始化SQLite数据库
        
        创建机器人表和相关索引，确保数据库结构正确。
        
        Raises:
            Exception: 数据库初始化失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 创建机器人表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bots (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        avatar TEXT,
                        position TEXT DEFAULT 'bottom-right',
                        size TEXT DEFAULT 'medium',
                        primary_color TEXT DEFAULT '#1890ff',
                        greeting_message TEXT,
                        knowledge_base_enabled BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # 创建索引以提高查询性能
                indexes = [
                    "CREATE INDEX IF NOT EXISTS idx_bot_name ON bots(name)",
                    "CREATE INDEX IF NOT EXISTS idx_bot_created_at ON bots(created_at)"
                ]
                
                for index_sql in indexes:
                    cursor.execute(index_sql)
                
                conn.commit()
                logger.info("机器人数据库初始化成功")
                
        except Exception as e:
            logger.error(f"机器人数据库初始化失败: {e}")
            raise

    async def create_bot(
        self,
        name: str,
        description: str,
        avatar: str = "/default-bot-avatar.png",
        position: str = "bottom-right",
        size: str = "medium",
        primary_color: str = "#1890ff",
        greeting_message: str = "您好！我是您的智能助手，有什么可以帮助您的吗？",
        knowledge_base_enabled: bool = True
    ) -> Dict[str, Any]:
        """
        创建机器人
        
        Args:
            name: 机器人名称
            description: 机器人描述
            avatar: 头像URL
            position: 显示位置
            size: 大小
            primary_color: 主色调
            greeting_message: 欢迎语
            knowledge_base_enabled: 是否启用知识库
            
        Returns:
            Dict[str, Any]: 创建的机器人信息
            
        Raises:
            Exception: 创建失败时抛出异常
        """
        try:
            bot_id = str(uuid.uuid4())
            
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO bots 
                    (id, name, description, avatar, position, size, primary_color, greeting_message, knowledge_base_enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    bot_id, name, description, avatar, position, size, 
                    primary_color, greeting_message, knowledge_base_enabled
                ))
                
                conn.commit()
            
            # 获取创建的机器人信息
            bot = await self.get_bot_by_id(bot_id)
            if not bot:
                raise Exception(f"创建机器人后无法获取机器人信息: {bot_id}")
            
            logger.info(f"机器人创建成功: {name} (ID: {bot_id})")
            return bot
            
        except Exception as e:
            logger.error(f"创建机器人失败: {e}")
            raise

    async def get_bot_by_id(self, bot_id: str) -> Optional[Dict[str, Any]]:
        """
        通过ID获取机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            Optional[Dict[str, Any]]: 机器人信息，不存在时返回None
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM bots WHERE id = ?", (bot_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                bot = dict(row)
                # 添加嵌入URL
                bot['embed_url'] = f"/bot/{bot_id}"
                
                return bot
                
        except Exception as e:
            logger.error(f"获取机器人失败: {e}")
            raise

    async def list_bots(
        self,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        获取机器人列表（分页）
        
        Args:
            page: 页码（从1开始）
            page_size: 每页大小
            
        Returns:
            Dict[str, Any]: 包含机器人列表和分页信息的字典
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # 获取总数
                cursor.execute("SELECT COUNT(*) FROM bots")
                total = cursor.fetchone()[0]
                
                # 获取分页数据
                offset = (page - 1) * page_size
                cursor.execute("""
                    SELECT * FROM bots 
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (page_size, offset))
                rows = cursor.fetchall()
                
                # 转换为字典格式并添加嵌入URL
                items = []
                for row in rows:
                    bot = dict(row)
                    bot['embed_url'] = f"/bot/{bot['id']}"
                    items.append(bot)
                
                return {
                    "items": items,
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": (total + page_size - 1) // page_size
                }
                
        except Exception as e:
            logger.error(f"获取机器人列表失败: {e}")
            raise

    async def delete_bot(self, bot_id: str) -> bool:
        """
        删除机器人
        
        Args:
            bot_id: 机器人ID
            
        Returns:
            bool: 删除成功返回True，机器人不存在返回False
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("DELETE FROM bots WHERE id = ?", (bot_id,))
                affected_rows = cursor.rowcount
                conn.commit()
                
                if affected_rows > 0:
                    logger.info(f"删除机器人成功: {bot_id}")
                    return True
                else:
                    logger.warning(f"机器人不存在: {bot_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"删除机器人失败: {e}")
            raise

    async def update_bot(
        self,
        bot_id: str,
        name: str,
        description: str,
        avatar: str = "/default-bot-avatar.png",
        position: str = "bottom-right",
        size: str = "medium",
        primary_color: str = "#1890ff",
        greeting_message: str = "您好！我是您的智能助手，有什么可以帮助您的吗？",
        knowledge_base_enabled: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        更新机器人信息
        
        Args:
            bot_id: 机器人ID
            name: 机器人名称
            description: 机器人描述
            avatar: 头像URL
            position: 显示位置
            size: 大小
            primary_color: 主色调
            greeting_message: 欢迎语
            knowledge_base_enabled: 是否启用知识库
            
        Returns:
            Optional[Dict[str, Any]]: 更新后的机器人信息，不存在时返回None
            
        Raises:
            Exception: 更新失败时抛出异常
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 检查机器人是否存在
                cursor.execute("SELECT id FROM bots WHERE id = ?", (bot_id,))
                if not cursor.fetchone():
                    return None
                
                # 更新机器人信息
                cursor.execute("""
                    UPDATE bots 
                    SET name = ?, description = ?, avatar = ?, position = ?, 
                        size = ?, primary_color = ?, greeting_message = ?, 
                        knowledge_base_enabled = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    name, description, avatar, position, size, 
                    primary_color, greeting_message, knowledge_base_enabled, bot_id
                ))
                
                conn.commit()
            
            # 获取更新后的机器人信息
            updated_bot = await self.get_bot_by_id(bot_id)
            
            logger.info(f"机器人更新成功: {name} (ID: {bot_id})")
            return updated_bot
            
        except Exception as e:
            logger.error(f"更新机器人失败: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取机器人统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                # 总机器人数
                cursor.execute("SELECT COUNT(*) FROM bots")
                total_bots = cursor.fetchone()[0]
                
                # 启用知识库的机器人数
                cursor.execute("SELECT COUNT(*) FROM bots WHERE knowledge_base_enabled = 1")
                enabled_kb_bots = cursor.fetchone()[0]
                
                # 最近创建的机器人
                cursor.execute("""
                    SELECT created_at 
                    FROM bots 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                latest_row = cursor.fetchone()
                latest_created = latest_row[0] if latest_row else None
                
                return {
                    "total_bots": total_bots,
                    "enabled_kb_bots": enabled_kb_bots,
                    "latest_created": latest_created
                }
                
        except Exception as e:
            logger.error(f"获取机器人统计失败: {e}")
            raise

    def generate_embed_script(self, bot_id: str, base_url: str) -> str:
        """
        生成机器人嵌入脚本
        
        Args:
            bot_id: 机器人ID
            base_url: 基础URL
            
        Returns:
            str: 嵌入脚本代码
        """
        # 确定前端URL - 从后端URL推导出前端URL
        if 'localhost' in base_url or '127.0.0.1' in base_url:
            # 开发环境
            frontend_url = 'http://localhost:3000'
        else:
            # 生产环境 - 将8000端口替换为3000端口
            frontend_url = base_url.replace(':8000', ':3000')
        
        script = f"""
(function() {{
    var botId = '{bot_id}';
    var frontendUrl = '{frontend_url}';
    
    // 创建样式
    var style = document.createElement('style');
    style.textContent = `
        .ai-bot-container {{
            position: fixed;
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }}
        .ai-bot-trigger {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: #1890ff;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}
        .ai-bot-trigger:hover {{
            transform: scale(1.1);
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
        }}
        .ai-bot-trigger svg {{
            width: 30px;
            height: 30px;
            fill: white;
        }}
        .ai-bot-chat {{
            position: fixed;
            bottom: 80px;
            right: 20px;
            width: 350px;
            height: 500px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
            display: none;
            flex-direction: column;
            z-index: 10001;
        }}
        .ai-bot-chat.show {{
            display: flex;
        }}
        .ai-bot-close {{
            position: absolute;
            top: 8px;
            right: 8px;
            width: 24px;
            height: 24px;
            border: none;
            background: rgba(0, 0, 0, 0.1);
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10002;
            color: #666;
            font-size: 14px;
        }}
        .ai-bot-close:hover {{
            background: rgba(0, 0, 0, 0.2);
        }}
    `;
    document.head.appendChild(style);
    
    // 创建机器人容器
    var container = document.createElement('div');
    container.className = 'ai-bot-container';
    container.style.bottom = '20px';
    container.style.right = '20px';
    
    // 创建触发按钮
    var trigger = document.createElement('button');
    trigger.className = 'ai-bot-trigger';
    trigger.innerHTML = '<svg viewBox="0 0 1024 1024"><path d="M300 328a60 60 0 1 0 120 0 60 60 0 1 0-120 0Z M540 328a60 60 0 1 0 120 0 60 60 0 1 0-120 0Z"/><path d="M512 64C264.6 64 64 264.6 64 512s200.6 448 448 448 448-200.6 448-448S759.4 64 512 64Z"/></svg>';
    
    // 创建聊天窗口
    var chatWindow = document.createElement('div');
    chatWindow.className = 'ai-bot-chat';
    
    // 创建关闭按钮
    var closeBtn = document.createElement('button');
    closeBtn.className = 'ai-bot-close';
    closeBtn.innerHTML = '×';
    closeBtn.addEventListener('click', function() {{
        chatWindow.classList.remove('show');
    }});
    
    // 创建iframe
    var iframe = document.createElement('iframe');
    iframe.src = frontendUrl + '/bot/' + botId;
    iframe.style.width = '100%';
    iframe.style.height = '100%';
    iframe.style.border = 'none';
    iframe.style.borderRadius = '12px';
    
    chatWindow.appendChild(closeBtn);
    chatWindow.appendChild(iframe);
    
    // 添加点击事件
    trigger.addEventListener('click', function() {{
        chatWindow.classList.toggle('show');
    }});
    
    // 点击外部关闭窗口
    document.addEventListener('click', function(e) {{
        if (!chatWindow.contains(e.target) && !trigger.contains(e.target)) {{
            chatWindow.classList.remove('show');
        }}
    }});
    
    // 添加到页面
    container.appendChild(trigger);
    document.body.appendChild(container);
    document.body.appendChild(chatWindow);
}})();
"""
        return script 