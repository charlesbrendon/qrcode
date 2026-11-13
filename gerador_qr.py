import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import qrcode
from PIL import Image, ImageTk


# ---------------------------------------------------------------------
# QR Studio — interface inspirada em Things, Craft, Linear e Notion
# Dependências: pip install qrcode[pil] pillow
# ---------------------------------------------------------------------

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(APP_DIR, "historico_qr.json")

# Paleta: azul-marinho, ciano discreto e superfícies neutras
C = {
    "nav": "#14243A",
    "nav_hover": "#203650",
    "nav_active": "#29435F",
    "accent": "#2786D9",
    "accent_hover": "#176FBD",
    "accent_soft": "#EAF4FE",
    "bg": "#F4F6F9",
    "surface": "#FFFFFF",
    "surface_alt": "#F8FAFC",
    "border": "#E4E9F0",
    "text": "#202B3C",
    "muted": "#718096",
    "subtle": "#A0ACBA",
    "danger": "#D84C4C",
    "danger_soft": "#FFF0F0",
    "success": "#23845B",
    "white": "#FFFFFF",
}

FONT = "Segoe UI"
QR_COLOR = "#14243A"
QR_SIZE = 300
MAX_HISTORY = 150


def generate_qr(data: str) -> Image.Image:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color=QR_COLOR, back_color="white").convert("RGB")


def load_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            items = json.load(file)
        if not isinstance(items, list):
            return []
        return [
            item for item in items
            if isinstance(item, dict) and isinstance(item.get("texto"), str)
        ][:MAX_HISTORY]
    except (OSError, json.JSONDecodeError):
        return []


def save_history(items):
    try:
        temp_file = HISTORY_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as file:
            json.dump(items, file, ensure_ascii=False, indent=2)
        os.replace(temp_file, HISTORY_FILE)
        return True
    except OSError:
        return False


