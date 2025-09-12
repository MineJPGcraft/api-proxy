# 🚀 灵活的API代理服务器 (Dynamic API Proxy)

一个基于Python Flask构建的轻量级、高性能API代理服务器，提供可配置的路由、自定义Header注入、请求日志控制、热重载配置、万能转发模式以及HTTP/Socks5代理支持。特别适用于为第三方API（如OpenAI、Gemini等）提供统一入口、添加认证信息或进行流量整形。

## ✨ 主要功能

*   **多上游路由**: 根据请求URL的第一个路径段，智能地将请求转发到不同的上游服务器。
*   **Header注入与策略**:
    *   为每个上游路由配置自定义请求Header。
    *   支持“优先使用客户端Header”或“强制覆盖客户端Header”两种策略，可在全局或路由级别配置。
    *   可配置丢弃客户端请求中的特定Header（例如 `X-Real-Ip`）。
*   **配置热重载**: 无需重启服务即可动态更新 `config.json` 中的配置（基于文件修改时间戳检测）。
    *   支持禁用、实时监控（1秒间隔）或按指定秒数间隔检查。
*   **路由启用/禁用开关**: 灵活控制每个上游路由的可用性，无需修改或删除配置项。
*   **万能转发模式 (Universal Proxy)**: 启用后，路由路径中的剩余部分将直接作为目标URL，实现动态的任意目标转发，无需预设 `target_url`。
    *   示例: `http://localhost:3000/passthrough/https://www.google.com`
*   **代理支持**:
    *   支持配置全局HTTP/HTTPS/SOCKS5代理。
    *   也可为每个路由单独配置代理，路由级配置优先于全局配置。
*   **请求日志控制**: 可通过配置完全禁用请求日志输出，避免高并发下日志刷屏。
*   **命令行仪表盘**: 服务启动时显示清晰的全局配置和路由概览，一目了然。

## 📦 如何开始

### 1. 先决条件

*   Python 3.8+
*   `pip` (Python包管理器)

### 2. 安装

克隆仓库并安装依赖：

```bash
git clone https://github.com/ZhuYuxuan9302/api-proxy.git
cd 你的仓库名
pip install -r requirements.txt
```

**`requirements.txt` 文件内容:**

```
Flask
requests
```

### 3. 配置 `config.json`

在项目根目录下创建一个名为 `config.json` 的文件。请参考下方 `config.json` 示例（含所有配置项）部分。

### 4. 运行服务

```bash
python main.py
```

服务启动后，您将在控制台看到一个简洁的配置仪表盘。

## 📋 配置 `config.json`

`config.json` 是代理服务器的核心配置文件，允许您灵活定义其行为。

**完整的配置示例和详细说明请参见下方 `config.json` 示例（含所有配置项）**

这里简述关键配置项：

*   **`server`**: 服务器监听设置和通用行为。
    *   `host`: 监听地址 (默认 `0.0.0.0`)。
    *   `port`: 监听端口 (默认 `3000`)。
    *   `log_requests`: `true` 或 `false`，是否输出请求详情日志。
    *   `reload_interval`: 配置热重载间隔 (秒)。`-1` 禁用，`0` 实时监控（1秒检查），`>0` 指定间隔秒数。
*   **`global_proxy`**: 全局HTTP/SOCKS5代理设置，例如 `"http://user:pass@host:port"` 或 `"socks5://user:pass@host:port"`。
*   **`force_header_overwrite` (全局)**: `true` 或 `false`，所有路由默认的Header覆盖策略。
*   **`headers_to_drop`**: 一个字符串数组，列出需要从客户端请求中移除的Header名称（不区分大小写）。
*   **`routes`**: 定义所有上游路由的字典。每个键代表一个路由前缀（例如 `openai`）。
    *   **每个路由的配置项**:
        *   `enabled`: `true` (默认) 或 `false`，是否启用此路由。
        *   `target_url`: 目标上游服务器的基础URL。万能代理模式下忽略。
        *   `custom_headers`: 要为此路由添加的Header键值对。
        *   `force_header_overwrite`: `true` 或 `false`，此路由特有的Header覆盖策略，覆盖全局设置。
        *   `proxy`: 此路由独有的HTTP/SOCKS5代理，格式同 `global_proxy`。
        *   `universal_proxy`: `true` 或 `false`，是否启用万能代理模式。

## 💡 使用示例

假设您的代理服务运行在 `http://localhost:3000`。

### 1. 标准路由转发 (OpenAI)

`config.json` 中配置了 `/openai` 路由，并带有自定义 `Authorization` Header：

```json
{
  "routes": {
    "openai": {
      "target_url": "https://api.openai.com",
      "custom_headers": {
        "Authorization": "Bearer sk-xxxxxxxxxxxxxxxxxxxxxxxx"
      },
      "force_header_overwrite": true
    }
  }
}
```

**发送请求:**

```bash
curl http://localhost:3000/openai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "Hello!"}]
      }'
```
代理会将请求转发到 `https://api.openai.com/v1/chat/completions`，并**强制添加/覆盖** `Authorization` Header。

### 2. 万能路由转发 (Google)

`config.json` 中配置了 `/passthrough` 路由为万能代理模式：

```json
{
  "routes": {
    "passthrough": {
      "universal_proxy": true,
      "custom_headers": {
        "X-Proxy-By": "My Universal Proxy"
      }
    }
  }
}
```

**发送请求:**

```bash
# 访问 Google 首页
curl http://localhost:3000/passthrough/https://www.google.com

# 访问 GitHub 某个 API
# 注意：原始请求的查询参数 (eg: ?key=123) 会被保留并附加到最终目标URL
curl "http://localhost:3000/passthrough/https://api.github.com/users/octocat?extra_param=true" \
     -H "Accept: application/vnd.github.v3+json"
```

代理会将请求转发到您在URL中指定的 `https://www.google.com` 或 `https://api.github.com/users/octocat?extra_param=true`，并添加 `X-Proxy-By` Header。

### 3. 被禁用路由

`config.json` 中配置了 `/disabled_service` 路由但 `enabled: false`：

```json
{
  "routes": {
    "disabled_service": {
      "enabled": false,
      "target_url": "https://api.example.com"
    }
  }
}
```

**发送请求:**

```bash
curl http://localhost:3000/disabled_service/some/path
```
您将收到 `404 Not Found` 错误和 `{"error": "Route 'disabled_service' not found or is disabled."}` 响应，因为该路由已被禁用。

## 📚 高级配置

### 配置热重载

当 `server.reload_interval` 配置为 `> -1` 的值时，任何对 `config.json` 文件的修改都将在指定间隔后自动生效，无需重启 `main.py`。这对于生产环境中的动态管理非常有用。

### 代理支持

*   **全局代理**: 在 `config.json` 的根目录配置 `global_proxy`。
*   **路由级代理**: 在特定路由配置中添加 `proxy` 字段。
    *   例如：`"proxy": "http://user:password@10.0.0.1:8080"` 或 `"socks5://127.0.0.1:1080"`。

## ⚠️ 安全提示

*   **万能转发模式 (`universal_proxy`)**: 启用此功能会将您的代理服务器变成一个开放的代理，可以转发到互联网上的任何URL。**在生产环境中谨慎使用，并确保您的服务器受到适当的网络安全保护。**
*   **API Keys/Tokens**: 避免直接在 `config.json` 中硬编码敏感信息。建议使用环境变量或其他更安全的秘密管理方式（此版本代码未实现，需要进一步开发）。

## 📝 贡献

欢迎提交Issue或Pull Request来改进此项目。

## 📄 许可证

本项目采用 MIT 许可证
