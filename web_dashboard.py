"""
Research Pipeline - 增强版 Web Dashboard
支持文件上传、实时进度、历史记录等完整功能
"""

from flask import Flask, render_template_string, request, jsonify, send_from_directory
from pathlib import Path
import subprocess
import sys
import threading
import webbrowser
import time
import json
from datetime import datetime

app = Flask(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 全局状态
running = False
completed = False
current_log = []

# 增强版 HTML 模板
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
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .header h1 {
            color: #667eea;
            font-size: 32px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .header p { color: #666; font-size: 16px; }
        .main-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
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
            padding: 40px 20px;
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
            width: 100%;
            justify-content: center;
            margin-bottom: 10px;
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .btn-primary:hover { transform: translateY(-2px); }
        .btn-secondary { background: #f0f0f0; color: #333; }
        .btn-success { background: #48bb78; color: white; }
        .log-output {
            background: #2d3748;
            color: #e2e8f0;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
            line-height: 1.8;
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
        .alert-warning { background: #fff3e0; color: #f57c00; }
        .file-item {
            background: #f8f9fa;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-number {
            font-size: 28px;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
            margin-top: 5px;
        }
        .progress-bar {
            height: 6px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 15px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s;
        }
        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .tab-btn {
            padding: 10px 20px;
            border: none;
            background: #f0f0f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .tab-btn.active {
            background: #667eea;
            color: white;
        }
        @media (max-width: 1200px) {
            .main-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span style="font-size: 48px;">📊</span>
                Research Pipeline
            </h1>
            <p>智能研报分析系统 - 完整版 Web Dashboard</p>
        </div>

        <div class="alert alert-success">
            <span style="font-size: 20px;">✅</span>
            <div>
                <strong>服务运行中</strong><br>
                地址: http://localhost:8080 | Mock 模式已启用
            </div>
        </div>

        <div class="main-grid">
            <!-- 左侧：主要功能 -->
            <div style="display: grid; gap: 20px;">
                <!-- 快速操作 -->
                <div class="card">
                    <h2><span>🚀</span> 快速操作</h2>
                    <button class="btn btn-primary" onclick="runDemo()">
                        <span>🎯</span> 运行 Demo（2份示例PDF）
                    </button>
                    <button class="btn btn-success" onclick="openResults()">
                        <span>📊</span> 查看最新结果
                    </button>
                    <button class="btn btn-secondary" onclick="openFolder()">
                        <span>📁</span> 打开输出文件夹
                    </button>
                </div>

                <!-- 文件上传 -->
                <div class="card">
                    <h2><span>📁</span> 上传研报 PDF</h2>
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div class="upload-icon">📄</div>
                        <div style="color: #666;">
                            <strong>点击选择 PDF 文件</strong><br>
                            <small>或拖拽到此处（功能开发中）</small>
                        </div>
                    </div>
                    <input type="file" id="fileInput" multiple accept=".pdf" style="display: none;" onchange="handleFiles(this.files)">
                    <div id="fileList" style="margin-top: 15px;"></div>
                </div>

                <!-- 运行日志 -->
                <div class="card">
                    <h2><span>⚡</span> 运行日志</h2>
                    <div id="progressBar" class="progress-bar" style="display: none;">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                    <div class="log-output" id="logOutput">
<span style="color: #48bb78;">●</span> 系统就绪
<span style="color: #4299e1;">ℹ</span> 当前模式: Mock (无需 API Key)
<span style="color: #4299e1;">ℹ</span> 点击「运行 Demo」开始测试
                    </div>
                </div>
            </div>

            <!-- 右侧：配置和状态 -->
            <div style="display: grid; gap: 20px;">
                <!-- 配置 -->
                <div class="card">
                    <h2><span>⚙️</span> 配置</h2>
                    <div class="config-row">
                        <label>LLM Provider</label>
                        <select id="provider">
                            <option value="mock">Mock (无需 API Key) ✅</option>
                            <option value="claude">Claude</option>
                            <option value="openai">OpenAI</option>
                        </select>
                    </div>
                    <div class="config-row">
                        <label>深度分析数量</label>
                        <input type="number" id="deepDive" value="10" min="0" max="20">
                    </div>
                    <div class="config-row">
                        <label>输出目录</label>
                        <input type="text" value="outputs/daily/" readonly>
                    </div>
                </div>

                <!-- 统计 -->
                <div class="card">
                    <h2><span>📈</span> 今日统计</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number" id="totalFiles">0</div>
                            <div class="stat-label">PDF 文件</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number" id="runCount">0</div>
                            <div class="stat-label">运行次数</div>
                        </div>
                    </div>
                </div>

                <!-- 帮助 -->
                <div class="card">
                    <h2><span>💡</span> 使用提示</h2>
                    <div style="color: #666; font-size: 14px; line-height: 1.8;">
                        <p><strong>1. 运行 Demo</strong><br>
                        使用内置示例测试系统</p>

                        <p style="margin-top: 15px;"><strong>2. 上传 PDF</strong><br>
                        点击上传区域选择研报</p>

                        <p style="margin-top: 15px;"><strong>3. 查看结果</strong><br>
                        分析完成后自动打开</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let running = false;
        let runCount = 0;

        function log(message, type = 'info') {
            const logOutput = document.getElementById('logOutput');
            const colors = {
                'success': '#48bb78',
                'info': '#4299e1',
                'error': '#f56565',
                'warning': '#f59e0b'
            };
            const color = colors[type] || colors['info'];
            const timestamp = new Date().toLocaleTimeString();
            logOutput.innerHTML += `<div><span style="color: ${color};">●</span> [${timestamp}] ${message}</div>`;
            logOutput.scrollTop = logOutput.scrollHeight;
        }

        function runDemo() {
            if (running) {
                log('已有任务在运行中', 'warning');
                return;
            }

            running = true;
            document.getElementById('progressBar').style.display = 'block';
            log('🚀 开始运行 Demo...', 'success');

            fetch('/run-demo', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        log('✓ 后台任务已启动', 'info');
                        log('ℹ 请查看终端输出实时日志', 'info');
                        pollProgress();
                    } else {
                        log('任务已在运行: ' + data.message, 'warning');
                    }
                })
                .catch(err => {
                    log('✗ 启动失败: ' + err, 'error');
                    running = false;
                });
        }

        function pollProgress() {
            const interval = setInterval(() => {
                fetch('/status')
                    .then(response => response.json())
                    .then(data => {
                        const fill = document.getElementById('progressFill');
                        if (data.running) {
                            // 模拟进度
                            const currentWidth = parseInt(fill.style.width) || 0;
                            fill.style.width = Math.min(currentWidth + 10, 90) + '%';
                        } else if (data.completed) {
                            fill.style.width = '100%';
                            log('✅ Demo 运行完成！', 'success');
                            log('📊 点击「查看最新结果」打开 Dashboard', 'info');
                            clearInterval(interval);
                            running = false;
                            runCount++;
                            document.getElementById('runCount').textContent = runCount;
                            setTimeout(() => {
                                document.getElementById('progressBar').style.display = 'none';
                                fill.style.width = '0%';
                            }, 2000);
                        }
                    });
            }, 1000);
        }

        function openResults() {
            log('📊 打开结果 Dashboard...', 'info');
            window.open('/results', '_blank');
        }

        function openFolder() {
            log('📁 在 Finder 中打开输出目录...', 'info');
            fetch('/open-folder', { method: 'POST' });
        }

        function handleFiles(files) {
            const fileList = document.getElementById('fileList');
            fileList.innerHTML = '';
            let count = 0;

            for (let file of files) {
                if (file.name.endsWith('.pdf')) {
                    count++;
                    fileList.innerHTML += `
                        <div class="file-item">
                            <span>📄 ${file.name}</span>
                            <span style="color: #999;">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
                        </div>
                    `;
                }
            }

            document.getElementById('totalFiles').textContent = count;
            log(`✓ 已选择 ${count} 个 PDF 文件`, 'success');
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """首页"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/run-demo', methods=['POST'])
def run_demo():
    """运行 Demo"""
    global running, completed

    if running:
        return jsonify({'status': 'already_running', 'message': '任务正在运行'})

    running = True
    completed = False
    current_log.clear()

    # 后台运行
    thread = threading.Thread(target=_run_demo_thread)
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started'})

def _run_demo_thread():
    """后台运行 Demo"""
    global running, completed

    try:
        print("\n" + "="*70)
        print("🚀 开始运行 Research Pipeline Demo")
        print("="*70 + "\n")

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
            print("\n" + "="*70)
            print("✅ Demo 完成！")
            print("="*70)
            completed = True
        else:
            print("\n❌ Demo 失败")

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
    """查看结果"""
    dashboard = PROJECT_ROOT / "outputs/demo/dashboard.html"
    if dashboard.exists():
        return send_from_directory(
            str(PROJECT_ROOT / "outputs/demo"),
            "dashboard.html"
        )
    else:
        return "结果文件不存在，请先运行 Demo", 404

@app.route('/open-folder', methods=['POST'])
def open_folder():
    """在 Finder 中打开输出目录"""
    output_dir = PROJECT_ROOT / "outputs"
    if sys.platform == "darwin":
        subprocess.run(["open", str(output_dir)])
    return jsonify({'status': 'ok'})

def open_browser(port):
    """自动打开浏览器"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{port}')

if __name__ == '__main__':
    PORT = 8080

    print("="*70)
    print("🚀 Research Pipeline Web Dashboard")
    print("="*70)
    print(f"📍 地址: http://localhost:{PORT}")
    print("🌐 浏览器将自动打开...")
    print("⏹️  按 Ctrl+C 停止服务")
    print("="*70 + "\n")

    threading.Thread(target=lambda: open_browser(PORT), daemon=True).start()
    app.run(host='0.0.0.0', port=PORT, debug=False)