class QRStudio:
    def __init__(self, root):
        self.root = root
        self.root.title("QR Studio")
        self.root.geometry("1080x760")
        self.root.minsize(900, 650)
        self.root.configure(bg=C["bg"])

        self.history = load_history()
        self.current_qr = None
        self.current_text = ""
        self.history_qr = None
        self.preview_photo = None
        self.history_photo = None
        self.active_page = "generator"
        self.history_selection = None

        self.setup_style()
        self.build_shell()
        self.build_generator()
        self.build_history()
        self.show_page("generator")

        self.root.bind("<Control-Return>", lambda _e: self.generate())
        self.root.bind("<Control-s>", lambda _e: self.save_current())
        self.root.bind("<Escape>", lambda _e: self.entry.focus_set())

    # ---------------------------- Base visual -------------------------
    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "History.Treeview",
            background=C["surface"],
            fieldbackground=C["surface"],
            foreground=C["text"],
            rowheight=38,
            borderwidth=0,
            font=(FONT, 10),
        )
        style.configure(
            "History.Treeview.Heading",
            background=C["surface_alt"],
            foreground=C["muted"],
            relief="flat",
            borderwidth=0,
            font=(FONT, 9, "bold"),
            padding=(10, 10),
        )
        style.map(
            "History.Treeview",
            background=[("selected", C["accent_soft"])],
            foreground=[("selected", C["text"])],
        )

    def build_shell(self):
        self.sidebar = tk.Frame(self.root, bg=C["nav"], width=224)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=C["nav"])
        brand.pack(fill="x", padx=22, pady=(25, 34))
        mark = tk.Label(
            brand, text="⌗", bg=C["accent"], fg=C["white"],
            font=(FONT, 19, "bold"), width=2, height=1,
        )
        mark.pack(side="left")
        brand_text = tk.Frame(brand, bg=C["nav"])
        brand_text.pack(side="left", padx=10)
        tk.Label(
            brand_text, text="QR Studio", bg=C["nav"], fg=C["white"],
            font=(FONT, 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_text, text="SIMPLES. RÁPIDO. SEU.", bg=C["nav"],
            fg="#91A4BA", font=(FONT, 7, "bold"),
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            self.sidebar, text="ESPAÇO DE TRABALHO", bg=C["nav"],
            fg="#8296AE", font=(FONT, 8, "bold"),
        ).pack(anchor="w", padx=23, pady=(0, 10))

        self.nav_buttons = {}
        self.nav_button("generator", "▦", "Gerador", self.show_generator)
        self.nav_button("history", "◷", "Histórico", self.show_history)

        tk.Frame(self.sidebar, bg="#2B3D53", height=1).pack(
            fill="x", padx=20, pady=20
        )
        tk.Label(
            self.sidebar, text="DICA RÁPIDA", bg=C["nav"], fg="#8296AE",
            font=(FONT, 8, "bold"),
        ).pack(anchor="w", padx=23, pady=(0, 7))
        tk.Label(
            self.sidebar,
            text="Use Ctrl + Enter para gerar\num QR Code e Ctrl + S para\nsalvar a imagem.",
            bg=C["nav"], fg="#B5C2D1", justify="left",
            font=(FONT, 9), pady=2,
        ).pack(anchor="w", padx=23)

        tk.Frame(self.sidebar, bg=C["nav"]).pack(fill="both", expand=True)
        tk.Label(
            self.sidebar, text="QR STUDIO  ·  1.0", bg=C["nav"],
            fg="#71869F", font=(FONT, 8),
        ).pack(anchor="w", padx=23, pady=(0, 8))
        tk.Label(
            self.sidebar, text="Feito para facilitar. by Charles Brendon", bg=C["nav"],
            fg="#A8B8C9", font=(FONT, 9),
        ).pack(anchor="w", padx=23, pady=(0, 22))

        self.main = tk.Frame(self.root, bg=C["bg"])
        self.main.pack(side="left", fill="both", expand=True)

        self.topbar = tk.Frame(
            self.main, bg=C["surface"], height=88,
            highlightbackground=C["border"], highlightthickness=1,
        )
        self.topbar.pack(fill="x")
        self.topbar.pack_propagate(False)

        title_area = tk.Frame(self.topbar, bg=C["surface"])
        title_area.pack(side="left", padx=32, pady=12)
        self.page_title = tk.Label(
            title_area, text="", bg=C["surface"], fg=C["text"],
            font=(FONT, 17, "bold"),
        )
        self.page_title.pack(anchor="w")
        self.page_subtitle = tk.Label(
            title_area, text="", bg=C["surface"], fg=C["muted"],
            font=(FONT, 9),
        )
        self.page_subtitle.pack(anchor="w", pady=(2, 0))

        self.page_area = tk.Frame(self.main, bg=C["bg"])
        self.page_area.pack(fill="both", expand=True, padx=30, pady=26)

        self.footer = tk.Frame(self.main, bg=C["bg"])
        self.footer.pack(fill="x", padx=32, pady=(0, 14))
        tk.Label(
            self.footer, text="Seus dados ficam armazenados localmente neste computador.",
            bg=C["bg"], fg=C["subtle"], font=(FONT, 8),
        ).pack(anchor="w")

    def nav_button(self, key, symbol, label, command):
        btn = tk.Frame(self.sidebar, bg=C["nav"], cursor="hand2")
        btn.pack(fill="x", padx=12, pady=2)
        accent = tk.Frame(btn, bg=C["nav"], width=3)
        accent.pack(side="left", fill="y")
        text = tk.Label(
            btn, text=f"  {symbol}    {label}", bg=C["nav"], fg="#C4D0DD",
            font=(FONT, 10), anchor="w", padx=12, pady=12, cursor="hand2",
        )
        text.pack(side="left", fill="x", expand=True)

        def click(_event=None):
            command()

        def enter(_event=None):
            if self.active_page != key:
                btn.configure(bg=C["nav_hover"])
                text.configure(bg=C["nav_hover"])

        def leave(_event=None):
            self.update_nav()

        for widget in (btn, text, accent):
            widget.bind("<Button-1>", click)
            widget.bind("<Enter>", enter)
            widget.bind("<Leave>", leave)
        self.nav_buttons[key] = (btn, accent, text)

    def update_nav(self):
        for key, (btn, accent, label) in self.nav_buttons.items():
            active = key == self.active_page
            bg = C["nav_active"] if active else C["nav"]
            btn.configure(bg=bg)
            label.configure(
                bg=bg, fg=C["white"] if active else "#C4D0DD",
                font=(FONT, 10, "bold" if active else "normal"),
            )
            accent.configure(bg=C["accent"] if active else C["nav"])

    def show_page(self, page):
        self.active_page = page
        for child in self.page_area.winfo_children():
            child.pack_forget()
        if page == "generator":
            self.generator_page.pack(fill="both", expand=True)
            self.page_title.configure(text="Gerador de QR Code")
            self.page_subtitle.configure(
                text="Transforme links, textos e informações em códigos QR."
            )
        else:
            self.history_page.pack(fill="both", expand=True)
            self.page_title.configure(text="Seu histórico")
            self.page_subtitle.configure(
                text="Encontre novamente os códigos que você já criou."
            )
            self.refresh_history()
        self.update_nav()

    def show_generator(self):
        self.show_page("generator")

    def show_history(self):
        self.show_page("history")

    # ------------------------------ Helpers --------------------------
    def card(self, parent, **kwargs):
        return tk.Frame(
            parent, bg=C["surface"], highlightbackground=C["border"],
            highlightthickness=1, **kwargs
        )

    def section_label(self, parent, text):
        tk.Label(
            parent, text=text, bg=C["surface"], fg=C["text"],
            font=(FONT, 10, "bold"),
        ).pack(anchor="w")

    def action_button(self, parent, text, command, primary=True, compact=False):
        bg = C["accent"] if primary else C["surface"]
        fg = C["white"] if primary else C["text"]
        active = C["accent_hover"] if primary else C["surface_alt"]
        btn = tk.Button(
            parent, text=text, command=command, bg=bg, fg=fg,
            activebackground=active, activeforeground=fg,
            relief="flat", bd=0, cursor="hand2",
            font=(FONT, 9, "bold"), padx=16 if compact else 20,
            pady=8 if compact else 11,
            highlightthickness=1 if not primary else 0,
            highlightbackground=C["border"],
        )
        btn.pack_propagate(False)
        return btn

    def show_empty_qr(self):
        self.qr_canvas.delete("all")
        self.qr_canvas.create_text(
            170, 145, text="⌗", fill="#C6D2DF", font=(FONT, 58),
        )
        self.qr_canvas.create_text(
            170, 205, text="Seu QR Code aparecerá aqui",
            fill=C["muted"], font=(FONT, 9),
        )

    def render_qr(self, canvas, image, size, attribute):
        rendered = image.resize((size - 34, size - 34), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(rendered)
        canvas.delete("all")
        canvas.create_image(size / 2, size / 2, image=photo)
        setattr(self, attribute, photo)

    # ------------------------------ Generator ------------------------
    def build_generator(self):
        self.generator_page = tk.Frame(self.page_area, bg=C["bg"])

        intro = tk.Frame(self.generator_page, bg=C["bg"])
        intro.pack(fill="x", pady=(0, 18))
        tk.Label(
            intro, text="O que vamos transformar em QR Code?",
            bg=C["bg"], fg=C["text"], font=(FONT, 12, "bold"),
        ).pack(anchor="w")
        tk.Label(
            intro, text="Cole um endereço, escreva uma mensagem ou informe um número.",
            bg=C["bg"], fg=C["muted"], font=(FONT, 9),
        ).pack(anchor="w", pady=(4, 0))

        content = tk.Frame(self.generator_page, bg=C["bg"])
        content.pack(fill="both", expand=True)

        left = tk.Frame(content, bg=C["bg"])
        left.pack(side="left", fill="both", expand=True, padx=(0, 16))

        input_card = self.card(left)
        input_card.pack(fill="x")
        input_inner = tk.Frame(input_card, bg=C["surface"])
        input_inner.pack(fill="x", padx=20, pady=20)

        self.section_label(input_inner, "CONTEÚDO")
        tk.Label(
            input_inner, text="Link, texto ou número", bg=C["surface"],
            fg=C["muted"], font=(FONT, 9),
        ).pack(anchor="w", pady=(15, 7))

        entry_wrap = tk.Frame(
            input_inner, bg=C["surface"], highlightbackground=C["border"],
            highlightthickness=1,
        )
        entry_wrap.pack(fill="x")
        self.entry = tk.Entry(
            entry_wrap, bg=C["surface"], fg=C["text"], insertbackground=C["accent"],
            relief="flat", bd=0, font=(FONT, 11),
        )
        self.entry.pack(fill="x", padx=12, pady=12)
        self.entry.bind("<Return>", lambda _e: self.generate())

        self.char_count = tk.Label(
            input_inner, text="0 caracteres", bg=C["surface"],
            fg=C["subtle"], font=(FONT, 8),
        )
        self.char_count.pack(anchor="e", pady=(5, 13))
        self.entry.bind("<KeyRelease>", self.update_char_count)

        buttons = tk.Frame(input_inner, bg=C["surface"])
        buttons.pack(fill="x")
        self.generate_btn = self.action_button(
            buttons, "Gerar QR Code  →", self.generate, primary=True
        )
        self.generate_btn.pack(side="left", fill="x", expand=True)
        self.clear_btn = self.action_button(
            buttons, "Limpar", self.clear_input, primary=False
        )
        self.clear_btn.pack(side="left", padx=(8, 0))

        hint = self.card(left)
        hint.pack(fill="x", pady=(14, 0))
        tk.Label(
            hint, text="✦  Dica", bg=C["surface"], fg=C["text"],
            font=(FONT, 9, "bold"),
        ).pack(anchor="w", padx=18, pady=(14, 4))
        tk.Label(
            hint,
            text="O código é gerado localmente. O conteúdo digitado não é enviado para nenhum servidor.",
            bg=C["surface"], fg=C["muted"], font=(FONT, 9),
            wraplength=390, justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 14))

        right = self.card(content)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(
            right, text="PRÉ-VISUALIZAÇÃO", bg=C["surface"], fg=C["muted"],
            font=(FONT, 8, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 8))

        preview_frame = tk.Frame(right, bg=C["surface_alt"])
        preview_frame.pack(fill="both", expand=True, padx=18, pady=(0, 14))
        self.qr_canvas = tk.Canvas(
            preview_frame, width=290, height=290, bg=C["surface_alt"],
            highlightthickness=0,
        )
        self.qr_canvas.pack(fill="both", expand=True, pady=5)
        self.show_empty_qr()

        self.result_label = tk.Label(
            right, text="Nenhum código gerado ainda", bg=C["surface"],
            fg=C["muted"], font=(FONT, 9),
        )
        self.result_label.pack(anchor="w", padx=20, pady=(0, 12))

        self.save_btn = self.action_button(
            right, "↓   Salvar imagem PNG", self.save_current, primary=False
        )
        self.save_btn.pack(fill="x", padx=18, pady=(0, 10))
        self.copy_btn = self.action_button(
            right, "Copiar conteúdo", self.copy_content, primary=True
        )
        self.copy_btn.pack(fill="x", padx=18, pady=(0, 18))
        self.set_result_actions(False)
        self.entry.focus_set()

    def update_char_count(self, _event=None):
        count = len(self.entry.get())
        self.char_count.configure(text=f"{count:,} caracteres".replace(",", "."))

    def set_result_actions(self, enabled):
        state = "normal" if enabled else "disabled"
        for btn in (self.save_btn, self.copy_btn):
            btn.configure(
                state=state,
                bg=(C["surface"] if btn == self.save_btn else C["accent"])
                if enabled else "#E9EDF2",
                fg=(C["text"] if btn == self.save_btn else C["white"])
                if enabled else C["subtle"],
                cursor="hand2" if enabled else "arrow",
            )

    def generate(self):
        data = self.entry.get().strip()
        if not data:
            messagebox.showinfo("Conteúdo necessário", "Digite um link, texto ou número para continuar.")
            self.entry.focus_set()
            return
        try:
            image = generate_qr(data)
        except Exception as exc:
            messagebox.showerror("Não foi possível gerar", f"O conteúdo não pôde ser convertido.\n\n{exc}")
            return

        self.current_qr = image
        self.current_text = data
        self.render_qr(self.qr_canvas, image, 290, "preview_photo")
        self.result_label.configure(
            text=f"✓  QR Code pronto  ·  {image.width} × {image.height} px",
            fg=C["success"],
        )
        self.set_result_actions(True)
        self.add_history(data)

    def clear_input(self):
        self.entry.delete(0, "end")
        self.update_char_count()
        self.entry.focus_set()

    def save_image(self, image, default_name):
        path = filedialog.asksaveasfilename(
            title="Salvar QR Code",
            defaultextension=".png",
            initialfile=default_name,
            filetypes=[("Imagem PNG", "*.png")],
        )
        if path:
            try:
                image.save(path, format="PNG")
                messagebox.showinfo("Imagem salva", f"QR Code salvo em:\n{path}")
            except OSError as exc:
                messagebox.showerror("Erro ao salvar", f"Não foi possível salvar a imagem.\n\n{exc}")

    def save_current(self):
        if self.current_qr:
            self.save_image(self.current_qr, "qrcode.png")

    def copy_content(self):
        if self.current_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_text)
            self.result_label.configure(text="✓  Conteúdo copiado para a área de transferência", fg=C["success"])

    # ------------------------------ History --------------------------
    def build_history(self):
        self.history_page = tk.Frame(self.page_area, bg=C["bg"])

        toolbar = tk.Frame(self.history_page, bg=C["bg"])
        toolbar.pack(fill="x", pady=(0, 16))
        left = tk.Frame(toolbar, bg=C["bg"])
        left.pack(side="left")
        tk.Label(
            left, text="Códigos recentes", bg=C["bg"], fg=C["text"],
            font=(FONT, 12, "bold"),
        ).pack(anchor="w")
        tk.Label(
            left, text="Selecione um item para visualizar ou salvar novamente.",
            bg=C["bg"], fg=C["muted"], font=(FONT, 9),
        ).pack(anchor="w", pady=(3, 0))

        self.history_count = tk.Label(
            toolbar, text="", bg=C["bg"], fg=C["muted"], font=(FONT, 9),
        )
        self.history_count.pack(side="right", anchor="s")

        body = tk.Frame(self.history_page, bg=C["bg"])
        body.pack(fill="both", expand=True)

        list_card = self.card(body)
        list_card.pack(side="left", fill="both", expand=True, padx=(0, 16))
        search_bar = tk.Frame(list_card, bg=C["surface"])
        search_bar.pack(fill="x", padx=16, pady=14)
        tk.Label(
            search_bar, text="⌕", bg=C["surface"], fg=C["muted"],
            font=(FONT, 16),
        ).pack(side="left", padx=(0, 8))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(
            search_bar, textvariable=self.search_var, relief="flat",
            bg=C["surface_alt"], fg=C["text"], insertbackground=C["accent"],
            font=(FONT, 10),
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=8)
        self.search_entry.insert(0, "Buscar no histórico...")
        self.search_entry.bind("<FocusIn>", self.clear_search_hint)
        self.search_entry.bind("<KeyRelease>", lambda _e: self.refresh_history())

        table_wrap = tk.Frame(list_card, bg=C["surface"])
        table_wrap.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        columns = ("content", "date")
        self.tree = ttk.Treeview(
            table_wrap, columns=columns, show="headings",
            style="History.Treeview", selectmode="browse",
        )
        self.tree.heading("content", text="CONTEÚDO")
        self.tree.heading("date", text="CRIADO EM")
        self.tree.column("content", width=300, anchor="w")
        self.tree.column("date", width=125, anchor="w", stretch=False)
        scrollbar = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.select_history)

        preview = self.card(body)
        preview.pack(side="left", fill="y")
        tk.Label(
            preview, text="PRÉ-VISUALIZAÇÃO", bg=C["surface"],
            fg=C["muted"], font=(FONT, 8, "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 10))
        self.history_canvas = tk.Canvas(
            preview, width=240, height=230, bg=C["surface_alt"],
            highlightthickness=0,
        )
        self.history_canvas.pack(padx=14)
        self.history_canvas.create_text(
            120, 115, text="Selecione um item", fill=C["muted"],
            font=(FONT, 9),
        )
        self.history_text = tk.Label(
            preview, text="Nenhum item selecionado", bg=C["surface"],
            fg=C["muted"], font=(FONT, 9), wraplength=220,
            justify="left", anchor="w",
        )
        self.history_text.pack(fill="x", padx=16, pady=(12, 14))

        self.history_save_btn = self.action_button(
            preview, "↓  Salvar PNG", self.save_history_item, primary=True
        )
        self.history_save_btn.pack(fill="x", padx=14, pady=(0, 8))
        self.history_delete_btn = self.action_button(
            preview, "Remover item", self.delete_history_item, primary=False
        )
        self.history_delete_btn.pack(fill="x", padx=14, pady=(0, 8))
        self.history_clear_btn = self.action_button(
            preview, "Limpar histórico", self.clear_history, primary=False
        )
        self.history_clear_btn.pack(fill="x", padx=14, pady=(0, 16))
        self.set_history_actions(False)

    def clear_search_hint(self, _event=None):
        if self.search_entry.get() == "Buscar no histórico...":
            self.search_entry.delete(0, "end")

    def add_history(self, data):
        self.history = [item for item in self.history if item["texto"] != data]
        self.history.insert(0, {
            "texto": data,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })
        self.history = self.history[:MAX_HISTORY]
        if not save_history(self.history):
            messagebox.showwarning(
                "Histórico", "O QR foi gerado, mas não foi possível salvar o histórico no disco."
            )
        if self.active_page == "history":
            self.refresh_history()

    def refresh_history(self):
        if not hasattr(self, "tree"):
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        query = self.search_var.get().strip().lower()
        if query == "buscar no histórico...":
            query = ""
        visible = 0
        for index, item in enumerate(self.history):
            content = item.get("texto", "")
            if query and query not in content.lower():
                continue
            preview = content.replace("\n", " ")
            if len(preview) > 43:
                preview = preview[:40] + "…"
            self.tree.insert(
                "", "end", iid=str(index),
                values=(preview, item.get("data", "—")),
            )
            visible += 1
        self.history_count.configure(
            text=f"{visible} de {len(self.history)} itens"
        )
        self.clear_history_preview()

    def clear_history_preview(self):
        self.history_selection = None
        self.history_qr = None
        self.history_canvas.delete("all")
        self.history_canvas.create_text(
            120, 115, text="Selecione um item", fill=C["muted"],
            font=(FONT, 9),
        )
        self.history_text.configure(text="Nenhum item selecionado")
        self.set_history_actions(False)

    def set_history_actions(self, enabled):
        for btn in (self.history_save_btn, self.history_delete_btn):
            btn.configure(
                state="normal" if enabled else "disabled",
                bg=(C["accent"] if btn == self.history_save_btn else C["surface"])
                if enabled else "#E9EDF2",
                fg=(C["white"] if btn == self.history_save_btn else C["text"])
                if enabled else C["subtle"],
                cursor="hand2" if enabled else "arrow",
            )
        self.history_clear_btn.configure(
            state="normal" if self.history else "disabled",
            bg=C["danger_soft"] if self.history else "#E9EDF2",
            fg=C["danger"] if self.history else C["subtle"],
            cursor="hand2" if self.history else "arrow",
        )

    def select_history(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        index = int(selection[0])
        item = self.history[index]
        self.history_selection = index
        self.history_qr = generate_qr(item["texto"])
        self.render_qr(
            self.history_canvas, self.history_qr, 230, "history_photo"
        )
        self.history_text.configure(
            text=f"{item['texto']}\n\nCriado em {item.get('data', 'data desconhecida')}",
            fg=C["text"],
        )
        self.set_history_actions(True)

    def save_history_item(self):
        if self.history_qr is not None and self.history_selection is not None:
            self.save_image(self.history_qr, "qrcode_historico.png")

    def delete_history_item(self):
        if self.history_selection is None:
            return
        del self.history[self.history_selection]
        save_history(self.history)
        self.refresh_history()

    def clear_history(self):
        if not self.history:
            return
        if not messagebox.askyesno(
            "Limpar histórico",
            "Isso removerá todos os itens salvos no histórico. Deseja continuar?",
        ):
            return
        self.history = []
        save_history(self.history)
        self.refresh_history()


if __name__ == "__main__":
    window = tk.Tk()
    app = QRStudio(window)
    window.mainloop()
