# Enterprise AI Workflow Assistant

企业智能工单与知识助手平台。

V1 知识库问答、V2 Agentic RAG、V3 工单系统 + 工具调用 + 人工审批、V4 GraphRAG 关系图谱、V5 评测监控与 token 成本面板已全部完成。

> 📊 **[项目总结报告（架构图 · 工作流图 · 指标 · 路线）](docs/project-report.md)** ·
> 🛠 **[工程化落地优化路线](docs/engineering-optimization.md)**

## 安全与工程加固（2026-08 批次）

### 角色鉴权全覆盖
- 写操作（上传/删除文档、重建 embedding、图谱重建、工单创建/删除）要求 `X-User-Role: operator/admin`。
- 审计数据（`/chat-logs`、`/tool-calls`、`/pending-actions`）含问题原文与工具入参，仅 operator/admin 可见；`/metrics/*` 为聚合数据对所有角色开放。
- 角色策略统一收敛在 `app/auth.py`（替换为 JWT/OIDC 时只改这一处）。

### 审批职责分离（四眼原则）
- 请求与审批可携带 `X-User-Id`；已知身份下，发起人不能审批自己的写操作（`APPROVAL_SOD_ENFORCED=0` 可关闭，匿名请求不比对以保留单人演示体验）。
- 前端顶栏提供「用户」标识输入（持久化到 localStorage），切换不同 ID 即可演示四眼审批。

### Agent 层纠偏
- LLM 工具选择的输出先过注册工具白名单，幻觉工具名记日志并在 trace 标记 `filtered`，不进入执行。
- 工单 ID 抽取兼容大写 UUID 并统一小写；目标状态模糊时拒绝生成草稿（不再静默默认 `resolved`）。

### 可观测性与架构
- 结构化 JSON 日志（`app/logging_config.py`，`LOG_FORMAT_TEXT=1` 切人类可读格式），关键降级（LLM 路由回退、API 生成失败、SoD 拒绝）均有日志留痕。
- 供应商异常原文不再进入用户可见答案，只进服务端日志。
- chat/documents 端点从 `main.py` 拆到 `app/routes/`；初始化挪入 FastAPI lifespan（import 无副作用）；`init_db` 按 DB_PATH 记忆化；槽位抽取拆分到 `app/slot_extraction.py`；删除死代码（database 统计函数、兼容包装器）。
- CI（`.github/workflows/ci.yml`）：回归测试 + V2–V6 评测门禁 + 前端 tsc/build。

## 当前流程

```text
上传文档 -> 解析切块 -> SQLite/embedding + 图谱抽取 -> 问题分类 -> query 计划
-> 一到两轮检索 -> 证据门控 -> Graph Agent 关系链 -> Tool Agent -> 回答 -> 引用审核
-> trace / token 成本 / 请求日志 / 用户反馈
```

当前技术实现：

- 后端使用 FastAPI。
- SQLite 持久化 documents、chunks、本地学习版 embedding、图谱实体关系、工单、审批、审计与请求日志。
- 支持 keyword、embedding、hybrid 三种检索方式。
- 支持 local、DeepSeek/OpenAI API、auto 三种回答方式。
- 支持 standard RAG 和 agentic RAG 两种工作流。
- 规则式实体/关系抽取 + BFS 关系链查询（学习版 GraphRAG，无需 Neo4j）。
- token 用量与成本核算（API 模式取真实 usage，local 模式按字符估算、成本记 0）。

## 项目目录

```text
enterprise-ai-workflow-assistant/
  apps/
    api/                 FastAPI 后端
    web/                 React 前端工作台
  docs/
    v1-guide.md          V1 学习与开发说明
  enterprise-ai-workflow-assistant-plan.md
```

## 后续升级路线

1. ~~V3：工单系统、工具调用和人工审批。~~ ✅ 已完成
2. ~~V4：GraphRAG 与关系图谱。~~ ✅ 已完成（学习版：规则抽取 + SQLite + BFS）
3. ~~V5：评测、监控和 token 成本面板。~~ ✅ 已完成
4. 生产化升级：真实 embedding + PostgreSQL/pgvector、Neo4j + LLM 抽取、LangGraph 编排、鉴权与多租户。详见 `docs/engineering-optimization.md`。

## 当前已实现

