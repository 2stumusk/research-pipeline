"""
Research Pipeline - Simple GUI Launcher
使用 Tkinter 创建的简单图形界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from pathlib import Path
import threading
import subprocess
import sys


class ResearchPipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Pipeline - 研报分析系统")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # 项目根目录
        self.project_root = Path(__file__).parent

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建所有界面组件"""

        # ===== 标题栏 =====
        title_frame = tk.Frame(self.root, bg="#2C3E50", height=60)
        title_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            title_frame,
            text="📊 Research Pipeline",
            font=("Arial", 20, "bold"),
            bg="#2C3E50",
            fg="white"
        )
        title_label.pack(pady=15)

        # ===== 主容器 =====
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----- 文件选择区域 -----
        file_frame = tk.LabelFrame(main_frame, text="📁 研报文件", padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))

        # 选择目录
        dir_row = tk.Frame(file_frame)
        dir_row.pack(fill=tk.X, pady=5)

        tk.Label(dir_row, text="PDF 目录:", width=15, anchor='w').pack(side=tk.LEFT)
        self.dir_entry = tk.Entry(dir_row, width=50)
        self.dir_entry.pack(side=tk.LEFT, padx=5)
        self.dir_entry.insert(0, str(self.project_root / "inbox"))

        tk.Button(
            dir_row,
            text="浏览...",
            command=self.browse_directory,
            bg="#3498DB",
            fg="white",
            padx=15
        ).pack(side=tk.LEFT)

        # 文件列表
        self.file_list_label = tk.Label(
            file_frame,
            text="未选择文件",
            fg="gray",
            anchor='w'
        )
        self.file_list_label.pack(fill=tk.X, pady=5)

        # ----- 配置区域 -----
        config_frame = tk.LabelFrame(main_frame, text="⚙️ 配置", padx=10, pady=10)
        config_frame.pack(fill=tk.X, pady=(0, 10))

        # Provider 选择
        provider_row = tk.Frame(config_frame)
        provider_row.pack(fill=tk.X, pady=5)

        tk.Label(provider_row, text="LLM Provider:", width=15, anchor='w').pack(side=tk.LEFT)
        self.provider_var = tk.StringVar(value="mock")
        provider_combo = ttk.Combobox(
            provider_row,
            textvariable=self.provider_var,
            values=["mock", "claude", "openai"],
            state="readonly",
            width=20
        )
        provider_combo.pack(side=tk.LEFT, padx=5)

        tk.Label(
            provider_row,
            text="💡 Mock 模式无需 API Key",
            fg="green"
        ).pack(side=tk.LEFT, padx=10)

        # API Key
        key_row = tk.Frame(config_frame)
        key_row.pack(fill=tk.X, pady=5)

        tk.Label(key_row, text="API Key:", width=15, anchor='w').pack(side=tk.LEFT)
        self.key_entry = tk.Entry(key_row, width=40, show="*")
        self.key_entry.pack(side=tk.LEFT, padx=5)
        self.key_entry.insert(0, "mock-mode-no-key-needed")
        self.key_entry.config(state='disabled')

        # Provider 变化时更新 API Key 状态
        self.provider_var.trace('w', self.on_provider_change)

        # Deep Dive 数量
        deep_row = tk.Frame(config_frame)
        deep_row.pack(fill=tk.X, pady=5)

        tk.Label(deep_row, text="深度分析数量:", width=15, anchor='w').pack(side=tk.LEFT)
        self.deep_dive_var = tk.IntVar(value=10)
        deep_spin = tk.Spinbox(
            deep_row,
            from_=0,
            to=20,
            textvariable=self.deep_dive_var,
            width=10
        )
        deep_spin.pack(side=tk.LEFT, padx=5)

        # ----- 操作按钮 -----
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.run_button = tk.Button(
            button_frame,
            text="🚀 开始分析",
            command=self.run_analysis,
            bg="#27AE60",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=10
        )
        self.run_button.pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="📊 查看结果",
            command=self.open_results,
            bg="#3498DB",
            fg="white",
            font=("Arial", 12),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="⚙️ 打开配置",
            command=self.open_config,
            bg="#95A5A6",
            fg="white",
            font=("Arial", 12),
            padx=30,
            pady=10
        ).pack(side=tk.LEFT, padx=5)

        # ----- 进度区域 -----
        progress_frame = tk.LabelFrame(main_frame, text="📈 运行状态", padx=10, pady=10)
        progress_frame.pack(fill=tk.BOTH, expand=True)

        # 进度条
        self.progress = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 状态文本
        self.status_label = tk.Label(
            progress_frame,
            text="就绪",
            fg="green",
            font=("Arial", 10)
        )
        self.status_label.pack(anchor='w')

        # 日志输出
        self.log_text = scrolledtext.ScrolledText(
            progress_frame,
            height=15,
            wrap=tk.WORD,
            bg="#2C3E50",
            fg="#ECF0F1",
            font=("Courier", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        # 初始欢迎消息
        self.log("欢迎使用 Research Pipeline 研报分析系统！")
        self.log("=" * 60)
        self.log("📌 Mock 模式已启用，无需 API Key 即可测试")
        self.log("📌 选择研报目录，点击「开始分析」即可运行")
        self.log("=" * 60)

    def browse_directory(self):
        """浏览选择目录"""
        directory = filedialog.askdirectory(initialdir=self.dir_entry.get())
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
            self.update_file_list(directory)

    def update_file_list(self, directory):
        """更新文件列表"""
        pdf_files = list(Path(directory).glob("*.pdf"))
        if pdf_files:
            self.file_list_label.config(
                text=f"找到 {len(pdf_files)} 个 PDF 文件",
                fg="green"
            )
        else:
            self.file_list_label.config(
                text="未找到 PDF 文件",
                fg="orange"
            )

    def on_provider_change(self, *args):
        """Provider 变化时的处理"""
        provider = self.provider_var.get()
        if provider == "mock":
            self.key_entry.config(state='disabled')
            self.key_entry.delete(0, tk.END)
            self.key_entry.insert(0, "mock-mode-no-key-needed")
        else:
            self.key_entry.config(state='normal')
            self.key_entry.delete(0, tk.END)

    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def run_analysis(self):
        """运行分析"""
        # 禁用按钮
        self.run_button.config(state='disabled')
        self.status_label.config(text="运行中...", fg="orange")
        self.progress.start()

        # 清空日志
        self.log_text.delete(1.0, tk.END)

        # 在新线程中运行
        thread = threading.Thread(target=self._run_analysis_thread)
        thread.daemon = True
        thread.start()

    def _run_analysis_thread(self):
        """后台运行分析"""
        try:
            self.log("=" * 60)
            self.log("🚀 开始运行 Research Pipeline")
            self.log("=" * 60)

            # 构建命令
            cmd = [
                sys.executable,
                "-m",
                "research_pipeline",
                "demo"
            ]

            self.log(f"执行命令: {' '.join(cmd)}")
            self.log("")

            # 运行命令
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # 实时输出
            for line in process.stdout:
                self.log(line.rstrip())

            process.wait()

            if process.returncode == 0:
                self.log("")
                self.log("=" * 60)
                self.log("✅ 分析完成！")
                self.log("=" * 60)
                self.log("📊 输出目录: outputs/demo/")
                self.log("📊 点击「查看结果」打开 Dashboard")

                self.root.after(0, lambda: self.status_label.config(
                    text="分析完成 ✅",
                    fg="green"
                ))

                # 自动打开结果
                self.root.after(1000, self.open_results)

            else:
                self.log("")
                self.log("❌ 分析失败")
                self.root.after(0, lambda: self.status_label.config(
                    text="分析失败 ❌",
                    fg="red"
                ))

        except Exception as e:
            self.log(f"❌ 错误: {e}")
            self.root.after(0, lambda: self.status_label.config(
                text=f"错误: {e}",
                fg="red"
            ))

        finally:
            # 恢复按钮
            self.root.after(0, lambda: self.run_button.config(state='normal'))
            self.root.after(0, self.progress.stop)

    def open_results(self):
        """打开结果"""
        dashboard = self.project_root / "outputs/demo/dashboard.html"
        if dashboard.exists():
            import webbrowser
            webbrowser.open(str(dashboard))
            self.log(f"📊 已打开: {dashboard}")
        else:
            messagebox.showwarning(
                "未找到结果",
                "请先运行分析生成结果文件"
            )

    def open_config(self):
        """打开配置文件"""
        config_file = self.project_root / "config/config.yaml"
        if config_file.exists():
            if sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(config_file)])
            elif sys.platform == "win32":  # Windows
                subprocess.run(["notepad", str(config_file)])
            else:  # Linux
                subprocess.run(["xdg-open", str(config_file)])
            self.log(f"⚙️ 已打开配置文件: {config_file}")
        else:
            messagebox.showerror("错误", "配置文件不存在")


def main():
    """主函数"""
    root = tk.Tk()
    app = ResearchPipelineGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
