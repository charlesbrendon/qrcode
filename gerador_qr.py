import json
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox

import qrcode
from PIL import Image, ImageTk

ARQUIVO_HISTORICO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "historico_qr.json")

COR_BARRA = "#1F2937"
COR_MENU = "#111827"
COR_MENU_HOVER = "#374151"
COR_AZUL = "#0078D7"
COR_VERDE = "#28A745"
COR_VERMELHO = "#DC3545"
COR_FUNDO = "#F3F4F6"

LARGURA_MENU = 200
ALTURA_BARRA = 50

INSTRUCOES = (
    "1. Digite um link, texto ou número no campo acima.\n"
    "2. Clique em \"Gerar QR Code\" (ou pressione Enter).\n"
    "3. Use \"Salvar Imagem (PNG)\" para guardar o QR Code.\n"
    "4. Cada QR gerado vai automaticamente para o Histórico.\n"
    "5. Abra o menu (☰) para trocar de tela ou sair."
)


def criar_qr(dados):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(dados)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").convert("RGB")


def salvar_png(imagem_pil, nome_inicial="meu_qrcode.png"):
    caminho = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("Imagem PNG", "*.png")],
        title="Salvar QR Code como...",
        initialfile=nome_inicial,
    )
    if caminho:
        imagem_pil.save(caminho)
        messagebox.showinfo("Sucesso", "QR Code salvo com sucesso!")


class GeradorQRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerador de QR Code")
        self.root.geometry("720x640")
        self.root.resizable(False, False)
        self.root.configure(bg=COR_FUNDO)

        self.qr_image_pil = None
        self.historico = self.carregar_historico()
        self.menu_aberto = False
        self.animando = False
        self.progresso = 0.0  # 0 = fechado, 1 = aberto

        self.construir_barra_superior()

        self.corpo = tk.Frame(root, bg=COR_FUNDO)
        self.corpo.pack(fill="both", expand=True)

        self.pagina_gerador = tk.Frame(self.corpo, bg=COR_FUNDO)
        self.pagina_historico = tk.Frame(self.corpo, bg=COR_FUNDO)

        self.construir_gerador()
        self.construir_historico()
        self.construir_rodape()
        self.construir_menu_lateral()

        self.mostrar_pagina("gerador")

    # ------------------------------------------------------------------
    # Persistência do histórico
    # ------------------------------------------------------------------
    def carregar_historico(self):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                dados = json.load(f)
            return [i for i in dados if isinstance(i, dict) and "texto" in i]
        except (OSError, json.JSONDecodeError):
            return []

    def salvar_historico(self):
        try:
            with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
                json.dump(self.historico, f, ensure_ascii=False, indent=2)
        except OSError:
            messagebox.showwarning("Aviso", "Não foi possível salvar o histórico em disco.")

    # ------------------------------------------------------------------
    # Barra superior com botão sanduíche
    # ------------------------------------------------------------------
    def construir_barra_superior(self):
        barra = tk.Frame(self.root, bg=COR_BARRA, height=ALTURA_BARRA)
        barra.pack(fill="x")
        barra.pack_propagate(False)

        self.canvas_burger = tk.Canvas(
            barra, width=44, height=44, bg=COR_BARRA, highlightthickness=0, cursor="hand2"
        )
        self.canvas_burger.pack(side="left", padx=(10, 5), pady=3)
        self.canvas_burger.bind("<Button-1>", lambda e: self.alternar_menu())

        self.label_titulo = tk.Label(
            barra, text="Gerador de QR Code", bg=COR_BARRA, fg="white", font=("Arial", 14, "bold")
        )
        self.label_titulo.pack(side="left", padx=10)

        self.desenhar_burger(0.0)

    def desenhar_burger(self, t):
        """Desenha as três barrinhas; em t=1 viram um X."""
        c = self.canvas_burger
        c.delete("all")

        def lerp(a, b):
            return a + (b - a) * t

        # barra de cima -> diagonal \
        c.create_line(
            lerp(9, 12), lerp(13, 12), lerp(35, 32), lerp(13, 32),
            fill="white", width=3, capstyle="round",
        )
        # barra do meio some
        if t < 0.5:
            c.create_line(9, 22, 35, 22, fill="white", width=3, capstyle="round")
        # barra de baixo -> diagonal /
        c.create_line(
            lerp(9, 12), lerp(31, 32), lerp(35, 32), lerp(31, 12),
            fill="white", width=3, capstyle="round",
        )

    # ------------------------------------------------------------------
    # Menu lateral com animação
    # ------------------------------------------------------------------
    def construir_menu_lateral(self):
        self.menu = tk.Frame(self.corpo, bg=COR_MENU, width=LARGURA_MENU)
        self.menu.place(x=-LARGURA_MENU, y=0, width=LARGURA_MENU, relheight=1)

        tk.Label(
            self.menu, text="MENU", bg=COR_MENU, fg="#9CA3AF", font=("Arial", 9, "bold")
        ).pack(anchor="w", padx=20, pady=(20, 10))

        self.criar_item_menu("🔳  Gerador", lambda: self.navegar("gerador"))
        self.criar_item_menu("🕘  Histórico", lambda: self.navegar("historico"))
        self.criar_item_menu("🚪  Sair", self.sair)

    def criar_item_menu(self, texto, comando):
        btn = tk.Label(
            self.menu, text=texto, bg=COR_MENU, fg="white", font=("Arial", 12),
            anchor="w", padx=20, pady=12, cursor="hand2",
        )
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg=COR_MENU_HOVER))
        btn.bind("<Leave>", lambda e: btn.config(bg=COR_MENU))
        btn.bind("<Button-1>", lambda e: comando())

    def alternar_menu(self):
        if self.animando:
            return
        self.menu_aberto = not self.menu_aberto
        self.animando = True
        self.animar_menu()

    def animar_menu(self):
        alvo = 1.0 if self.menu_aberto else 0.0
        passo = 0.1 if self.menu_aberto else -0.1
        self.progresso = min(1.0, max(0.0, self.progresso + passo))

        # easing suave (ease-in-out)
        t = self.progresso
        suave = t * t * (3 - 2 * t)

        self.menu.place(x=int(-LARGURA_MENU + LARGURA_MENU * suave), y=0,
                        width=LARGURA_MENU, relheight=1)
        self.menu.lift()
        self.desenhar_burger(suave)

        if abs(self.progresso - alvo) > 1e-6:
            self.root.after(15, self.animar_menu)
        else:
            self.animando = False

    def fechar_menu(self):
        if self.menu_aberto and not self.animando:
            self.alternar_menu()

    def navegar(self, pagina):
        self.mostrar_pagina(pagina)
        self.fechar_menu()

    def mostrar_pagina(self, pagina):
        self.pagina_gerador.pack_forget()
        self.pagina_historico.pack_forget()
        if pagina == "gerador":
            self.pagina_gerador.pack(fill="both", expand=True, padx=25, pady=(15, 35))
            self.label_titulo.config(text="Gerador de QR Code")
        else:
            self.atualizar_lista_historico()
            self.pagina_historico.pack(fill="both", expand=True, padx=25, pady=(15, 35))
            self.label_titulo.config(text="Histórico")
        self.menu.lift()

    def sair(self):
        if messagebox.askyesno("Sair", "Deseja realmente sair do aplicativo?"):
            self.root.destroy()

    # ------------------------------------------------------------------
    # Página: Gerador
    # ------------------------------------------------------------------
    def construir_gerador(self):
        p = self.pagina_gerador

        tk.Label(p, text="Digite o link, texto ou número:", font=("Arial", 11, "bold"),
                 bg=COR_FUNDO).pack(anchor="w")

        self.entrada_texto = tk.Entry(p, font=("Arial", 12))
        self.entrada_texto.pack(fill="x", pady=(5, 10))
        self.entrada_texto.bind("<Return>", lambda e: self.gerar_qr())
        self.entrada_texto.focus()

        tk.Button(
            p, text="Gerar QR Code", font=("Arial", 11, "bold"),
            bg=COR_AZUL, fg="white", cursor="hand2", command=self.gerar_qr,
        ).pack(fill="x", pady=(0, 10))

        meio = tk.Frame(p, bg=COR_FUNDO)
        meio.pack(fill="both", expand=True)

        self.label_imagem = tk.Label(
            meio, text="O QR Code aparecerá aqui", bg="#E0E0E0", width=30, height=14
        )
        self.label_imagem.pack(side="left", anchor="n")

        caixa = tk.LabelFrame(meio, text=" Instruções de uso ", font=("Arial", 10, "bold"),
                              bg=COR_FUNDO, padx=8, pady=8)
        caixa.pack(side="left", fill="both", expand=True, padx=(15, 0))

        self.texto_instrucoes = tk.Text(
            caixa, font=("Arial", 10), wrap="word", bg="white", relief="flat",
            height=10, width=28,
        )
        self.texto_instrucoes.insert("1.0", INSTRUCOES)
        self.texto_instrucoes.config(state="disabled")
        self.texto_instrucoes.pack(fill="both", expand=True)

        self.btn_salvar = tk.Button(
            p, text="Salvar Imagem (PNG)", font=("Arial", 11),
            state="disabled", cursor="hand2", command=self.salvar_qr,
        )
        self.btn_salvar.pack(fill="x", pady=(10, 0))

    def gerar_qr(self):
        dados = self.entrada_texto.get().strip()
        if not dados:
            messagebox.showwarning("Aviso", "Por favor, digite algum texto, link ou número!")
            return

        self.qr_image_pil = criar_qr(dados)

        img_exibicao = self.qr_image_pil.resize((250, 250), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_exibicao)
        self.label_imagem.config(image=img_tk, text="", width=250, height=250)
        self.label_imagem.image = img_tk
        self.btn_salvar.config(state="normal", bg=COR_VERDE, fg="white")

        self.adicionar_ao_historico(dados)

    def salvar_qr(self):
        if self.qr_image_pil:
            salvar_png(self.qr_image_pil)

    # ------------------------------------------------------------------
    # Página: Histórico
    # ------------------------------------------------------------------
    def construir_historico(self):
        p = self.pagina_historico

        tk.Label(p, text="QR Codes gerados anteriormente:", font=("Arial", 11, "bold"),
                 bg=COR_FUNDO).pack(anchor="w", pady=(0, 8))

        corpo = tk.Frame(p, bg=COR_FUNDO)
        corpo.pack(fill="both", expand=True)

        esquerda = tk.Frame(corpo, bg=COR_FUNDO)
        esquerda.pack(side="left", fill="both", expand=True)

        scroll = tk.Scrollbar(esquerda)
        scroll.pack(side="right", fill="y")

        self.lista_historico = tk.Listbox(
            esquerda, font=("Arial", 10), yscrollcommand=scroll.set,
            activestyle="none", exportselection=False, width=30,
        )
        self.lista_historico.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.lista_historico.yview)
        self.lista_historico.bind("<<ListboxSelect>>", self.ao_selecionar_historico)

        direita = tk.Frame(corpo, bg=COR_FUNDO)
        direita.pack(side="left", fill="both", padx=(15, 0))

        self.label_hist_img = tk.Label(
            direita, text="Selecione um item\npara visualizar", bg="#E0E0E0", width=28, height=13
        )
        self.label_hist_img.pack()

        self.label_hist_texto = tk.Label(
            direita, text="", bg=COR_FUNDO, font=("Arial", 10), wraplength=250, justify="left"
        )
        self.label_hist_texto.pack(pady=(8, 0), anchor="w")

        botoes = tk.Frame(p, bg=COR_FUNDO)
        botoes.pack(fill="x", pady=(10, 0))

        self.btn_hist_salvar = tk.Button(
            botoes, text="Salvar PNG", state="disabled", cursor="hand2",
            command=self.salvar_item_historico,
        )
        self.btn_hist_salvar.pack(side="left", expand=True, fill="x", padx=(0, 5))

        self.btn_hist_remover = tk.Button(
            botoes, text="Remover", state="disabled", cursor="hand2",
            command=self.remover_item_historico,
        )
        self.btn_hist_remover.pack(side="left", expand=True, fill="x", padx=5)

        tk.Button(
            botoes, text="Limpar tudo", bg=COR_VERMELHO, fg="white", cursor="hand2",
            command=self.limpar_historico,
        ).pack(side="left", expand=True, fill="x", padx=(5, 0))

        self.imagem_hist_pil = None

    def adicionar_ao_historico(self, texto):
        # Se já existe, remove para recolocar no topo com a nova data
        self.historico = [i for i in self.historico if i["texto"] != texto]
        self.historico.insert(0, {
            "texto": texto,
            "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        })
        self.historico = self.historico[:100]
        self.salvar_historico()

    def atualizar_lista_historico(self):
        self.lista_historico.delete(0, "end")
        for item in self.historico:
            texto = item["texto"]
            resumo = texto if len(texto) <= 28 else texto[:27] + "…"
            self.lista_historico.insert("end", f"{resumo}   ({item['data']})")
        self.limpar_visualizacao()

    def limpar_visualizacao(self):
        self.imagem_hist_pil = None
        self.label_hist_img.config(image="", text="Selecione um item\npara visualizar",
                                   width=28, height=13)
        self.label_hist_img.image = None
        self.label_hist_texto.config(text="")
        self.btn_hist_salvar.config(state="disabled")
        self.btn_hist_remover.config(state="disabled")

    def ao_selecionar_historico(self, _event=None):
        sel = self.lista_historico.curselection()
        if not sel:
            return
        item = self.historico[sel[0]]

        self.imagem_hist_pil = criar_qr(item["texto"])
        img = self.imagem_hist_pil.resize((220, 220), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.label_hist_img.config(image=img_tk, text="", width=220, height=220)
        self.label_hist_img.image = img_tk

        self.label_hist_texto.config(text=f"Código: {item['texto']}\nGerado em: {item['data']}")
        self.btn_hist_salvar.config(state="normal")
        self.btn_hist_remover.config(state="normal")

    def salvar_item_historico(self):
        if self.imagem_hist_pil:
            salvar_png(self.imagem_hist_pil)

    def remover_item_historico(self):
        sel = self.lista_historico.curselection()
        if not sel:
            return
        del self.historico[sel[0]]
        self.salvar_historico()
        self.atualizar_lista_historico()

    def limpar_historico(self):
        if not self.historico:
            return
        if messagebox.askyesno("Limpar histórico", "Apagar todo o histórico de QR Codes?"):
            self.historico = []
            self.salvar_historico()
            self.atualizar_lista_historico()

    # ------------------------------------------------------------------
    # Rodapé
    # ------------------------------------------------------------------
    def construir_rodape(self):
        self.label_autor = tk.Label(
            self.corpo, text="Charles Brendon", bg=COR_FUNDO, fg="#6B7280",
            font=("Arial", 9, "italic"),
        )
        self.label_autor.place(relx=1.0, rely=1.0, anchor="se", x=-12, y=-8)


if __name__ == "__main__":
    janela = tk.Tk()
    app = GeradorQRApp(janela)
    janela.mainloop()