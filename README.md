# 🚀 Python API Proxy

一个功能强大、高度可配置的大模型 API 代理服务，支持多路由转发、自定义 Header、反向代理适配等特性。

## ✨ 特性

- 🔀 **多路由转发** - 单一服务代理多个 API 端点
- 🎯 **Base Path 支持** - 完美适配 Nginx 等反向代理场景，支持任意层级路径
- 🔑 **自定义 Header** - 为每个路由配置独立的认证信息
- ⚡ **Header 覆盖策略** - 灵活控制客户端 Header 与配置 Header 的优先级
- 🌐 **代理支持** - 全局代理与路由级代理配置
- 🔄 **配置热重载** - 无需重启即可更新配置
- 📝 **请求日志** - 可开关的详细请求日志
- 🗑️ **Header 过滤** - 移除指定的客户端 Header
- 🌍 **万能代理模式** - 支持动态目标 URL
- 📡 **流式响应** - 完整支持 SSE 流式传输

## 📦 安装

### 依赖

```bash
pip install flask requests
```

### 文件结构

```
your-project/
├── proxy.py        # 主程序
└── config.json     # 配置文件
```

## ⚙️ 配置文件

### 完整配置示例

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3000,
    "log_requests": true,
    "reload_interval": 5,
    "base_path": ""
  },
  "global_proxy": null,
  "force_header_overwrite": false,
  "headers_to_drop": ["x-forwarded-for", "x-real-ip"],
  
  "routes": {
    "openai": {
      "enabled": true,
      "target_url": "https://api.openai.com",
      "proxy": null,
      "force_header_overwrite": false,
      "custom_headers": {
        "Authorization": "Bearer sk-xxxx"
      }
    }
  }
}
```

### 配置项详解

#### `server` - 服务器配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | string | `"0.0.0.0"` | 监听地址 |
| `port` | number | `3000` | 监听端口 |
| `log_requests` | boolean | `true` | 是否输出请求日志 |
| `reload_interval` | number | `-1` | 配置热重载间隔（秒）<br>`-1`: 禁用<br>`0`: 实时监控（1秒）<br>`>0`: 指定间隔 |
| `base_path` | string | `""` | 基础路径前缀，用于反代场景<br>支持多级路径如 `/api/v1` |

#### 全局配置

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `global_proxy` | string/null | `null` | 全局转发代理<br>格式: `http://host:port` 或 `socks5://host:port` |
| `force_header_overwrite` | boolean | `false` | 全局 Header 覆盖策略<br>`true`: 配置优先<br>`false`: 客户端优先 |
| `headers_to_drop` | array | `[]` | 要移除的客户端 Header 列表 |

#### `routes` - 路由配置

每个路由的 key 作为访问路径的第一段。

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `enabled` | boolean | 否 | 是否启用，默认 `true` |
| `target_url` | string | 是* | 目标 API 地址 |
| `universal_proxy` | boolean | 否 | 万能代理模式，默认 `false` |
| `proxy` | string/null | 否 | 路由专用代理<br>`null`: 使用全局代理<br>`""`: 不使用代理<br>`"http://..."`: 指定代理 |
| `force_header_overwrite` | boolean | 否 | 路由级 Header 覆盖策略，覆盖全局设置 |
| `custom_headers` | object | 否 | 自定义请求 Header |

\* 当 `universal_proxy: true` 时不需要 `target_url`

## 🚀 启动

```bash
python proxy.py
```

启动后会显示详细的配置信息：

```
============================================================
🚀 高级功能代理服务已启动
============================================================

[全局配置]
  - 监听地址: http://0.0.0.0:3000
  - 基础路径 (base_path): /api/v1
    → 前端反代示例: https://your-domain.com/api/v1/openai/v1/chat/completions
  - 请求日志: ✅ 已开启
  - 配置热重载: ✅ 已开启 (每 5 秒检查一次)
  - 全局Header策略: 🔄 优先客户端

[路由表]
  ✅ /api/v1/openai -> https://api.openai.com
  ✅ /api/v1/anthropic -> https://api.anthropic.com
  ❌ /api/v1/disabled-route -> https://example.com  (已禁用)

============================================================
...等待请求...
```

## 📖 使用示例

### 基础用法

#### 配置

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 3000
  },
  "routes": {
    "openai": {
      "enabled": true,
      "target_url": "https://api.openai.com",
      "custom_headers": {
        "Authorization": "Bearer sk-xxxx"
      }
    }
  }
}
```

#### 请求

```bash
# 原始请求
curl https://api.openai.com/v1/chat/completions

