# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import os
import threading

import webview

from core.config_manager import load_config, save_config
from core.ruby_converter import text_file_to_paragraphs
from core.html_builder import build_html
from core.pdf_exporter import generate_pdf


APP_NAME = "Japanese Ruby PDF Generator"

preview_window = None
preview_started = False


def parse_px(value: str, default: int = 15) -> int:
    try:
        value = value.strip().lower().replace("px", "")
        return int(float(value))
    except Exception:
        return default


def parse_em(value: str, default: float = 0.48) -> float:
    try:
        value = value.strip().lower().replace("em", "")
        return float(value)
    except Exception:
        return default


class MainWindow:
    def __init__(self):
        self.config = load_config()

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("620x470")
        self.root.resizable(False, False)

        self.status_var = tk.StringVar(value="待机中")

        self.build_ui()

    def build_ui(self):
        tk.Label(self.root, text="入力 TXT ファイル").grid(
            row=0, column=0, padx=15, pady=(14, 4), sticky="w", columnspan=3
        )

        self.entry_input = tk.Entry(self.root, width=54)
        self.entry_input.grid(row=1, column=0, columnspan=2, padx=(15, 5), pady=4, sticky="w")

        tk.Button(self.root, text="参照", width=8, command=self.select_input_file).grid(
            row=1, column=2, padx=(5, 15), pady=4, sticky="w"
        )

        tk.Label(self.root, text="出力 PDF ファイル").grid(
            row=2, column=0, padx=15, pady=(12, 4), sticky="w", columnspan=3
        )

        self.entry_output = tk.Entry(self.root, width=54)
        self.entry_output.grid(row=3, column=0, columnspan=2, padx=(15, 5), pady=4, sticky="w")

        tk.Button(self.root, text="参照", width=8, command=self.select_output_file).grid(
            row=3, column=2, padx=(5, 15), pady=4, sticky="w"
        )

        tk.Label(self.root, text="正文大小").grid(
            row=4, column=0, padx=15, pady=(16, 4), sticky="w"
        )

        self.entry_body_font = tk.Entry(self.root, width=12)
        self.entry_body_font.grid(row=5, column=0, padx=15, pady=4, sticky="w")
        self.entry_body_font.insert(0, self.config["body_font_size"])

        tk.Label(self.root, text="页面内边距").grid(
            row=4, column=1, padx=15, pady=(16, 4), sticky="w"
        )

        self.entry_body_margin = tk.Entry(self.root, width=12)
        self.entry_body_margin.grid(row=5, column=1, padx=15, pady=4, sticky="w")
        self.entry_body_margin.insert(0, self.config["body_margin"])

        tk.Label(self.root, text="注音大小").grid(
            row=6, column=0, padx=15, pady=(8, 4), sticky="w"
        )

        self.entry_ruby_font = tk.Entry(self.root, width=12)
        self.entry_ruby_font.grid(row=7, column=0, padx=15, pady=4, sticky="w")
        self.entry_ruby_font.insert(0, self.config["ruby_font_size"])

        tk.Label(self.root, text="PDF 页边距").grid(
            row=6, column=1, padx=15, pady=(8, 4), sticky="w"
        )

        self.entry_page_margin = tk.Entry(self.root, width=12)
        self.entry_page_margin.grid(row=7, column=1, padx=15, pady=4, sticky="w")
        self.entry_page_margin.insert(0, self.config["page_margin"])

        tk.Label(self.root, text="行距").grid(
            row=8, column=0, padx=15, pady=(8, 4), sticky="w"
        )

        self.entry_line_height = tk.Entry(self.root, width=12)
        self.entry_line_height.grid(row=9, column=0, padx=15, pady=4, sticky="w")
        self.entry_line_height.insert(0, self.config["line_height"])

        preview_frame = tk.LabelFrame(self.root, text="字体预览")
        preview_frame.grid(row=8, column=1, columnspan=2, padx=15, pady=(8, 4), sticky="w")

        self.font_preview_ruby = tk.Label(
            preview_frame,
            text="にほんご　ぶんしょう　さんぷる",
            font=("Yu Mincho", max(6, int(parse_px(self.config["body_font_size"]) * parse_em(self.config["ruby_font_size"])))),
            fg="gray",
            anchor="center"
        )
        self.font_preview_ruby.pack(anchor="center", padx=10, pady=(8, 0))

        self.font_preview_main = tk.Label(
            preview_frame,
            text="日本語の文章サンプル",
            font=("Yu Mincho", parse_px(self.config["body_font_size"])),
            anchor="center"
        )
        self.font_preview_main.pack(anchor="center", padx=10, pady=(0, 8))

        self.entry_body_font.bind("<KeyRelease>", self.update_font_preview)
        self.entry_ruby_font.bind("<KeyRelease>", self.update_font_preview)

        tk.Button(self.root, text="刷新预览", width=14, height=2, command=self.show_preview).grid(
            row=10, column=0, padx=15, pady=22, sticky="w"
        )

        tk.Button(self.root, text="生成 PDF", width=14, height=2, command=self.run_generate).grid(
            row=10, column=1, padx=15, pady=22, sticky="w"
        )

        tk.Label(self.root, textvariable=self.status_var, anchor="w", fg="gray").grid(
            row=11, column=0, columnspan=3, padx=15, pady=(0, 10), sticky="we"
        )

    def collect_config_from_gui(self) -> dict:
        return {
            "body_font_size": self.entry_body_font.get().strip(),
            "ruby_font_size": self.entry_ruby_font.get().strip(),
            "line_height": self.entry_line_height.get().strip(),
            "body_margin": self.entry_body_margin.get().strip(),
            "page_margin": self.entry_page_margin.get().strip(),
        }

    def set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    def update_font_preview(self, event=None):
        body_size = parse_px(self.entry_body_font.get(), 15)
        ruby_ratio = parse_em(self.entry_ruby_font.get(), 0.48)
        ruby_size = max(6, int(body_size * ruby_ratio))

        self.font_preview_ruby.config(font=("Yu Mincho", ruby_size))
        self.font_preview_main.config(font=("Yu Mincho", body_size))

    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="选择 TXT 文件",
            filetypes=[("Text files", "*.txt")]
        )

        if file_path:
            self.entry_input.delete(0, tk.END)
            self.entry_input.insert(0, file_path)

            default_pdf = str(Path(file_path).with_suffix(".pdf"))
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, default_pdf)

            self.set_status("已选择输入文件")

    def select_output_file(self):
        file_path = filedialog.asksaveasfilename(
            title="选择输出 PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )

        if file_path:
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, file_path)
            self.set_status("已选择输出路径")

    def build_preview_html(self):
        input_path = self.entry_input.get().strip().strip('"')

        if not input_path:
            raise ValueError("请先选择输入 TXT 文件")

        txt_path = Path(input_path).resolve()

        if not txt_path.exists():
            raise FileNotFoundError(f"输入文件不存在：{txt_path}")

        cfg = self.collect_config_from_gui()
        content = text_file_to_paragraphs(txt_path)

        return build_html(content, cfg, preview=True), cfg

    def start_preview_window(self, initial_html: str):
        global preview_window, preview_started

        preview_window = webview.create_window(
            "Preview",
            html=initial_html,
            width=900,
            height=1000
        )

        preview_started = True
        webview.start()

    def show_preview(self):
        global preview_window, preview_started

        try:
            html_content, cfg = self.build_preview_html()
            save_config(cfg)

            if not preview_started:
                threading.Thread(
                    target=self.start_preview_window,
                    args=(html_content,),
                    daemon=True
                ).start()
                self.set_status("预览窗口已打开")
            else:
                if preview_window is not None:
                    preview_window.load_html(html_content)
                self.set_status("预览已刷新")

        except Exception as e:
            self.set_status("预览失败")
            messagebox.showerror("预览错误", str(e))

    def run_generate(self):
        input_path = self.entry_input.get().strip().strip('"')
        output_path = self.entry_output.get().strip().strip('"')

        if not input_path:
            messagebox.showerror("错误", "请选择输入 TXT 文件")
            return

        if not output_path:
            output_path = str(Path(input_path).with_suffix(".pdf"))
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, output_path)

        cfg = self.collect_config_from_gui()

        try:
            self.set_status("正在生成 PDF...")
            generate_pdf(input_path, output_path, cfg)
            save_config(cfg)

            self.set_status("生成完成")
            messagebox.showinfo("完成", f"PDF 已生成：\n{output_path}")

            if Path(output_path).exists():
                os.startfile(output_path)

        except Exception as e:
            self.set_status("生成失败")
            messagebox.showerror("错误", str(e))

    def run(self):
        self.root.mainloop()


def run_app():
    app = MainWindow()
    app.run()