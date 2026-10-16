"""Interface grafica (tkinter) do cofre de senhas.

MVP: desbloquear/criar cofre com senha mestra, cadastrar/acessar/remover
senhas e copiar a senha para a area de transferencia. Toda a cifragem fica
em :mod:`cofre_senhas_aes256.cofre`; esta camada so exibe dados decifrados.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from .cofre import CofreError, CofreSenhas

CAMINHO_PADRAO = Path.home() / "cofre-senhas-aes256.enc"


class CofreGUI(tk.Tk):
    """Janela principal: cadastra e acessa senhas cifradas AES-256."""

    def __init__(self, caminho_arquivo: Path = CAMINHO_PADRAO) -> None:
        super().__init__()
        self.title("Cofre de Senhas AES-256")
        self.geometry("540x430")
        self.caminho_arquivo = caminho_arquivo
        self.cofre = CofreSenhas(caminho_arquivo)
        self._construir_interface()
        self._atualizar_estado()

    # ------------------------------------------------------------------ UI

    def _construir_interface(self) -> None:
        container = ttk.Frame(self, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        # --- Acesso (senha mestra) -------------------------------------
        frame_acesso = ttk.LabelFrame(container, text="Acesso ao cofre", padding=10)
        frame_acesso.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(frame_acesso, text="Senha mestra:").grid(row=0, column=0, sticky=tk.W)
        self.entry_senha_mestra = ttk.Entry(frame_acesso, show="*", width=38)
        self.entry_senha_mestra.grid(row=0, column=1, padx=(8, 0), sticky=tk.W)
        self.entry_senha_mestra.bind("<Return>", lambda _event: self._acao_acesso())

        self.botao_criar = ttk.Button(
            frame_acesso, text="Criar cofre", command=self._criar
        )
        self.botao_criar.grid(row=0, column=2, padx=(8, 0))
        self.botao_desbloquear = ttk.Button(
            frame_acesso, text="Desbloquear", command=self._desbloquear
        )
        self.botao_desbloquear.grid(row=0, column=3, padx=(8, 0))
        self.botao_bloquear = ttk.Button(
            frame_acesso, text="Bloquear", command=self._bloquear
        )
        self.botao_bloquear.grid(row=0, column=4, padx=(8, 0))

        self.label_status = ttk.Label(frame_acesso, text="", foreground="red")
        self.label_status.grid(row=1, column=0, columnspan=5, sticky=tk.W, pady=(6, 0))

        # --- Cadastro / acesso a senha ---------------------------------
        frame_cadastro = ttk.LabelFrame(container, text="Nova senha", padding=10)
        frame_cadastro.pack(fill=tk.X, pady=(0, 12))

        for coluna, (rotulo, nome_attr) in enumerate(
            [
                (0, ("Servico:", "servico")),
                (1, ("Usuario:", "usuario")),
                (2, ("Senha:", "senha_nova")),
            ]
        ):
            ttk.Label(frame_cadastro, text=rotulo).grid(
                row=0, column=coluna * 2, sticky=tk.W
            )
            entry = ttk.Entry(frame_cadastro, width=22)
            entry.grid(row=0, column=coluna * 2 + 1, padx=(4, 8), sticky=tk.W)
            setattr(self, f"entry_{nome_attr}", entry)
        self.entry_senha_nova.config(show="")

        self.botao_adicionar = ttk.Button(
            frame_cadastro, text="Adicionar / Atualizar", command=self._adicionar
        )
        self.botao_adicionar.grid(row=0, column=7, padx=(4, 0))

        # --- Lista de entradas -----------------------------------------
        frame_lista = ttk.LabelFrame(container, text="Entradas cadastradas", padding=10)
        frame_lista.pack(fill=tk.BOTH, expand=True)

        colunas = ("servico", "usuario")
        self.tree = ttk.Treeview(
            frame_lista,
            columns=colunas,
            show="headings",
            height=8,
            selectmode="browse",
        )
        self.tree.heading("servico", text="Servico")
        self.tree.heading("usuario", text="Usuario")
        self.tree.column("servico", width=180)
        self.tree.column("usuario", width=140)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(
            frame_lista, orient=tk.VERTICAL, command=self.tree.yview
        )
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        botoes = ttk.Frame(frame_lista)
        botoes.pack(fill=tk.X, pady=(8, 0))
        self.botao_copiar = ttk.Button(
            botoes, text="Copiar senha", command=self._copiar
        )
        self.botao_copiar.pack(side=tk.LEFT)
        self.botao_remover = ttk.Button(
            botoes, text="Remover selecionada", command=self._remover
        )
        self.botao_remover.pack(side=tk.LEFT, padx=(8, 0))

    # ------------------------------------------------------- acoes de acesso

    def _acao_acesso(self) -> None:
        """Desbloqueia se o arquivo existe, senao cria o cofre."""
        if self.caminho_arquivo.exists():
            self._desbloquear()
        else:
            self._criar()

    def _criar(self) -> None:
        senha = self.entry_senha_mestra.get()
        if not senha.strip():
            messagebox.showwarning("Aviso", "Informe a senha mestra.")
            return
        try:
            self.cofre.criar(senha.strip())
        except (CofreError, ValueError) as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.entry_senha_mestra.delete(0, tk.END)
        self.label_status.config(
            text="Cofre criado e desbloqueado.", foreground="green"
        )
        self._atualizar_estado()

    def _desbloquear(self) -> None:
        senha = self.entry_senha_mestra.get()
        if not senha.strip():
            messagebox.showwarning("Aviso", "Informe a senha mestra.")
            return
        try:
            self.cofre.desbloquear(senha.strip())
        except CofreError as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.entry_senha_mestra.delete(0, tk.END)
        self.label_status.config(text="Cofre desbloqueado.", foreground="green")
        self._atualizar_estado()

    def _bloquear(self) -> None:
        self.cofre.bloquear()
        self.label_status.config(text="Cofre bloqueado.", foreground="red")
        self._atualizar_estado()

    # ------------------------------------------------------ cadastro de senha

    def _adicionar(self) -> None:
        servico = self.entry_servico.get()
        usuario = self.entry_usuario.get()
        senha = self.entry_senha_nova.get()
        try:
            self.cofre.adicionar(servico, usuario, senha)
        except (CofreError, ValueError) as exc:
            messagebox.showerror("Erro", str(exc))
            return
        for entry in (self.entry_servico, self.entry_usuario, self.entry_senha_nova):
            entry.delete(0, tk.END)
        self._atualizar_estado()

    def _copiar(self) -> None:
        selecao = self.tree.selection()
        if not selecao:
            return
        servico, usuario = self.tree.item(selecao[0], "values")
        try:
            senha = self.cofre.obter(servico, usuario)
        except CofreError as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self.clipboard_clear()
        self.clipboard_append(senha)
        self.label_status.config(
            text=f"Senha de {servico} copiada.", foreground="green"
        )
        self.after(3000, lambda: self.label_status.config(text=""))

    def _remover(self) -> None:
        selecao = self.tree.selection()
        if not selecao:
            return
        servico, usuario = self.tree.item(selecao[0], "values")
        if not messagebox.askyesno(
            "Confirmar", f"Remover senha de {servico} ({usuario})?"
        ):
            return
        try:
            self.cofre.remover(servico, usuario)
        except CofreError as exc:
            messagebox.showerror("Erro", str(exc))
            return
        self._atualizar_estado()

    # ----------------------------------------------------------- estado da UI

    def _atualizar_estado(self) -> None:
        desbloqueado = self.cofre.esta_desbloqueado()
        estado = tk.NORMAL if desbloqueado else tk.DISABLED
        for widget in (
            self.botao_adicionar,
            self.botao_copiar,
            self.botao_remover,
            self.entry_servico,
            self.entry_usuario,
            self.entry_senha_nova,
            self.tree,
        ):
            widget.configure(state=estado)
        self.botao_bloquear.configure(
            state=tk.NORMAL if desbloqueado else tk.DISABLED
        )
        self.botao_criar.configure(state=tk.DISABLED if desbloqueado else tk.NORMAL)
        self.botao_desbloquear.configure(
            state=tk.DISABLED if desbloqueado else tk.NORMAL
        )
        self._listar_entradas()

    def _listar_entradas(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        if not self.cofre.esta_desbloqueado():
            return
        for entrada in self.cofre.listar_entradas():
            self.tree.insert(
                "", tk.END, values=(entrada.servico, entrada.usuario)
            )


def main(caminho_arquivo: Path = CAMINHO_PADRAO) -> int:
    """Executa a interface grafica. Retorna 0 ao encerrar."""
    app = CofreGUI(caminho_arquivo)
    app.mainloop()
    return 0