# 通过代理
curl http://localhost:3000/openai/v1/chat/completions
```

### 多个 API 服务

```json
{
  "routes": {
    "openai": {
      "enabled": true,
      "target_url": "https://api.openai.com",
      "custom_headers": {
        "Authorization": "Bearer sk-openai-xxxx"
      }
    },
    "anthropic": {
      "enabled": true,
      "target_url": "https://api.anthropic.com",
      "custom_headers": {
        "x-api-key": "sk-ant-xxxx",
        "anthropic-version": "2023-06-01"
      }
    },
    "gemini": {
      "enabled": true,
      "target_url": "https://generativelanguage.googleapis.com",
      "custom_headers": {
        "x-goog-api-key": "your-gemini-key"
      }
    },
    "deepseek": {
      "enabled": true,
      "target_url": "https://api.deepseek.com",
      "custom_headers": {
        "Authorization": "Bearer sk-deepseek-xxxx"
      }
    }
  }
}
```

```bash
# OpenAI
curl http://localhost:3000/openai/v1/chat/completions

# Anthropic Claude
curl http://localhost:3000/anthropic/v1/messages

# Google Gemini
curl http://localhost:3000/gemini/v1beta/models/gemini-pro:generateContent

# DeepSeek
curl http://localhost:3000/deepseek/v1/chat/completions
```

### 反向代理场景 (Base Path)

当服务部署在 Nginx 等反向代理后面时：

#### Nginx 配置

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;
    
    location /byok/ {
        proxy_pass http://127.0.0.1:3000/byok/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
    }
}
```

#### 代理配置

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 3000,
    "base_path": "/byok"
  },
  "routes": {
    "openai": {
      "enabled": true,
      "target_url": "https://api.openai.com"
    }
  }
}
```

#### 请求流程

```
用户请求:
  https://api.example.com/byok/openai/v1/chat/completions
                    ↓ Nginx
程序收到:
  /byok/openai/v1/chat/completions
                    ↓ 剥离 base_path
有效路径:
  openai/v1/chat/completions
                    ↓ 路由匹配
转发到:
  https://api.openai.com/v1/chat/completions
```

#### 多级 Base Path

支持任意层级的路径前缀：

```json
{
  "server": {
    "base_path": "/api/v1/proxy"
  }
}
```

```bash
curl https://example.com/api/v1/proxy/openai/v1/chat/completions
```

### Header 覆盖策略

控制当客户端 Header 与配置 Header 冲突时的行为。

#### 全局优先客户端（默认）

```json
{
  "force_header_overwrite": false,
  "routes": {
    "openai": {
      "target_url": "https://api.openai.com",
      "custom_headers": {
        "Authorization": "Bearer sk-default-key"
      }
    }
  }
}
```

```bash
# 使用配置中的 key
curl http://localhost:3000/openai/v1/models

# 使用自己的 key（客户端优先）
curl -H "Authorization: Bearer sk-my-key" http://localhost:3000/openai/v1/models
```

#### 全局强制覆盖

```json
{
  "force_header_overwrite": true
}
```

所有请求都将使用配置中的 Header，忽略客户端提供的。

#### 路由级覆盖

```json
{
  "force_header_overwrite": false,
  "routes": {
    "public-api": {
      "target_url": "https://api.openai.com",
      "force_header_overwrite": false,
      "custom_headers": {
        "Authorization": "Bearer sk-default"
      }
    },
    "private-api": {
      "target_url": "https://api.openai.com",
      "force_header_overwrite": true,
      "custom_headers": {
        "Authorization": "Bearer sk-fixed-key"
      }
    }
  }
}
```

### 代理配置

#### 全局代理

所有路由默认使用此代理：

```json
{
  "global_proxy": "http://127.0.0.1:7890"
}
```

#### 路由专用代理

```json
{
  "global_proxy": "http://127.0.0.1:7890",
  "routes": {
    "openai": {
      "target_url": "https://api.openai.com",
      "proxy": "http://us-proxy.example.com:8080"
    },
    "domestic-api": {
      "target_url": "https://api.domestic.com",
      "proxy": ""
    }
  }
}
```

| `proxy` 值 | 行为 |
|------------|------|
| 未设置/`null` | 使用全局代理 |
| `""` (空字符串) | 不使用代理（直连） |
| `"http://..."` | 使用指定代理 |

#### 支持的代理协议

```json
"proxy": "http://host:port"
"proxy": "https://host:port"
"proxy": "socks5://host:port"
"proxy": "socks5://user:pass@host:port"
```

### 万能代理模式

动态指定目标 URL，适用于需要代理任意地址的场景：

```json
{
  "routes": {
    "proxy": {
      "enabled": true,
      "universal_proxy": true
    }
  }
}
```

```bash
# 代理任意 HTTPS 地址
curl http://localhost:3000/proxy/https://api.example.com/v1/endpoint

# 代理任意 HTTP 地址
curl http://localhost:3000/proxy/http://internal-api.local/data
```

**格式**: `/{route_key}/{protocol}://{target_host}/{path}`

### Header 过滤

移除客户端发送的特定 Header：

```json
{
  "headers_to_drop": [
    "x-forwarded-for",
    "x-real-ip",
    "cf-connecting-ip",
    "x-forwarded-proto"
  ]
}
```

