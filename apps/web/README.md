# Web 前端

这是 V1 的 React 前端工作台。

当前能力：

- 上传 `.txt` / `.md` / `.pdf` 文档。
- 查看已上传文档列表。
- 输入问题。
- 选择回答模式：`auto` / `local` / `api`。
- 展示回答和来源证据。

## 启动方式

先确保后端在运行：

```powershell
cd "D:\multi agents\apps\api"
uvicorn app.main:app --reload --port 8000
```

再启动前端：

```powershell
cd "D:\multi agents\apps\web"
npm install
npm run dev
```

访问：

```text
http://127.0.0.1:5173
```

## API 地址配置

默认连接：

```text
http://127.0.0.1:8000
```

如需修改，创建 `.env`：

```text
VITE_API_BASE_URL=http://127.0.0.1:8000
```