- FastAPI 后端。
- SQLite 持久化保存文档和 chunk。
- React 前端工作台。
- 上传 `.txt` / `.md` / `.pdf` 文档。
- 查看和删除文档。
- `local` / `api` / `auto` 三种回答模式。
- DeepSeek / OpenAI 兼容 API 接入。
- 来源证据展示。
- 执行轨迹展示，包括检索、来源选择和回答路径。
- Agentic RAG：问题分类、query 改写、多轮检索和动态重查。
- Evidence Check：分数、意图覆盖和主题锚点三层证据门控。
- Reviewer：最终返回前检查并补全标准来源引用。
- Agent 执行摘要：意图、复杂度、检索轮数、query、证据和引用状态。
- 运行指标：请求量、回答/拒答/错误率、证据和引用率、平均/P95 延迟、平均轮数与使用分布。
- 87 个自动化回归测试，覆盖 V2 防幻觉、V3 审批安全、V4 图谱抽取、V5 观测闭环、P0 加固、真实 embedding、结构切块、LLM 路由/声明溯源，P1/P2 的事务回滚、缓存失效、LLM 客户端策略和并发审批，以及安全加固批次（角色校验、职责分离、LLM 工具白名单、槽位抽取纠偏）。
- 离线评测与质量门槛（V2–V6 五道门禁），防止优化后功能悄悄回退。
- V6 黄金评测集（`scripts/golden/`：42 条标注问答 + 4 份多风格语料），judge 用事实子串 + 期望文档，对重切块免疫；基线存档 `baseline_v6.json`。
- A2 检索打分纠偏：停用词、锚点门控三级规则（实体/长词/双字）、意图覆盖按同义词组判定、因果句选择优先级。
- A3 真实语义 embedding（fastembed/BGE-small-zh，512 维，本地 ONNX 推理）＋可选 reranker（cross-encoder，已实测 `RERANKER_MODEL` env 开关，默认关以守住延迟预算）；哈希 n-gram 版保留为无模型降级通道。
- A4 结构感知切块：标题层级链（文档/章节）随块入库，句子级打包与重叠，超长句才硬切；标题词项参与检索与证据锚点。
- B1/B2 LLM 路由、检索规划与工具选择（function-calling 风格，带真实 token 核算），规则版自动降级（`LLM_ROUTER_ENABLED=0` 可关闭，离线门禁默认关闭）。
- B3 声明级溯源：含数字/日期/百分比的陈述句必须在来源中找到锚点，否则附审核提示。
- P1/P2 工程优化：文档/chunk/图谱同事务写入，图谱原子重建，SQLite revision 驱动的 chunk 缓存，SQL 侧指标聚合，共享且受超时/重试/token 预算约束的 LLM 客户端；后端路由按领域拆分，前端按四个 feature 拆分。

## V4 新功能

### 关系图谱（学习版 GraphRAG）
- 规则式实体抽取：客户 / 项目 / 人员 / 合同 / 日期 / 原因 / 风险 / 工单 8 类。
- 关系抽取：委托、负责人、原计划交付、调整后交付、延期原因、涉及合同、合同风险、约定，每条关系带证据句和文档溯源。
- 字段式文档兼容：`客户:甲方客户A项目:xxx` 连排字段自动补句界后抽取。
- SQLite 图存储（graph_entities + graph_relations），上传增量抽取、删除自动重建。
- BFS 关系链查询（最多 4 跳）与实体邻域子图。
- 工单同步进图：工单与命中的客户/项目/人员实体连边，实现跨来源关系。

### Graph Agent
- 关系/风险/因果/事实类问题自动查图，命中实体后取 2 跳邻域。
- 关系链与风险链路注入回答（【关系图谱】上下文块），并写入 trace（graph_lookup 步骤）。
- Agent 摘要新增 graph_entities 和 graph_paths。

### 前端图谱面板
- 实体分层 SVG 可视化（按类型分列、风险关系虚线高亮、点击实体聚焦关联）。
- 关系链查询（起点/终点实体选择 + 链路展示）。
- 关系明细表：源实体、关系、目标实体、证据、来源文档。

## V5 新功能

### Token 成本核算
- API 模式记录真实 prompt/completion token，按可配置单价估算美元成本
  （`LLM_PROMPT_PRICE_PER_1M_USD` / `LLM_COMPLETION_PRICE_PER_1M_USD`，默认 DeepSeek 公开价）。
- local 模式按 0.7 token/字估算规模、成本记 0。
- `/chat` 返回 token_usage；`/metrics/summary` 汇总累计 token、平均 token、累计/平均成本和按回答模式分布。

