# API 服务

这是 V1 的 FastAPI 后端。

当前能力：

- 上传 `.txt` / `.md` 文档。
- 将文档切成 chunk。
- 用 SQLite 持久化保存文档和 chunk。
- 查看已上传文档列表。
- 根据问题检索相关 chunk。
- 返回模板答案和来源。
- 可选接入 DeepSeek / OpenAI 兼容 API，让大模型基于检索来源生成回答。

## 启动方式

进入 `apps/api` 后安装依赖：

```bash
pip install -r requirements.txt
```

启动服务：

```bash
uvicorn app.main:app --reload --port 8000
```

访问：

```text
http://127.0.0.1:8000/docs
```

数据库文件会自动创建在：

```text
apps/api/data/knowledge_base.sqlite3
```

## 可选：接入 DeepSeek API 回答

先重新安装依赖，确保 `openai` SDK 已安装。DeepSeek API 兼容 OpenAI SDK：

```powershell
python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

复制配置模板：

```powershell
Copy-Item .env.example .env
```

然后编辑 `.env`：

```text
LLM_PROVIDER=deepseek
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=你的 DeepSeek API Key
LLM_TIMEOUT_SECONDS=30
LLM_MAX_RETRIES=2
LLM_MAX_COMPLETION_TOKENS=1200
DEFAULT_ANSWER_MODE=local
```

LLM 客户端在进程内复用 HTTP 连接池；以上三个参数分别控制单次超时、SDK
重试次数和最大输出 token。生产环境仍应在网关层增加租户限流和总预算。

然后重新启动服务。

## 选择回答模式

`POST /chat` 支持 `answer_mode`：

```json
{
  "question": "请总结客户 A 项目风险",
  "answer_mode": "local"
}
```

可选值：

- `local`：只使用内部 RAG 规则/模板，不调用外部 API。
- `api`：调用 DeepSeek / OpenAI 兼容 API，基于检索来源生成总结。
- `auto`：默认自动模式。明确延期原因问题优先走内部规则；其他问题如果配置了 API Key，就调用 API。
