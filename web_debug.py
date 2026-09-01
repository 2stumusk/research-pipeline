"""
Research Pipeline - 调试版 Web Dashboard
添加详细日志以排查问题
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser
import time

app = Flask(__name__)
PROJECT_ROOT = Path(__file__).parent

# 全局状态
running = False
completed = False
current_process = None

# 简化的 HTML 模板（用于调试）
DEBUG_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Research Pipeline - Debug</title>
    <style>
        body { font-family: Arial; padding: 20px; background: #f5f5f5; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }
        button { padding: 15px 30px; font-size: 16px; cursor: pointer; background: #4CAF50; color: white; border: none; border-radius: 5px; margin: 10px; }
        button:hover { background: #45a049; }
        #log { background: #222; color: #0f0; padding: 15px; border-radius: 5px; font-family: monospace; min-height: 200px; overflow-y: auto; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .status.running { background: #fff3cd; }
        .status.success { background: #d4edda; }
        .status.error { background: #f8d7da; }
    </style>
</head>
<body>
    <h1>📊 Research Pipeline - 调试模式</h1>

    <div class="card">
        <h2>状态</h2>
        <div id="status" class="status">就绪</div>
    </div>

    <div class="card">
        <h2>操作</h2>
        <button onclick="runDemo()">🚀 运行 Demo</button>
        <button onclick="checkStatus()">🔍 检查状态</button>
        <button onclick="openResults()">📊 查看结果</button>
        <button onclick="clearLog()">🗑️ 清空日志</button>
    </div>

    <div class="card">
        <h2>日志</h2>
        <div id="log"></div>
    </div>

    <script>
        function log(msg) {
            const logDiv = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logDiv.innerHTML += `[${time}] ${msg}<br>`;
            logDiv.scrollTop = logDiv.scrollHeight;
            console.log(msg);
        }

        function setStatus(msg, type) {
            const status = document.getElementById('status');
            status.textContent = msg;
            status.className = 'status ' + (type || '');
        }

        function runDemo() {
            log('🚀 发送运行请求...');
            setStatus('运行中...', 'running');

            fetch('/run-demo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(response => {
                log('✓ 收到响应: ' + response.status);
                return response.json();
            })
            .then(data => {
                log('✓ 数据: ' + JSON.stringify(data));
                if (data.status === 'started') {
                    log('✓ Demo 已启动，开始轮询状态...');
                    pollStatus();
                } else {
                    log('⚠ 状态: ' + data.message);
                    setStatus(data.message, 'error');
                }
            })
            .catch(error => {
                log('✗ 错误: ' + error);
                setStatus('错误: ' + error, 'error');
            });
        }

        function pollStatus() {
            const interval = setInterval(() => {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.completed) {
                            log('✅ Demo 完成！');
                            setStatus('完成', 'success');
                            clearInterval(interval);
                        } else if (!data.running) {
                            log('⚠ 运行停止');
                            setStatus('已停止', '');
                            clearInterval(interval);
                        } else {
                            log('⏳ 运行中...');
                        }
                    })
                    .catch(error => {
                        log('✗ 轮询错误: ' + error);
                        clearInterval(interval);
                    });
            }, 2000);
        }

        function checkStatus() {
            log('🔍 检查状态...');
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    log('状态: running=' + data.running + ', completed=' + data.completed);
                    if (data.running) {
                        setStatus('运行中', 'running');
                    } else if (data.completed) {
                        setStatus('已完成', 'success');
                    } else {
                        setStatus('就绪', '');
                    }
                })
                .catch(error => log('✗ 错误: ' + error));
        }

        function openResults() {
            log('📊 打开结果...');
            window.open('/results', '_blank');
        }

        function clearLog() {
            document.getElementById('log').innerHTML = '';
        }

        // 页面加载时显示欢迎信息
        window.onload = function() {
            log('✓ 页面加载完成');
            log('✓ 后端服务已连接');
            log('ℹ 点击「运行 Demo」开始测试');
        };
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """首页"""
    return render_template_string(DEBUG_HTML)

@app.route('/run-demo', methods=['POST'])
def run_demo():
    """运行 Demo"""
    global running, completed, current_process

    print("\n" + "="*70)
    print("收到运行请求")
    print("="*70)

    if running:
        print("❌ 任务已在运行")
        return jsonify({'status': 'already_running', 'message': '任务正在运行中'})

    running = True
    completed = False

    print("✓ 启动后台线程...")

    # 在后台线程中运行
    thread = threading.Thread(target=_run_demo_thread)
    thread.daemon = True
    thread.start()

    print("✓ 返回响应")
    return jsonify({'status': 'started', 'message': 'Demo 已启动'})

def _run_demo_thread():
    """后台运行 Demo"""
    global running, completed, current_process

    try:
        print("\n" + "="*70)
        print("🚀 开始运行 Demo")
        print("="*70 + "\n")

        cmd = [sys.executable, "-m", "research_pipeline", "demo"]
        print(f"命令: {' '.join(cmd)}")
        print(f"工作目录: {PROJECT_ROOT}")
        print()

        current_process = subprocess.Popen(
            cmd,
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # 实时输出
        for line in current_process.stdout:
            print(line.rstrip())

        current_process.wait()

        if current_process.returncode == 0:
            print("\n" + "="*70)
            print("✅ Demo 完成")
            print("="*70)
            completed = True
        else:
            print("\n❌ Demo 失败")
            print(f"退出代码: {current_process.returncode}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        running = False
        current_process = None

@app.route('/status')
def status():
    """获取状态"""
    return jsonify({
        'running': running,
        'completed': completed
    })

@app.route('/results')
def results():
    """查看结果"""
    dashboard = PROJECT_ROOT / "outputs/demo/dashboard.html"
    if dashboard.exists():
        return send_from_directory(
            str(PROJECT_ROOT / "outputs/demo"),
            "dashboard.html"
        )
    else:
        return "<h1>结果文件不存在</h1><p>请先运行 Demo</p>", 404

def open_browser(port):
    """自动打开浏览器"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    PORT = 8080

    print("="*70)
    print("🚀 Research Pipeline - 调试模式")
    print("="*70)
    print(f"📍 地址: http://localhost:{PORT}")
    print("🐛 调试日志已启用")
    print("⏹️  按 Ctrl+C 停止服务")
    print("="*70 + "\n")

    # 自动打开浏览器
    threading.Thread(target=lambda: open_browser(PORT), daemon=True).start()

    # 启动服务器（启用调试模式）
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)