### 请求日志与失败回放
- chat_logs 表记录每次请求的问题、结果、证据/引用状态、延迟、token、成本、回答摘要与完整 trace。
- `GET /chat-logs?outcome=refused` 过滤失败案例，`GET /chat-logs/{id}` 回放完整执行轨迹。
- chat_metrics 指标表保持不含问题原文（隐私分层）。

### 用户反馈闭环
- 回答下方 👍/👎 一键反馈，`POST /chat-logs/{id}/feedback`。
- `/metrics/summary` 输出反馈量、正/负向数和满意度。

### 前端监控面板
- 指标带：请求量、回答率、错误率、P95 延迟、平均 token、累计成本、满意度。
- Token 与成本卡片：累计/Prompt/Completion token、按回答模式分布、成本行。
- 请求日志表：结果标签、延迟、token、反馈状态，行内展开回放执行轨迹。

### API 新增端点
```text
GET  /graph/overview                 图谱概览（实体/关系/类型分布）
GET  /graph/entities                 实体列表（类型/关键词过滤）
GET  /graph/relations                关系列表（按实体过滤）
GET  /graph/paths                    两实体间关系链（BFS，最多 4 跳）
POST /graph/rebuild                  全量重建图谱（operator/admin）
GET  /chat-logs                      请求日志（outcome 过滤，operator/admin）
GET  /chat-logs/{id}                 单条日志 + trace 回放（operator/admin）
POST /chat-logs/{id}/feedback        用户反馈（up/down + 备注）
```

鉴权约定（详见上方「安全与工程加固」）：所有端点接受 `X-User-Role`（viewer/operator/admin，默认 viewer）；
写操作与审计数据端点额外要求 operator/admin，`X-User-Id` 用于审批职责分离。

### 评测门禁
```text
scripts/evaluate_v4.py   实体/关系召回 >= 90%、结构检查 100%、图查询 P95 <= 150ms
scripts/evaluate_v5.py   观测闭环 8 项检查 100%、chat P95 <= 300ms
scripts/evaluate_v6.py   黄金集：decision>=90%、hybrid recall3>=75%、fact>=70%
```

> 墙钟类门禁（v2 P95<=200ms、v4 P95<=150ms）含本地 ONNX 推理/SQLite IO，
> 阈值按共享 CI runner 的波动预留了余量；算法级回退（N+1 检索、重复嵌入）仍会显著超标被拦截。

## V2 验收

```powershell
cd "D:\multi agents"
.\scripts\context-harness.ps1 -Mode verify
```

单独运行 V2 评测：

```powershell
python scripts\evaluate_v2.py
```

前端生产构建：

```powershell
cd "D:\multi agents\apps\web"
npm run build
```

## 前端工作台

启动后端：

```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

启动前端：

```bash
cd apps/web
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```


## V3 新功能

### 工单系统
- SQLite 工单表（tickets + pending_actions）
- 工单 CRUD API：`GET/POST/DELETE /tickets`
- 前端工单管理面板（状态标签、优先级标签、工单列表）

### 工具调用
- Tool Registry：4 个内置工具（query_tickets, get_ticket_detail, create_ticket, update_ticket_status）
- Tool Agent：根据问题自动判断是否需要工具调用
- 读操作（查询）立即执行，写操作（创建/更新）进入审批流程

### Human-in-the-loop
- 待审批操作队列：`GET /pending-actions` + `POST /pending-actions/{id}/approve`
- 前端审批按钮（批准/拒绝），问答结果中直接展示待审批操作
- 15 分钟有效期；批准后原子执行，拒绝/过期不写库，重复批准不重复执行

### V3 工程指标
- `GET /metrics/tools`：成功率、审批率、平均/P95 耗时、各工具/状态分布、重复执行违规
- `GET /tool-calls`：工具、角色、输入/结果摘要、最终状态、失败原因和耗时
- `scripts/evaluate_v3.py`：安全检查 100%、重复执行违规 0、工具 P95 <= 200 ms

### API 新增端点
```text
GET    /tickets                      工单列表
GET    /tickets/{ticket_id}          工单详情
POST   /tickets                      手动创建工单
DELETE /tickets/{ticket_id}          删除工单
GET    /pending-actions              待审批列表
POST   /pending-actions/{id}/approve 批准/拒绝操作
```

### 演示流程
```text
用户："客户A的项目为什么延期？要不要创建工单跟进？"
→ Router 分类 → Planner 生成 query → Retriever 检索文档
→ Tool Agent 检测到"创建工单"关键词 → 生成工单草稿
→ 返回回答 + 待审批操作
→ 用户在审批面板点击"批准" → 工单创建成功
```
