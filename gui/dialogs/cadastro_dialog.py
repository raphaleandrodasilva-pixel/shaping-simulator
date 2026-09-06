"""
Janela de Cadastro - permite adicionar, editar e remover materiais e
ferramentas usados na simulacao, persistindo em data/materials.json e
data/tools.json atraves do core.data_manager.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from core import data_manager as dm


class CadastroDialog(tk.Toplevel):
    def __init__(self, parent, on_close_callback=None):
        super().__init__(parent)
        self.title("Cadastro de Materiais e Ferramentas")
        self.geometry("760x520")
        self.on_close_callback = on_close_callback

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.aba_materiais = CadastroPanel(
            notebook,
            titulo="Material",
            campos=dm.CAMPOS_MATERIAL,
            load_fn=dm.load_materials,
            upsert_fn=dm.upsert_material,
            delete_fn=dm.delete_material,
        )
        self.aba_ferramentas = CadastroPanel(
            notebook,
            titulo="Ferramenta",
            campos=dm.CAMPOS_FERRAMENTA,
            load_fn=dm.load_tools,
            upsert_fn=dm.upsert_tool,
            delete_fn=dm.delete_tool,
        )

        notebook.add(self.aba_materiais, text="Materiais")
        notebook.add(self.aba_ferramentas, text="Ferramentas")

        ttk.Button(self, text="Fechar", command=self._fechar).pack(pady=(0, 8))

        self.protocol("WM_DELETE_WINDOW", self._fechar)

    def _fechar(self):
        if self.on_close_callback:
            self.on_close_callback()
        self.destroy()


class CadastroPanel(ttk.Frame):
    """
    Painel generico de cadastro: lista (Treeview) + formulario, reaproveitado
    tanto para materiais quanto para ferramentas, conforme os 'campos'
    informados pelo core.data_manager.
    """

    def __init__(self, parent, titulo, campos, load_fn, upsert_fn, delete_fn):
        super().__init__(parent, padding=10)
        self.titulo = titulo
        self.campos = campos  # lista de (chave_json, label, tipo, default)
        self.load_fn = load_fn
        self.upsert_fn = upsert_fn
        self.delete_fn = delete_fn
        self.chave_selecionada = None

        self._build()
        self._refresh_lista()

    def _build(self):
        # ---------------- Lista (esquerda) ----------------
        left = ttk.Frame(self)
        left.pack(side="left", fill="y", padx=(0, 10))

        ttk.Label(left, text=f"{self.titulo}s cadastrados", font=("Segoe UI", 10, "bold")).pack(anchor="w")

        self.tree = ttk.Treeview(left, columns=("nome",), show="headings", height=16, selectmode="browse")
        self.tree.heading("nome", text="Nome")
        self.tree.column("nome", width=220)
        self.tree.pack(fill="y", expand=False, pady=(4, 6))
        self.tree.bind("<<TreeviewSelect>>", self._ao_selecionar)

        btn_row = ttk.Frame(left)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Novo", command=self._novo).pack(side="left", padx=2)
        ttk.Button(btn_row, text="Excluir", command=self._excluir).pack(side="left", padx=2)

        # ---------------- Formulario (direita) ----------------
        right = ttk.LabelFrame(self, text=f"Dados do {self.titulo.lower()}", padding=10)
        right.pack(side="left", fill="both", expand=True)

        ttk.Label(right, text="Chave interna (sem espacos, ex: SAE_1050):").grid(
            row=0, column=0, sticky="w", pady=3, columnspan=2
        )
        self.var_chave = tk.StringVar()
        self.entry_chave = ttk.Entry(right, textvariable=self.var_chave, width=30)
        self.entry_chave.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        self.form_vars = {}
        row = 2
        for chave_campo, label, tipo, default in self.campos:
            ttk.Label(right, text=label + ":").grid(row=row, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=str(default))
            entry = ttk.Entry(right, textvariable=var, width=32)
            entry.grid(row=row, column=1, sticky="w", pady=3)
            self.form_vars[chave_campo] = (var, tipo)
            row += 1

        btn_form = ttk.Frame(right)
        btn_form.grid(row=row, column=0, columnspan=2, pady=(12, 0), sticky="w")
        ttk.Button(btn_form, text="Salvar", command=self._salvar).pack(side="left", padx=2)
        ttk.Button(btn_form, text="Limpar formulario", command=self._limpar_form).pack(side="left", padx=2)

    def _refresh_lista(self):
        self.tree.delete(*self.tree.get_children())
        dados = self.load_fn()
        for chave, valores in dados.items():
            nome = valores.get("nome", chave)
            self.tree.insert("", "end", iid=chave, values=(nome,))

    def _ao_selecionar(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        chave = sel[0]
        self.chave_selecionada = chave
        dados = self.load_fn()
        registro = dados.get(chave, {})

        self.var_chave.set(chave)
        self.entry_chave.configure(state="disabled")  # nao deixa mudar a chave de um existente

        for chave_campo, (var, tipo) in self.form_vars.items():
            var.set(str(registro.get(chave_campo, "")))

    def _novo(self):
        self.chave_selecionada = None
        self.entry_chave.configure(state="normal")
        self._limpar_form()

    def _limpar_form(self):
        self.var_chave.set("")
        for chave_campo, label, tipo, default in self.campos:
            self.form_vars[chave_campo][0].set(str(default))

    def _validar_e_montar_registro(self):
        registro = {}
        for chave_campo, label, tipo, default in self.campos:
            valor_str = self.form_vars[chave_campo][0].get().strip()
            try:
                if tipo is float:
                    registro[chave_campo] = float(valor_str.replace(",", "."))
                else:
                    registro[chave_campo] = valor_str
            except ValueError:
                raise ValueError(f"O campo '{label}' precisa ser numerico. Valor recebido: '{valor_str}'")
        return registro

    def _salvar(self):
        chave = self.var_chave.get().strip().replace(" ", "_")
        if not chave:
            messagebox.showerror("Erro", "Informe a chave interna (identificador) antes de salvar.")
            return

        try:
            registro = self._validar_e_montar_registro()
        except ValueError as e:
            messagebox.showerror("Erro de validacao", str(e))
            return

        self.upsert_fn(chave, registro)
        self._refresh_lista()
        self.entry_chave.configure(state="disabled")
        self.chave_selecionada = chave
        messagebox.showinfo("Salvo", f"{self.titulo} '{registro.get('nome', chave)}' salvo com sucesso.")

    def _excluir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atencao", f"Selecione um {self.titulo.lower()} na lista para excluir.")
            return
        chave = sel[0]
        nome = self.load_fn().get(chave, {}).get("nome", chave)
        if messagebox.askyesno("Confirmar exclusao", f"Excluir '{nome}' definitivamente?"):
            self.delete_fn(chave)
            self._refresh_lista()
            self._limpar_form()
            self.entry_chave.configure(state="normal")
            self.chave_selecionada = None
