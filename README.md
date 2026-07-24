# 🚂 Railway MCP Server (Remote)

通过SSE协议暴露Railway管理接口，让AI助手直接管理你的Railway项目。

## 部署到Railway

### 1. 获取API Token

1. 打开 https://railway.app/account/tokens
2. 点击 **New Token** → 选择 **Account Token**（完整权限）或 **Workspace Token**
3. 复制生成的Token（只显示一次！）

### 2. 连接GitHub部署

1. 打开 [Railway Dashboard](https://railway.app/dashboard)
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 选择 `qinwu611-lab/railway-mcp-server`
4. 在Variables页面添加：
   - `RAILWAY_API_TOKEN` = 你的token
5. 部署自动开始 ✅

### 3. 获取MCP URL

部署成功后：
- Railway会给一个 `*.railway.app` 域名
- MCP服务地址：`https://你的域名.railway.app/mcp`

### 4. 配置MCP客户端

```json
{
  "mcpServers": {
    "railway": {
      "url": "https://你的域名.railway.app/mcp"
    }
  }
}
```
