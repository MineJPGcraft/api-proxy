import requests
import json
import sys
import os
import time
import threading
import logging
from flask import Flask, request, Response, jsonify

# --- 全局变量与线程锁 (保持不变) ---
CONFIG = {}
LOG_REQUESTS = True
GLOBAL_PROXY = None
HEADERS_TO_DROP = set()
FORCE_HEADER_OVERWRITE_GLOBAL = False
LAST_CONFIG_MTIME = 0
CONFIG_PATH = ''
CONFIG_LOCK = threading.Lock()

# --- 配置加载 (保持不变) ---
def load_config(is_reload=False):
    global CONFIG, LOG_REQUESTS, GLOBAL_PROXY, HEADERS_TO_DROP, FORCE_HEADER_OVERWRITE_GLOBAL, LAST_CONFIG_MTIME, CONFIG_PATH
    if not CONFIG_PATH:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        CONFIG_PATH = os.path.join(script_dir, 'config.json')

    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            new_config = json.load(f)
        with CONFIG_LOCK:
            CONFIG = new_config
            server_config = CONFIG.get('server', {})
            LOG_REQUESTS = server_config.get('log_requests', True)
            GLOBAL_PROXY = CONFIG.get('global_proxy')
            FORCE_HEADER_OVERWRITE_GLOBAL = CONFIG.get('force_header_overwrite', False)
            headers_list = CONFIG.get('headers_to_drop', [])
            HEADERS_TO_DROP = {h.lower() for h in headers_list}
            LAST_CONFIG_MTIME = os.path.getmtime(CONFIG_PATH)
        if is_reload:
            print(f"✅ [{time.strftime('%Y-%m-%d %H:%M:%S')}] 配置文件已成功重载。")
        return True
    except Exception as e:
        print(f"❌ 错误: 加载或重载配置文件 '{CONFIG_PATH}' 失败: {e}", file=sys.stderr)
        return False
        
def config_reloader_thread(interval):
    while True:
        try:
            time.sleep(interval)
            current_mtime = os.path.getmtime(CONFIG_PATH)
            if current_mtime > LAST_CONFIG_MTIME:
                load_config(is_reload=True)
        except Exception as e:
            print(f"❌ 自动重载线程发生错误: {e}", file=sys.stderr)
            
# --- Flask应用 (保持不变) ---
app = Flask(__name__)

# [ ... 这里是 proxy 和 root_handler 函数，与上一版完全相同，为简洁此处省略 ... ]
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    with CONFIG_LOCK:
        routes = CONFIG.get('routes', {})
        force_overwrite_global = FORCE_HEADER_OVERWRITE_GLOBAL
        log_requests_local = LOG_REQUESTS
        global_proxy_local = GLOBAL_PROXY
        headers_to_drop_local = HEADERS_TO_DROP

    route_key = path.split('/', 1)[0]
    target_config = routes.get(route_key)

    if not target_config or not target_config.get('enabled', True):
        return jsonify({"error": f"Route '{route_key}' not found or is disabled."}), 404
        
    is_universal = target_config.get('universal_proxy', False)
    
    if is_universal:
        try:
            final_target_url = path.split('/', 1)[1]
            if not (final_target_url.startswith('http://') or final_target_url.startswith('https://')):
                raise ValueError(f"Invalid target URL format: '{final_target_url}'.")
        except (IndexError, ValueError) as e:
            if log_requests_local: print(f"⚠️  万能路由错误: {e}")
            return jsonify({"error": str(e)}), 400
        params = None
    else:
        target_url = target_config.get('target_url')
        if not target_url:
            if log_requests_local: print(f"⚠️  标准路由'{route_key}'缺少'target_url'配置。")
            return jsonify({"error": f"Route '{route_key}' is missing 'target_url' configuration."}), 500
        full_path_without_query = request.path
        subpath = full_path_without_query.replace(f'/{route_key}', '', 1).lstrip('/')
        final_target_url = f"{target_url.rstrip('/')}/{subpath}"
        params = request.args.to_dict()

    if log_requests_local:
        log_prefix = "🔗 [万能]" if is_universal else "➡️ "
        print(f"⬇️  收到请求:      {request.method} {request.full_path}")
        print(f"{log_prefix} 路由 '{route_key}' 转发到: {final_target_url}")
        if params: print(f"   携带参数:     {params}")
    
    proxies_to_use = None
    route_proxy = target_config.get('proxy') 
    if route_proxy is not None:
        if route_proxy: proxies_to_use = {"http": route_proxy, "https": route_proxy}
    elif global_proxy_local:
        proxies_to_use = {"http": global_proxy_local, "https": global_proxy_local}
    if log_requests_local and proxies_to_use: print(f"   使用代理:     {proxies_to_use.get('https')}")

    forward_headers = { key: value for key, value in request.headers.items() if key.lower() not in headers_to_drop_local }
    forward_headers.pop('Host', None)
    
    custom_headers = target_config.get('custom_headers', {})
    if custom_headers:
        force_overwrite_policy = target_config.get('force_header_overwrite', force_overwrite_global)
        if log_requests_local: print("   --- Header 处理 ---")
        original_header_keys_lower = {k.lower() for k in forward_headers.keys()}
        for key, value in custom_headers.items():
            if key.lower() not in original_header_keys_lower:
                forward_headers[key] = value
                if log_requests_local: print(f"   ➕  添加Header:      '{key}'")
            elif force_overwrite_policy:
                forward_headers[key] = value
                if log_requests_local: print(f"   ❗️  强制覆盖Header:  '{key}'")
            else:
                if log_requests_local: print(f"   🔄  保留Header:      '{key}'")
        if log_requests_local: print("   -------------------")

    request_body = request.get_data()
    
    try:
        target_response = requests.request(method=request.method, url=final_target_url, params=params, headers=forward_headers, data=request_body, stream=True, timeout=180, allow_redirects=False, proxies=proxies_to_use)
    except requests.exceptions.RequestException as e:
        if log_requests_local: print(f"❌ 请求转发失败: {e}", file=sys.stderr)
        return jsonify({"error": "Proxy failed to connect to the target server."}), 502
    
    if log_requests_local: print(f"⬅️  响应状态:      {target_response.status_code}\n")
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    response_headers = [(key, value) for key, value in target_response.raw.headers.items() if key.lower() not in excluded_headers]
    return Response(target_response.iter_content(chunk_size=8192), status=target_response.status_code, headers=response_headers, content_type=target_response.headers.get('content-type'))

