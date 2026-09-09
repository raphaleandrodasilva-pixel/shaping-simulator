"""
Aba de Entrada de Dados
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json

from core import data_manager as dm
from gui.dialogs.cadastro_dialog import CadastroDialog

class InputTab(ttk.Frame):
    """
    Aba para entrada de todos os parâmetros
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main = main_window
        
        # Dicionário para armazenar as variáveis
        self.vars = {}
        
        # Dicionário para armazenar os cortes (passes)
        self.cortes = []  # Lista de dicionários: {'tipo': 'Desbaste', 'avanco': 0.004, 'profundidade': 80}
        
        self._build_layout()
        self._carregar_dados_padrao()
    
    def _build_layout(self):
        # Frame principal com scroll
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        self._canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Faz o frame interno acompanhar a largura do canvas
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self._canvas_window, width=e.width)
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Duas colunas lado a lado
        col_esquerda = ttk.Frame(self.scrollable_frame)
        col_direita = ttk.Frame(self.scrollable_frame)
        col_esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        col_direita.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # Cria as seções
        self._criar_secao_geometria(col_esquerda)
        self._criar_secao_ferramenta(col_esquerda)
        self._criar_secao_processo(col_direita)
        self._criar_secao_material(col_direita)

        # Seção avançada em largura total
        self._criar_secao_avancada(self.scrollable_frame, row=1)

        # Botões de ação
        btn_frame = ttk.Frame(self.scrollable_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=20)
        
        ttk.Button(
            btn_frame,
            text="🧮 Calcular e Preparar",
            command=self._iniciar_simulacao,
            style="Accent.TButton"
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="🔄 Carregar Padrão",
            command=self._carregar_dados_padrao
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="💾 Salvar Parâmetros",
            command=self.salvar_parametros
        ).pack(side="left", padx=5)
        
        ttk.Button(
            btn_frame,
            text="📂 Carregar Parâmetros",
            command=self.carregar_parametros
        ).pack(side="left", padx=5)

        ttk.Button(
            btn_frame,
            text="🗂️ Cadastrar Materiais/Ferramentas",
            command=self._abrir_cadastro
        ).pack(side="left", padx=5)
    
    def _criar_secao_geometria(self, parent):
        frame = ttk.LabelFrame(parent, text="Geometria da Peça", padding=10)
        frame.pack(fill="x", pady=5)
        
        # ==== NOVO: Seletor de Tipo de Engrenagem ====
        ttk.Label(frame, text="Tipo de engrenagem:").grid(row=0, column=0, sticky="w", pady=2)
        self.vars['tipo_engrenagem'] = tk.StringVar(value="Interna")
        combo_tipo = ttk.Combobox(
            frame, 
            textvariable=self.vars['tipo_engrenagem'],
            values=["Externa", "Interna"],
            state="readonly", 
            width=12
        )
        combo_tipo.grid(row=0, column=1, sticky="w", pady=2)
        combo_tipo.bind("<<ComboboxSelected>>", self._atualizar_geometria_por_tipo)
        
        # Parâmetros de geometria
        params = [
            ("Módulo (mm)", "modulo", 3.5),      # Atualizado para valor real
            ("Número de dentes", "z_peca", 12),  # Atualizado para valor real
            ("Largura de face (mm)", "face_width", 20),
            ("Raio interno (mm)", "inner_radius", 39.6),  # Atualizado para valor real
            ("Raio externo (mm)", "outer_radius", 59.5),  # Atualizado para valor real
        ]
        
        # Ajuste para começar na linha 1 (linha 0 é o seletor)
        for i, (label, key, default) in enumerate(params):
            row = i + 1
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=row, column=1, sticky="w", pady=2)
            self.vars[key] = var

    def _atualizar_geometria_por_tipo(self, event=None):
        """Atualiza os raios com base no tipo de engrenagem selecionado"""
        tipo = self.vars['tipo_engrenagem'].get()
        if tipo == "Interna":
            # Para interna: raio interno é onde estão os dentes (menor)
            # Os valores padrão já são para interna
            pass
        else:
            # Para externa: raio externo é onde estão os dentes (maior)
            # Mantém os valores atuais, o usuário pode ajustar manualmente
            pass
        # Nota: o usuário pode ajustar manualmente os valores, esta função é apenas
        # para orientação visual
    
    def _criar_secao_ferramenta(self, parent):
        frame = ttk.LabelFrame(parent, text="Ferramenta (Shaper Cutter)", padding=10)
        frame.pack(fill="x", pady=5)
        
        params = [
            ("Número de dentes", "z_ferramenta", 8),  # Atualizado para valor real
            ("Ângulo de saída (°)", "rake_angle", 5),
            ("Ângulo de folga (°)", "clearance_angle", 6),
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
        
        # Material da ferramenta
        ttk.Label(frame, text="Material da ferramenta:").grid(row=3, column=0, sticky="w", pady=2)
        self.vars['tool_material'] = tk.StringVar(value="Carbeto")
        self.combo_tool_material = ttk.Combobox(
            frame, textvariable=self.vars['tool_material'],
            values=list(dm.load_tools().keys()),
            state="readonly", width=14
        )
        self.combo_tool_material.grid(row=3, column=1, sticky="w", pady=2)
    
    def _criar_secao_processo(self, parent):
        frame = ttk.LabelFrame(parent, text="Parâmetros de Corte", padding=10)
        frame.pack(fill="x", pady=5)
        
        params = [
            ("Golpes/min (SPM)", "spm", 450),  # Atualizado para valor real
            ("Comprimento do curso (mm)", "stroke_length", 23.8),
            ("Avanço envolvente (mm/golpe)", "circular_feed", 0.730),  # Atualizado para valor real
            ("Profundidade total (mm)", "depth", 3.318),  # Atualizado para valor real
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
        
        # ==== NOVO: Tabela de Múltiplos Cortes ====
        ttk.Label(frame, text="Cortes (Passes):", font=('TkDefaultFont', 9, 'bold')).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 2))
        
        # Frame para a tabela
        tabela_frame = ttk.Frame(frame)
        tabela_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=2)
        
        # Treeview para exibir os cortes
        colunas = ("Tipo", "Avanço Radial (mm/Bat)", "Profundidade (%)")
        self.tree_cortes = ttk.Treeview(tabela_frame, columns=colunas, show="headings", height=3)
        
        # Definir cabeçalhos
        self.tree_cortes.heading("Tipo", text="Tipo")
        self.tree_cortes.heading("Avanço Radial (mm/Bat)", text="Avanço Radial (mm/Bat)")
        self.tree_cortes.heading("Profundidade (%)", text="Profundidade (%)")
        
        # Ajustar larguras
        self.tree_cortes.column("Tipo", width=80)
        self.tree_cortes.column("Avanço Radial (mm/Bat)", width=100)
        self.tree_cortes.column("Profundidade (%)", width=80)
        
        # Scrollbar para a tabela
        scroll_tree = ttk.Scrollbar(tabela_frame, orient="vertical", command=self.tree_cortes.yview)
        self.tree_cortes.configure(yscrollcommand=scroll_tree.set)
        
        self.tree_cortes.pack(side="left", fill="both", expand=True)
        scroll_tree.pack(side="right", fill="y")
        
        # Botões para gerenciar cortes
        btn_cortes_frame = ttk.Frame(frame)
        btn_cortes_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=5)
        
        ttk.Button(
            btn_cortes_frame,
            text="➕ Adicionar Corte",
            command=self._adicionar_corte
        ).pack(side="left", padx=2)
        
        ttk.Button(
            btn_cortes_frame,
            text="❌ Remover Corte",
            command=self._remover_corte
        ).pack(side="left", padx=2)
        
        ttk.Button(
            btn_cortes_frame,
            text="📋 Carregar Padrão (2 Cortes)",
            command=self._carregar_cortes_padrao
        ).pack(side="left", padx=2)
        
        # Refrigeração
        ttk.Label(frame, text="Refrigeração:").grid(row=7, column=0, sticky="w", pady=2)
        self.vars['cooling'] = tk.StringVar(value="Com fluido")
        combo = ttk.Combobox(frame, textvariable=self.vars['cooling'],
                             values=["Com fluido", "Sem fluido", "Mínima quantidade"],
                             state="readonly", width=12)
        combo.grid(row=7, column=1, sticky="w", pady=2)
        
        # Carregar cortes padrão
        self._carregar_cortes_padrao()
    
    def _adicionar_corte(self):
        """Abre um diálogo para adicionar um novo corte"""
        from tkinter import simpledialog
        
        tipo = simpledialog.askstring("Adicionar Corte", "Tipo do corte (ex: Desbaste, Acabamento):")
        if not tipo:
            return
        
        try:
            avanco = float(simpledialog.askstring("Adicionar Corte", "Avanço radial (mm/Bat):"))
            profundidade = float(simpledialog.askstring("Adicionar Corte", "Profundidade (% do total):"))
        except (TypeError, ValueError):
            messagebox.showerror("Erro", "Valores inválidos!")
            return
        
        self.cortes.append({
            'tipo': tipo,
            'avanco': avanco,
            'profundidade': profundidade
        })
        self._atualizar_tree_cortes()
    
    def _remover_corte(self):
        """Remove o corte selecionado"""
        selecionado = self.tree_cortes.selection()
        if not selecionado:
            return
        
        for item in selecionado:
            idx = self.tree_cortes.index(item)
            if idx < len(self.cortes):
                del self.cortes[idx]
        
        self._atualizar_tree_cortes()
    
    def _carregar_cortes_padrao(self):
        """Carrega a configuração padrão de dois cortes (baseado nos dados reais)"""
        self.cortes = [
            {'tipo': 'Desbaste', 'avanco': 0.004, 'profundidade': 75},
            {'tipo': 'Acabamento', 'avanco': 0.010, 'profundidade': 25},
        ]
        self._atualizar_tree_cortes()
    
    def _atualizar_tree_cortes(self):
        """Atualiza a tabela de cortes"""
        # Limpar tabela
        for item in self.tree_cortes.get_children():
            self.tree_cortes.delete(item)
        
        # Adicionar dados
        for corte in self.cortes:
            self.tree_cortes.insert("", "end", values=(
                corte['tipo'],
                f"{corte['avanco']:.4f}",
                f"{corte['profundidade']:.0f}%"
            ))
    
    def _criar_secao_material(self, parent):
        frame = ttk.LabelFrame(parent, text="Material da Peça", padding=10)
        frame.pack(fill="x", pady=5)

        materiais = dm.load_materials()
        self._mapa_materiais = {v.get("nome", k): k for k, v in materiais.items()}

        ttk.Label(frame, text="Material:").grid(row=0, column=0, sticky="w", pady=2)
        primeiro_nome = next(iter(self._mapa_materiais), "")
        self.vars['material'] = tk.StringVar(value=primeiro_nome)
        self.combo_material = ttk.Combobox(
            frame, textvariable=self.vars['material'],
            values=list(self._mapa_materiais.keys()), state="readonly", width=28
        )
        self.combo_material.grid(row=0, column=1, sticky="w", pady=2)
        self.combo_material.bind("<<ComboboxSelected>>", self._atualizar_kienzle)

        kienzle_params = [
            ("k_c1,1 (N/mm²)", "k_c1_1", 1680),
            ("m_c", "m_c", 0.26),
            ("k_f1,1 (N/mm²)", "k_f1_1", 340),
            ("m_f", "m_f", 0.68),
        ]

        for i, (label, key, default) in enumerate(kienzle_params, 1):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var

        self._atualizar_kienzle()

    def _abrir_cadastro(self):
        CadastroDialog(self.winfo_toplevel(), on_close_callback=self._refresh_combos_apos_cadastro)

    def _refresh_combos_apos_cadastro(self):
        self.combo_tool_material.configure(values=list(dm.load_tools().keys()))
        materiais = dm.load_materials()
        self._mapa_materiais = {v.get("nome", k): k for k, v in materiais.items()}
        self.combo_material.configure(values=list(self._mapa_materiais.keys()))
    
    def _criar_secao_avancada(self, parent, row=0):
        frame = ttk.LabelFrame(parent, text="Parâmetros Avançados", padding=10)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        
        params = [
            ("Ângulo de atrito (°)", "friction_angle", 25),
            ("Ângulo de cisalhamento (°)", "shear_angle", 30),
            ("Rigidez X (N/m)", "stiffness_x", 1e6),  # Atualizado para valor real
            ("Rigidez Y (N/m)", "stiffness_y", 1e6),  # Atualizado para valor real
            ("Resolução da malha", "mesh_resolution", 50),
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
    
    def _atualizar_kienzle(self, event=None):
        nome_selecionado = self.vars['material'].get()
        chave = self._mapa_materiais.get(nome_selecionado)
        if not chave:
            return
        dados = dm.load_materials().get(chave, {})
        if dados:
            self.vars['k_c1_1'].set(dados.get('k_c', 0))
            self.vars['m_c'].set(dados.get('m_c', 0))
            self.vars['k_f1_1'].set(dados.get('k_f', 0))
            self.vars['m_f'].set(dados.get('m_f', 0))
    
    def _carregar_dados_padrao(self):
        """Carrega os dados padrão baseados nos valores reais da máquina"""
        # Geometria da Peça (valores reais)
        self.vars['tipo_engrenagem'].set("Interna")
        self.vars['modulo'].set(3.5)
        self.vars['z_peca'].set(12)
        self.vars['face_width'].set(20)
        self.vars['inner_radius'].set(39.6)
        self.vars['outer_radius'].set(59.5)
        
        # Ferramenta (valores reais)
        self.vars['z_ferramenta'].set(8)
        self.vars['rake_angle'].set(5)
        self.vars['clearance_angle'].set(6)
        self.vars['tool_material'].set("Carbeto")
        
        # Processo (valores reais)
        self.vars['spm'].set(450)
        self.vars['stroke_length'].set(23.8)
        self.vars['circular_feed'].set(0.730)
        self.vars['depth'].set(3.318)
        self.vars['cooling'].set("Com fluido")
        self._carregar_cortes_padrao()
        
        # Material (C45)
        nome_c45 = next((n for n, k in self._mapa_materiais.items() if k == "C45"), None)
        if nome_c45:
            self.vars['material'].set(nome_c45)
        self._atualizar_kienzle()
        
        # Avançados
        self.vars['friction_angle'].set(25)
        self.vars['shear_angle'].set(30)
        self.vars['stiffness_x'].set(1e6)
        self.vars['stiffness_y'].set(1e6)
        self.vars['mesh_resolution'].set(50)
    
    def get_params(self):
        """Retorna todos os parâmetros como dicionário, incluindo os cortes"""
        params = {}
        for key, var in self.vars.items():
            try:
                params[key] = var.get()
            except:
                params[key] = None
        
        # Adiciona a lista de cortes
        params['cortes'] = self.cortes
        
        # Adiciona o tipo de engrenagem (já está em params)
        return params
    
    def _iniciar_simulacao(self):
        """Inicia a simulação com os parâmetros atuais"""
        params = self.get_params()
        
        # Verifica se há cortes definidos
        if not params.get('cortes'):
            messagebox.showerror("Erro", "Defina pelo menos um corte (passe) na tabela de cortes!")
            return
        
        print("🚀 Iniciando simulação...")
        print(f"📊 Parâmetros: {params}")
        
        # Validações básicas
        if params['z_peca'] <= params['z_ferramenta']:
            messagebox.showerror("Erro", "O número de dentes da peça deve ser maior que o da ferramenta")
            return
        
        if params['inner_radius'] >= params['outer_radius']:
            messagebox.showerror("Erro", "O raio interno deve ser menor que o raio externo")
            return
        
        # Calcula e prepara o motor antes da execução dos golpes
        self.main.set_status("Calculando parâmetros da simulação...")
        
        # Passa para a aba de simulação
        self.main.notebook.select(1)
        
        # Força a atualização da interface
        self.main.root.update_idletasks()
        
        # Inicializa a simulação com os parâmetros
        self.main.tab_simulation.iniciar(params)
        self.main.set_status("Parâmetros calculados. Clique em 'Iniciar' na aba Simulação.")
    
    def salvar_parametros(self):
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            params = self.get_params()
            with open(filename, 'w') as f:
                json.dump(params, f, indent=2)
            self.main.set_status(f"Parâmetros salvos em {filename}")
    
    def carregar_parametros(self):
        from tkinter import filedialog
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, 'r') as f:
                params = json.load(f)
            for key, val in params.items():
                if key in self.vars:
                    try:
                        self.vars[key].set(val)
                    except:
                        pass
            # Carregar cortes se existirem
            if 'cortes' in params:
                self.cortes = params['cortes']
                self._atualizar_tree_cortes()
            self._atualizar_kienzle()
            self.main.set_status(f"Parâmetros carregados de {filename}")