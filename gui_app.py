#!/usr/bin/env python3
"""
Research Pipeline - 图形界面应用
简单的上传-分析-查看流程
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import sys
import json
import hashlib
import secrets
from pathlib import Path
import shutil
from datetime import datetime

# Import shared session validator
from research_pipeline.pipeline import validate_session_name

class ResearchPipelineGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Pipeline - 研报分析系统")
        self.root.geometry("800x600")

        self.project_root = Path(__file__).parent
        self.uploaded_files = []
        self.running = False
        self.last_output_dir = None
        self.last_dashboard = None

        self.create_widgets()

    def create_widgets(self):
        # 标题
        title = tk.Label(
            self.root,
            text="📊 Research Pipeline",
            font=("Arial", 24, "bold"),
            fg="#667eea"
        )
        title.pack(pady=20)

        subtitle = tk.Label(
            self.root,
            text="智能研报分析系统",
            font=("Arial", 14),
            fg="#666"
        )
        subtitle.pack()

        # 分隔线
        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill='x', pady=20, padx=20)

        # 步骤1：上传文件
        step1_frame = tk.Frame(self.root)
        step1_frame.pack(pady=10, padx=40, fill='x')

        step1_label = tk.Label(
            step1_frame,
            text="步骤 1：上传 PDF 研报",
            font=("Arial", 16, "bold")
        )
        step1_label.pack(anchor='w')

        btn_frame = tk.Frame(step1_frame)
        btn_frame.pack(pady=10, fill='x')

        self.upload_btn = tk.Button(
            btn_frame,
            text="📁 选择 PDF 文件",
            font=("Arial", 14),
            bg="#4CAF50",
            fg="white",
            padx=20,
            pady=10,
            command=self.upload_files
        )
        self.upload_btn.pack(side='left', padx=5)

        self.clear_btn = tk.Button(
            btn_frame,
            text="🗑️ 清空",
            font=("Arial", 14),
            bg="#f44336",
            fg="white",
            padx=20,
            pady=10,
            command=self.clear_files
        )
        self.clear_btn.pack(side='left', padx=5)

        # 文件列表
        self.file_list = tk.Listbox(
            step1_frame,
            height=6,
            font=("Arial", 12)
        )
        self.file_list.pack(fill='both', expand=True, pady=5)

        self.file_count_label = tk.Label(
            step1_frame,
            text="已选择 0 个文件",
            font=("Arial", 12),
            fg="#666"
        )
        self.file_count_label.pack(anchor='w', pady=5)

        # 步骤2：运行分析
        step2_frame = tk.Frame(self.root)
        step2_frame.pack(pady=10, padx=40, fill='x')

        step2_label = tk.Label(
            step2_frame,
            text="步骤 2：运行分析",
            font=("Arial", 16, "bold")
        )
        step2_label.pack(anchor='w')

        self.run_btn = tk.Button(
            step2_frame,
            text="🚀 开始分析",
            font=("Arial", 16, "bold"),
            bg="#667eea",
            fg="white",
            padx=30,
            pady=15,
            command=self.run_analysis,
            state='disabled'
        )
        self.run_btn.pack(pady=10)

        # 进度显示
        self.progress_label = tk.Label(
            step2_frame,
            text="",
            font=("Arial", 12),
            fg="#666"
        )
        self.progress_label.pack(pady=5)

        self.progress = ttk.Progressbar(
            step2_frame,
            mode='indeterminate',
            length=400
        )

        # 步骤3：查看结果
        step3_frame = tk.Frame(self.root)
        step3_frame.pack(pady=10, padx=40, fill='x')

        step3_label = tk.Label(
            step3_frame,
            text="步骤 3：查看结果",
            font=("Arial", 16, "bold")
        )
        step3_label.pack(anchor='w')

        self.result_btn = tk.Button(
            step3_frame,
            text="📊 查看分析报告",
            font=("Arial", 14),
            bg="#2196F3",
            fg="white",
            padx=20,
            pady=10,
            command=self.view_results,
            state='disabled'
        )
        self.result_btn.pack(pady=10)

        # 状态栏
        self.status_label = tk.Label(
            self.root,
            text="准备就绪",
            font=("Arial", 10),
            fg="#999",
            anchor='w'
        )
        self.status_label.pack(side='bottom', fill='x', padx=10, pady=5)

    def upload_files(self):
        files = filedialog.askopenfilenames(
            title="选择 PDF 文件",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )

        if files:
            for file in files:
                if file not in self.uploaded_files:
                    self.uploaded_files.append(file)
                    filename = Path(file).name
                    self.file_list.insert(tk.END, filename)

            self.update_file_count()
            self.run_btn['state'] = 'normal'
            self.status_label.config(text=f"已选择 {len(self.uploaded_files)} 个文件")

    def clear_files(self):
        self.uploaded_files.clear()
        self.file_list.delete(0, tk.END)
        self.update_file_count()
        self.run_btn['state'] = 'disabled'
        self.result_btn['state'] = 'disabled'
        self.status_label.config(text="已清空文件列表")

    def update_file_count(self):
        count = len(self.uploaded_files)
        self.file_count_label.config(text=f"已选择 {count} 个文件")

    def run_analysis(self):
        if not self.uploaded_files:
            messagebox.showwarning("警告", "请先上传 PDF 文件")
            return

        if self.running:
            messagebox.showinfo("提示", "分析正在进行中，请稍候")
            return

        # 确认对话框
        result = messagebox.askyesno(
            "确认",
            f"将分析 {len(self.uploaded_files)} 个 PDF 文件\n\n"
            "这可能需要几分钟时间，是否继续？"
        )

        if not result:
            return

        # 开始分析
        self.running = True
        self.run_btn['state'] = 'disabled'
        self.upload_btn['state'] = 'disabled'
        self.clear_btn['state'] = 'disabled'
        self.progress_label.config(text="正在分析...")
        self.progress.pack(pady=5)
        self.progress.start()
        self.status_label.config(text="分析进行中...")

        # 在后台线程运行
        thread = threading.Thread(target=self.run_analysis_thread)
        thread.daemon = True
        thread.start()

    def _generate_safe_session(self) -> str:
        """Generate a unique validated session name with random suffix."""
        now = datetime.now()
        suffix = secrets.token_hex(3)  # 6 lowercase hex chars
        session = f"gui-{now.strftime('%H%M%S')}-{suffix}"
        return session

    def _stage_files_safely(self, input_dir: Path, files: list[str]) -> list[Path]:
        """Stage files with collision detection using streamed SHA-256.

        Args:
            input_dir: Target directory for staging
            files: List of source file paths (must be regular .pdf files)

        Returns:
            List of staged file paths

        Raises:
            ValueError: If source path is invalid or collision cannot be resolved
        """
        input_dir.mkdir(parents=True, exist_ok=True)
        staged = []

        for file_path in files:
            src = Path(file_path).resolve()

            # Validate source: must exist, be a regular file, and have .pdf extension
            if not src.exists():
                raise ValueError(f"Source file does not exist: {src}")
            if not src.is_file():
                raise ValueError(f"Source is not a regular file: {src}")
            if src.suffix.lower() != ".pdf":
                raise ValueError(f"Source is not a PDF file: {src}")

            dest = input_dir / src.name

            # Check for existing file with same name
            if dest.exists():
                # Compute hash of source file using streaming to handle large files
                src_hash = self._compute_file_hash(src)
                dest_hash = self._compute_file_hash(dest)

                if src_hash != dest_hash:
                    # Different file, use collision suffix (first 8 hex chars)
                    dest = input_dir / f"{src.stem}-{src_hash[:8]}{src.suffix}"

                    # If collision suffix file already exists with different content, fail
                    if dest.exists():
                        dest_existing_hash = self._compute_file_hash(dest)
                        if dest_existing_hash != src_hash:
                            raise ValueError(
                                f"Cannot stage {src.name}: collision suffix already exists "
                                f"with different content"
                            )

            # Copy only if destination doesn't exist
            if not dest.exists():
                shutil.copy2(src, dest)

            staged.append(dest)

        return staged

    def _compute_file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file using streaming."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def _parse_cli_output(self, stdout: str, stderr: str, returncode: int) -> dict:
        """Parse CLI output JSON regardless of return code.

        Args:
            stdout: Standard output from CLI
            stderr: Standard error from CLI
            returncode: Process return code

        Returns:
            Dict with keys: success, output_dir, dashboard, is_partial, error_detail
        """
        output_dir = None
        dashboard = None
        status = None

        # Try to parse JSON from stdout
        try:
            output = json.loads(stdout)
            status = output.get("status")
            output_dir = output.get("output_dir")
            dashboard = output.get("dashboard")
        except (json.JSONDecodeError, ValueError):
            pass

        # Determine success: returncode 0, or partial with usable output_dir
        is_partial = status == "partial"
        success = returncode == 0 or (is_partial and output_dir)

        # If we have dashboard path, validate it
        if success and dashboard and output_dir:
            dashboard_path = Path(dashboard).resolve()
            output_dir_path = Path(output_dir).resolve()

            # Dashboard must exist and be under output_dir
            if not dashboard_path.exists():
                dashboard = None
            elif not self._is_subpath(dashboard_path, output_dir_path):
                dashboard = None  # Fail closed on unsafe path

        # Only consider viewable if we have a valid dashboard
        if success and not dashboard:
            success = False

        return {
            "success": success,
            "output_dir": output_dir,
            "dashboard": dashboard,
            "is_partial": is_partial,
            "error_detail": stderr[:200] if stderr else None,
        }

    def _is_subpath(self, child: Path, parent: Path) -> bool:
        """Check if child path is under parent path."""
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def run_analysis_thread(self):
        try:
            # Capture immutable snapshot in UI thread before starting
            files_snapshot = list(self.uploaded_files)
            today = datetime.now().strftime("%Y-%m-%d")
            session = self._generate_safe_session()

            # Validate session name
            if not validate_session_name(session):
                raise ValueError(f"Invalid session name: {session}")

            # Create unique input directory for this run
            input_dir = self.project_root / "inbox" / f"{today}-{session}"

            # Stage files safely with collision detection
            self.root.after(0, lambda: self.status_label.config(text="复制文件..."))
            staged_paths = self._stage_files_safely(input_dir, files_snapshot)

            # Run analysis with explicit input-dir
            self.root.after(0, lambda: self.status_label.config(text="运行分析..."))
            venv_python = self.project_root / ".venv" / "bin" / "python3"

            result = subprocess.run(
                [str(venv_python), "-m", "research_pipeline", "run",
                 "--date", today, "--session", session, "--input-dir", str(input_dir)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )

            # Parse JSON output regardless of return code
            parsed = self._parse_cli_output(result.stdout, result.stderr, result.returncode)

            self.root.after(
                0,
                self.analysis_complete,
                parsed["success"],
                parsed["output_dir"],
                parsed["dashboard"],
                parsed["is_partial"],
                parsed["error_detail"]
            )

        except Exception as e:
            self.root.after(0, self.analysis_error, str(e))

    def analysis_complete(self, success, output_dir=None, dashboard=None, is_partial=False, error_detail=None):
        self.running = False
        self.progress.stop()
        self.progress.pack_forget()
        self.run_btn['state'] = 'normal'
        self.upload_btn['state'] = 'normal'
        self.clear_btn['state'] = 'normal'

        if success and dashboard:
            # Store only the actual returned, resolved dashboard path
            self.last_output_dir = output_dir
            self.last_dashboard = dashboard

            if is_partial:
                # Partial success - show warning
                self.progress_label.config(text="⚠️ 分析完成（部分警告）")
                self.status_label.config(text="分析完成但有警告，点击查看结果")
                messagebox.showwarning("完成（有警告）",
                                       "分析完成但有部分警告。\n\n点击「查看分析报告」查看结果。")
            else:
                self.progress_label.config(text="✅ 分析完成！")
                self.status_label.config(text="分析完成，点击查看结果")
                messagebox.showinfo("完成", "分析完成！\n\n点击「查看分析报告」查看结果。")

            self.result_btn['state'] = 'normal'
        else:
            self.progress_label.config(text="❌ 分析失败")
            self.status_label.config(text="分析失败")
            detail = error_detail if error_detail else "请检查日志"
            messagebox.showerror("错误", f"分析过程出现错误\n\n{detail}")

    def analysis_error(self, error_msg):
        self.running = False
        self.progress.stop()
        self.progress.pack_forget()
        self.run_btn['state'] = 'normal'
        self.upload_btn['state'] = 'normal'
        self.clear_btn['state'] = 'normal'
        self.progress_label.config(text="❌ 分析失败")
        self.status_label.config(text="分析失败")
        messagebox.showerror("错误", f"分析失败：\n\n{error_msg}")

    def view_results(self):
        # Open only the actual returned, resolved dashboard path
        if self.last_dashboard:
            dashboard_path = Path(self.last_dashboard)
            if dashboard_path.exists():
                subprocess.run(["open", str(dashboard_path)])
                self.status_label.config(text="已打开结果报告")
                return

        messagebox.showwarning("警告", "未找到分析结果\n\n请先运行分析。")

def main():
    root = tk.Tk()
    app = ResearchPipelineGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