@app.route('/')
def root_handler():
    return jsonify({"message": "Python Proxy is running."})

if __name__ == '__main__':
    if not load_config(): sys.exit(1)
        
    if not LOG_REQUESTS:
        log = logging.getLogger('werkzeug')
        log.disabled = True

    server_config = CONFIG.get('server', {})
    listen_host = server_config.get('host', '0.0.0.0')
    listen_port = server_config.get('port', 3000)
    reload_interval = server_config.get('reload_interval', -1)

    # --- 核心修改：打造一个信息丰富的启动仪表盘 ---
    print("\n" + "="*50)
    print("🚀 高级功能代理服务已启动")
    print("="*50)

    print("\n[全局配置]")
    print(f"  - 监听地址: http://{listen_host}:{listen_port}")
    print(f"  - 请求日志: {'✅ 已开启' if LOG_REQUESTS else '❌ 已关闭'}")
    
    if reload_interval == -1:
        print("  - 配置热重载: ❌ 已禁用")
    elif reload_interval == 0:
        print("  - 配置热重载: ✅ 已开启 (实时监控)")
    else:
        print(f"  - 配置热重载: ✅ 已开启 (每 {reload_interval} 秒检查一次)")
        
    print(f"  - 全局Header策略: {'❗️ 强制覆盖' if FORCE_HEADER_OVERWRITE_GLOBAL else '🔄 优先客户端'}")
    
    if GLOBAL_PROXY:
        print(f"  - 全局转发代理: {GLOBAL_PROXY}")
        
    if HEADERS_TO_DROP:
        print(f"  - 移除客户端Header: {', '.join(CONFIG.get('headers_to_drop', []))}")

    print("\n[路由表]")
    configured_routes = CONFIG.get('routes', {})
    if not configured_routes:
        print("  - ⚠️  未配置任何路由。")
    else:
        for key, route_info in configured_routes.items():
            is_enabled = route_info.get('enabled', True)
            status_icon = "✅" if is_enabled else "❌"
            
            is_universal = route_info.get('universal_proxy', False)
            if is_universal:
                target_display = "[万能代理模式]"
            else:
                target_display = route_info.get('target_url', '[⚠️ 缺少目标URL]')
            
            # 构建一个包含特殊配置的标签列表
            tags = []
            route_overwrite = route_info.get('force_header_overwrite')
            if route_overwrite is True:
                tags.append("❗️ 强制覆盖Header")
            elif route_overwrite is False:
                tags.append("🔄 优先客户端Header")
                
            route_proxy = route_info.get('proxy')
            if route_proxy:
                tags.append(f"代理: {route_proxy}")

            tags_str = f"  ({', '.join(tags)})" if tags else ""
            
            print(f"  {status_icon} /{key} -> {target_display} {tags_str}")

    print("\n" + "="*50)
    print("...等待请求...\n")

    # 启动后台重载线程 (如果需要)
    if reload_interval >= 0:
        actual_interval = 1 if reload_interval == 0 else reload_interval
        reloader = threading.Thread(target=config_reloader_thread, args=(actual_interval,), daemon=True)
        reloader.start()
        
    app.run(host=listen_host, port=listen_port)