常用于：
- 隐藏客户端真实 IP
- 移除 CDN 添加的 Header
- 清理不必要的元数据

### 配置热重载

```json
{
  "server": {
    "reload_interval": 5
  }
}
```

| 值 | 行为 |
|----|------|
| `-1` | 禁用热重载 |
| `0` | 实时监控（每秒检查） |
| `>0` | 指定检查间隔（秒） |

修改 `config.json` 后无需重启服务，配置会自动生效。

## 📡 API 端点

### `GET /`

健康检查端点。

**响应:**
```json
{
  "message": "Python Proxy is running.",
  "base_path": "/api/v1"
}
```

### `* /<path>`

代理转发端点，支持所有 HTTP 方法。

## 🔧 完整配置示例

### 生产环境配置

```json
{
  "server": {
    "host": "127.0.0.1",
    "port": 3000,
    "log_requests": false,
    "reload_interval": 30,
    "base_path": "/api/llm"
  },
  "global_proxy": null,
  "force_header_overwrite": false,
  "headers_to_drop": [
    "x-forwarded-for",
    "x-real-ip",
    "cf-connecting-ip"
  ],
  
  "routes": {
    "openai": {
      "enabled": true,
      "target_url": "https://api.openai.com",
      "custom_headers": {
        "Authorization": "Bearer sk-openai-xxxx"
      }
    },
    "openai-azure": {
      "enabled": true,
      "target_url": "https://your-resource.openai.azure.com",
      "custom_headers": {
        "api-key": "your-azure-key"
      }
    },
    "anthropic": {
      "enabled": true,
      "target_url": "https://api.anthropic.com",
      "force_header_overwrite": true,
      "custom_headers": {
        "x-api-key": "sk-ant-xxxx",
        "anthropic-version": "2023-06-01"
      }
    },
    "gemini": {
      "enabled": true,
      "target_url": "https://generativelanguage.googleapis.com",
      "proxy": "http://us-proxy:8080",
      "custom_headers": {
        "x-goog-api-key": "your-gemini-key"
      }
    },
    "ollama": {
      "enabled": true,
      "target_url": "http://localhost:11434",
      "proxy": ""
    }
  }
}
```

### BYOK (Bring Your Own Key) 配置

允许用户使用自己的 API Key：

```json
{
  "server": {
    "base_path": "/byok"
  },
  "force_header_overwrite": false,
  "routes": {
    "openai": {
      "enabled": true,
      "target_url": "https://api.openai.com"
    },
    "anthropic": {
      "enabled": true,
      "target_url": "https://api.anthropic.com",
      "custom_headers": {
        "anthropic-version": "2023-06-01"
      }
    }
  }
}
```

用户请求时需自带 API Key：

```bash
curl -H "Authorization: Bearer sk-user-key" \
  https://example.com/byok/openai/v1/chat/completions
```

### 内部服务聚合

```json
{
  "routes": {
    "user-service": {
      "enabled": true,
      "target_url": "http://user-service.internal:8080",
      "proxy": ""
    },
    "order-service": {
      "enabled": true,
      "target_url": "http://order-service.internal:8080",
      "proxy": ""
    },
    "external-api": {
      "enabled": true,
      "target_url": "https://api.external.com",
      "proxy": "http://egress-proxy:3128"
    }
  }
}
```

## ❓ 常见问题

### Q: 流式响应 (SSE) 是否支持？

A: 支持。程序使用 `stream=True` 和 chunked 传输，完整支持 OpenAI、Anthropic 等的流式响应。

### Q: 超时时间如何配置？

A: 当前硬编码为 180 秒。如需修改，可在代码中搜索 `timeout=180` 进行调整。

### Q: 如何部署到生产环境？

A: 推荐使用 Gunicorn 或 uWSGI：

```bash
# Gunicorn
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:3000 proxy:app

# 配合 systemd
[Unit]
Description=API Proxy Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/proxy
ExecStart=/usr/bin/gunicorn -w 4 -b 127.0.0.1:3000 proxy:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Q: 配置热重载时会丢失请求吗？

A: 不会。热重载使用线程锁保护，配置更新是原子操作。

### Q: base_path 可以为空吗？

A: 可以。不设置或设为空字符串时，程序按原始逻辑工作，不做路径前缀处理。

## 📝 日志示例

```
⬇️  收到请求:      POST /api/v1/openai/v1/chat/completions?
   剥离前缀:      '/api/v1' -> 有效路径: 'openai/v1/chat/completions'
➡️  路由 'openai' 转发到: https://api.openai.com/v1/chat/completions
   使用代理:     http://127.0.0.1:7890
   --- Header 处理 ---
   ➕  添加Header:      'Authorization'
   🔄  保留Header:      'Content-Type'
   -------------------
⬅️  响应状态:      200
```

## 📄 License

MIT License

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！
```