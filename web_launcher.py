"""
Research Pipeline - Web Dashboard Launcher
使用 Flask 创建本地 Web 界面，无需 tkinter
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser
import time

app = Flask(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# HTML 模板
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Pipeline - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .header h1 { color: #667eea; font-size: 32px; margin-bottom: 10px; }
        .header p { color: #666; font-size: 16px; }
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.08);
        }
        .card h2 {
            color: #333;
            font-size: 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .upload-area {
            border: 3px dashed #ddd;
            border-radius: 10px;
            padding: 60px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover { border-color: #667eea; background: #f8f9ff; }
        .upload-icon { font-size: 48px; margin-bottom: 15px; }
        .config-row { margin-bottom: 20px; }
        .config-row label {
            display: block;
            color: #555;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 8px;
        }
        .config-row select, .config-row input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
        }
        .btn {
            padding: 14px 30px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover { transform: translateY(-2px); }
        .btn-secondary { background: #f0f0f0; color: #333; }
        .btn-group { display: flex; gap: 15px; margin-top: 25px; }
        .log-output {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 300px;
            overflow-y: auto;
            line-height: 1.6;
        }
        .full-width { grid-column: 1 / -1; }
        .alert {
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .alert-success { background: #e8f5e9; color: #388e3c; }
        .alert-info { background: #e3f2fd; color: #1976d2; }
        .file-item {
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
        }
        @media (max-width: 768px) {
            .main-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Research Pipeline</h1>
            <p>智能研报分析系统 - Web Dashboard</p>
        </div>

        <div class="alert alert-success">
            <span style="font-size: 20px;">✅</span>
            <div><strong>服务已启动</strong><br>地址: http://localhost:5000</div>
        </div>

        <div class="main-grid">
            <div class="card">
                <h2><span>📁</span> 上传研报</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <input type="file" name="files" multiple accept=".pdf"
                           style="margin-bottom: 15px;" onchange="showFiles(this)">
                    <div id="fileList"></div>
                </form>
            </div>

            <div class="card">
                <h2><span>⚙️</span> 配置</h2>
                <div class="config-row">
                    <label>LLM Provider</label>
                    <select id="provider">
                        <option value="mock">Mock (无需 API Key)</option>
                        <option value="claude">Claude</option>
                        <option value="openai">OpenAI</option>
                    </select>
                </div>
                <div class="config-row">
                    <label>深度分析数量</label>
                    <input type="number" id="deepDive" value="10" min="0" max="20">
                </div>
                <div class="btn-group">
                    <button class="btn btn-primary" onclick="runDemo()">
                        <span>🚀</span> 运行 Demo
                    </button>
                    <button class="btn btn-secondary" onclick="openResults()">
                        <span>📊</span> 查看结果
                    </button>
                </div>
            </div>

            <div class="card full-width">
                <h2><span>⚡</span> 运行日志</h2>
                <div class="log-output" id="logOutput">
<span style="color: #48bb78;">●</span> 系统就绪
<span style="color: #4299e1;">ℹ</span> 使用 Mock 模式，无需 API Key
<span style="color: #4299e1;">ℹ</span> 点击「运行 Demo」开始分析
                </div>
            </div>
        </div>
    </div>

    <script>
        function showFiles(input) {
            const fileList = document.getElementById('fileList');
            const files = Array.from(input.files);
            fileList.innerHTML = files.map(f =>
                `<div class="file-item"><span>📄 ${f.name}</span></div>`
            ).join('');
        }

        function runDemo() {
            const logOutput = document.getElementById('logOutput');
            logOutput.innerHTML = '<span style="color: #48bb78;">●</span> 开始运行 Demo...\n';

            fetch('/run-demo', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        logOutput.innerHTML += '<span style="color: #4299e1;">ℹ</span> Demo 正在后台运行\n';
                        logOutput.innerHTML += '<span style="color: #4299e1;">ℹ</span> 请查看终端输出\n';
                        setTimeout(pollStatus, 2000);
                    }
                })
                .catch(err => {
                    logOutput.innerHTML += '<span style="color: #f56565;">✗</span> 错误: ' + err + '\n';
                });
        }

        function pollStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    const logOutput = document.getElementById('logOutput');
                    if (data.completed) {
                        logOutput.innerHTML += '<span style="color: #48bb78;">✓</span> Demo 完成！\n';
                        logOutput.innerHTML += '<span style="color: #4299e1;">ℹ</span> 点击「查看结果」打开 Dashboard\n';
                    } else {
                        setTimeout(pollStatus, 2000);
                    }
                });
        }

        function openResults() {
            window.open('/results', '_blank');
        }
    </script>
</body>
</html>
'''

# 全局状态
running = False
completed = False

@app.route('/')
def index():
    """首页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/run-demo', methods=['POST'])
def run_demo():
    """运行 Demo"""
    global running, completed

    if running:
        return jsonify({'status': 'already_running'})

    running = True
    completed = False

    # 在后台线程运行
    thread = threading.Thread(target=_run_demo_thread)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started'})

def _run_demo_thread():
    """后台运行 Demo"""
    global running, completed

    try:
        print("\n" + "="*60)
        print("🚀 开始运行 Research Pipeline Demo")
        print("="*60 + "\n")

        # 运行命令
        result = subprocess.run(
            [sys.executable, "-m", "research_pipeline", "demo"],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode == 0:
            print("\n" + "="*60)
            print("✅ Demo 完成！")
            print("="*60)
            print("📊 输出目录: outputs/demo/")
            print("📊 在浏览器中点击「查看结果」")
            completed = True
        else:
            print("\n❌ Demo 运行失败")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
    finally:
        running = False

@app.route('/status')
def status():
    """获取状态"""
    return jsonify({
        'running': running,
        'completed': completed
    })

@app.route('/results')
def results():
    """打开结果页面"""
    dashboard = PROJECT_ROOT / "outputs/demo/dashboard.html"
    if dashboard.exists():
        return send_from_directory(
            str(PROJECT_ROOT / "outputs/demo"),
            "dashboard.html"
        )
    else:
        return "结果文件不存在，请先运行 Demo", 404

def open_browser(port):
    """自动打开浏览器"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    # 使用端口 8080（避免与 AirPlay 冲突）
    PORT = 8080

    print("="*60)
    print("🚀 Research Pipeline Web Dashboard")
    print("="*60)
    print(f"📍 地址: http://localhost:{PORT}")
    print("🌐 浏览器将自动打开...")
    print("⏹️  按 Ctrl+C 停止服务")
    print("="*60 + "\n")

    # 自动打开浏览器
    threading.Thread(target=lambda: open_browser(PORT), daemon=True).start()

    # 启动服务器
    app.run(host='0.0.0.0', port=PORT, debug=False)
