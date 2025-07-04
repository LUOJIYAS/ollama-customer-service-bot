#!/usr/bin/env python3
"""
示例数据初始化脚本
用于为智能客服机器人添加初始知识库数据
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.vector_store import VectorStore
from services.ollama_client import OllamaClient
from services.knowledge_manager import KnowledgeManager

# 示例知识库数据
SAMPLE_KNOWLEDGE = [
    {
        "title": "公司介绍",
        "content": "我们是一家专注于人工智能技术的创新公司，致力于为客户提供最优质的智能客服解决方案。我们的产品基于最新的大语言模型技术，能够理解和回答各种复杂的客户问题。",
        "category": "company",
        "tags": ["公司", "介绍", "AI"]
    },
    {
        "title": "产品功能",
        "content": "我们的智能客服机器人具有以下核心功能：1. 自然语言理解和对话；2. 知识库管理和搜索；3. 多种文件格式支持；4. 实时流式响应；5. 可视化管理界面；6. 多分类知识组织。",
        "category": "product",
        "tags": ["产品", "功能", "特性"]
    },
    {
        "title": "技术支持",
        "content": "如果您在使用过程中遇到任何技术问题，请尝试以下解决方案：1. 检查网络连接是否正常；2. 确认Ollama服务是否运行；3. 查看后端服务日志；4. 重启相关服务。如问题仍存在，请联系技术支持团队。",
        "category": "technical",
        "tags": ["技术支持", "故障排除", "帮助"]
    },
    {
        "title": "常见问题",
        "content": "Q: 如何添加新的知识库内容？A: 您可以通过知识库管理界面手动添加，或者上传文件批量导入。Q: 支持哪些文件格式？A: 支持TXT、PDF、DOCX、XLSX、JSON等格式。Q: 如何提高回答准确性？A: 建议添加更多相关知识内容，并使用合适的分类和标签。",
        "category": "faq",
        "tags": ["常见问题", "FAQ", "帮助"]
    },
    {
        "title": "服务价格",
        "content": "我们提供灵活的价格方案：1. 基础版：适合小型企业，包含基本对话功能；2. 专业版：适合中型企业，包含知识库管理；3. 企业版：适合大型企业，包含定制化功能。具体价格请联系销售团队获取报价。",
        "category": "pricing",
        "tags": ["价格", "服务", "套餐"]
    },
    {
        "title": "联系方式",
        "content": "如需了解更多信息或寻求帮助，请通过以下方式联系我们：技术支持邮箱：support@example.com；销售咨询邮箱：sales@example.com；客服热线：400-123-4567；工作时间：周一至周五 9:00-18:00。",
        "category": "contact",
        "tags": ["联系方式", "客服", "支持"]
    },
    {
        "title": "用户指南",
        "content": "使用指南：1. 首次使用请先启动Ollama服务；2. 访问系统首页开始对话；3. 点击知识库管理按钮可以添加或编辑知识；4. 支持文件拖拽上传；5. 使用搜索功能快速查找相关知识；6. 查看统计信息了解使用情况。",
        "category": "guide",
        "tags": ["用户指南", "使用方法", "教程"]
    },
    {
        "title": "系统要求",
        "content": "系统运行要求：硬件要求 - CPU: 4核以上，内存: 16GB以上，存储: 50GB可用空间；软件要求 - Python 3.8+，Node.js 16+，Ollama最新版；网络要求 - 稳定的互联网连接用于模型下载；推荐配置 - 支持CUDA的GPU可显著提升性能。",
        "category": "system",
        "tags": ["系统要求", "配置", "硬件"]
    }
]

async def initialize_sample_data():
    """初始化示例数据"""
    print("🚀 开始初始化示例知识库数据...")
    
    try:
        # 初始化服务
        print("📋 初始化服务组件...")
        vector_store = VectorStore()
        await vector_store.initialize()
        
        ollama_client = OllamaClient()
        knowledge_manager = KnowledgeManager(vector_store, ollama_client)
        
        # 检查Ollama服务
        print("🔍 检查Ollama服务状态...")
        if not await ollama_client.check_health():
            print("❌ Ollama服务不可用，请先启动Ollama服务")
            return False
        
        # 添加示例数据
        print(f"📚 开始添加 {len(SAMPLE_KNOWLEDGE)} 条示例知识...")
        success_count = 0
        
        for i, knowledge in enumerate(SAMPLE_KNOWLEDGE, 1):
            try:
                print(f"  ({i}/{len(SAMPLE_KNOWLEDGE)}) 添加: {knowledge['title']}")
                await knowledge_manager.add_knowledge(**knowledge)
                success_count += 1
            except Exception as e:
                print(f"  ❌ 添加失败: {e}")
        
        print(f"✅ 成功添加 {success_count}/{len(SAMPLE_KNOWLEDGE)} 条知识库数据")
        
        # 显示统计信息
        stats = await knowledge_manager.get_stats()
        print(f"📊 当前知识库统计:")
        print(f"  - 总文档数: {stats['total_documents']}")
        print(f"  - 分类数量: {len(stats['categories'])}")
        print(f"  - 热门标签: {len(stats['popular_tags'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("智能客服机器人 - 示例数据初始化")
    print("=" * 60)
    
    success = await initialize_sample_data()
    
    if success:
        print("\n🎉 示例数据初始化完成！")
        print("现在您可以启动后端服务开始使用智能客服机器人了。")
        print("\n启动命令:")
        print("  python start.py")
    else:
        print("\n💥 初始化失败，请检查错误信息并重试。")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 