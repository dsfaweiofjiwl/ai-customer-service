# 中创证券智能客服

基于 RAG + LLM 的 AI 客服系统，面向证券行业场景，实现知识库检索增强生成 + 流式对话。

## 功能

- **RAG 问答**：用户提问 → FAISS 向量检索 → DeepSeek 流式生成回答
- **知识库管理**：后台管理面板，支持 Markdown 知识文档和 JSON FAQ 的增删改查
- **流式对话**：SSE 实时推送回复，用户无需等待完整生成
- **行业合规**：System Prompt 约束纯文本输出、禁止投资建议、禁止 Markdown 格式

## 快速开始

```bash
pip install -r requirements.txt
# 配置 .env 文件（参考 .env.example）
python main.py
# 浏览器打开 http://localhost:8000
# 管理后台 http://localhost:8000/admin
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `DEEPSEEK_API_KEY` | DeepSeek API Key |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 |
| `DEEPSEEK_MODEL` | 模型名称 |
| `EMBEDDING_MODEL` | Sentence Transformers 模型名 |
| `SIMILARITY_THRESHOLD` | 检索相似度阈值 |

## 架构

```
main.py           # FastAPI 入口
src/
  rag.py          # RAG 引擎（Embedding + FAISS 检索）
  llm.py          # DeepSeek 流式调用
  chat.py         # 对话接口（SSE）
  kb.py           # 知识库管理 API
  prompts.py      # System Prompt 模板
  session.py      # 会话管理
knowledge/        # 知识库 Markdown 文件
templates/        # Jinja2 页面模板
static/           # CSS / JS / 吉祥物动画
```

## 技术栈

Python / FastAPI / Sentence Transformers / FAISS / DeepSeek API / Jinja2 / SSE
