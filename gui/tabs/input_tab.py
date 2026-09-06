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

        # Faz o frame interno acompanhar a largura do canvas, para nao sobrar
        # espaco vazio a direita quando a janela e maior que o conteudo.
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self._canvas_window, width=e.width)
        )

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Duas colunas lado a lado para aproveitar a largura da janela
        col_esquerda = ttk.Frame(self.scrollable_frame)
        col_direita = ttk.Frame(self.scrollable_frame)
        col_esquerda.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        col_direita.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

        # Cria as seções (2 por coluna)
        self._criar_secao_geometria(col_esquerda)
        self._criar_secao_ferramenta(col_esquerda)
        self._criar_secao_processo(col_direita)
        self._criar_secao_material(col_direita)

        # Seção avançada em largura total, abaixo das duas colunas
        self._criar_secao_avancada(self.scrollable_frame, row=1)

        # Botões de ação, largura total
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
        
        params = [
            ("Módulo (mm)", "modulo", 2.2),
            ("Número de dentes", "z_peca", 43),
            ("Largura de face (mm)", "face_width", 20),
            ("Raio interno (mm)", "inner_radius", 47.3),
            ("Raio externo (mm)", "outer_radius", 60.4),
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
    
    def _criar_secao_ferramenta(self, parent):
        frame = ttk.LabelFrame(parent, text="Ferramenta (Shaper Cutter)", padding=10)
        frame.pack(fill="x", pady=5)
        
        params = [
            ("Número de dentes", "z_ferramenta", 14),
            ("Ângulo de saída (°)", "rake_angle", 5),
            ("Ângulo de folga (°)", "clearance_angle", 6),
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
        
        # Material da ferramenta (Combobox) - lido de data/tools.json
        ttk.Label(frame, text="Material da ferramenta:").grid(row=3, column=0, sticky="w", pady=2)
        self.vars['tool_material'] = tk.StringVar(value="HSS-Co")
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
            ("Golpes/min (SPM)", "spm", 400),
            ("Comprimento do curso (mm)", "stroke_length", 23.8),
            ("Avanço circular (mm/golpe)", "circular_feed", 0.25),
            ("Avanço radial (mm/golpe)", "radial_feed", 0.05),
            ("Profundidade total (mm)", "depth", 3),
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
        
        # Refrigeração (Combobox)
        ttk.Label(frame, text="Refrigeração:").grid(row=5, column=0, sticky="w", pady=2)
        self.vars['cooling'] = tk.StringVar(value="Com fluido")
        combo = ttk.Combobox(frame, textvariable=self.vars['cooling'],
                             values=["Com fluido", "Sem fluido", "Mínima quantidade"],
                             state="readonly", width=12)
        combo.grid(row=5, column=1, sticky="w", pady=2)
    
    def _criar_secao_material(self, parent):
        frame = ttk.LabelFrame(parent, text="Material da Peça", padding=10)
        frame.pack(fill="x", pady=5)

        materiais = dm.load_materials()  # lido de data/materials.json (fonte unica)
        # mapa nome de exibicao -> chave interna, para o combobox mostrar o nome
        self._mapa_materiais = {v.get("nome", k): k for k, v in materiais.items()}

        # Seleção do material
        ttk.Label(frame, text="Material:").grid(row=0, column=0, sticky="w", pady=2)
        primeiro_nome = next(iter(self._mapa_materiais), "")
        self.vars['material'] = tk.StringVar(value=primeiro_nome)
        self.combo_material = ttk.Combobox(
            frame, textvariable=self.vars['material'],
            values=list(self._mapa_materiais.keys()), state="readonly", width=28
        )
        self.combo_material.grid(row=0, column=1, sticky="w", pady=2)
        self.combo_material.bind("<<ComboboxSelected>>", self._atualizar_kienzle)

        # Parâmetros Kienzle (preenchidos automaticamente ao escolher o material,
        # mas editaveis manualmente para ajuste fino pontual)
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
        """Abre a janela de Cadastro de Materiais/Ferramentas e atualiza os
        combobox desta aba quando ela for fechada."""
        CadastroDialog(self.winfo_toplevel(), on_close_callback=self._refresh_combos_apos_cadastro)

    def _refresh_combos_apos_cadastro(self):
        # Atualiza combobox de ferramenta
        self.combo_tool_material.configure(values=list(dm.load_tools().keys()))
        # Atualiza combobox de material (nome -> chave)
        materiais = dm.load_materials()
        self._mapa_materiais = {v.get("nome", k): k for k, v in materiais.items()}
        self.combo_material.configure(values=list(self._mapa_materiais.keys()))
    
    def _criar_secao_avancada(self, parent, row=0):
        frame = ttk.LabelFrame(parent, text="Parâmetros Avançados", padding=10)
        frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=5)
        
        params = [
            ("Ângulo de atrito (°)", "friction_angle", 25),
            ("Ângulo de cisalhamento (°)", "shear_angle", 30),
            ("Rigidez X (N/m)", "stiffness_x", 1e7),
            ("Rigidez Y (N/m)", "stiffness_y", 1e7),
            ("Resolução da malha", "mesh_resolution", 50),
        ]
        
        for i, (label, key, default) in enumerate(params):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky="w", pady=2)
            var = tk.DoubleVar(value=default)
            entry = ttk.Entry(frame, textvariable=var, width=12)
            entry.grid(row=i, column=1, sticky="w", pady=2)
            self.vars[key] = var
    
    def _atualizar_kienzle(self, event=None):
        """Atualiza os parâmetros Kienzle com base no material selecionado,
        lendo diretamente de data/materials.json (fonte unica de dados)."""
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
        """Carrega os dados padrão de exemplo"""
        self.vars['modulo'].set(2.2)
        self.vars['z_peca'].set(43)
        self.vars['face_width'].set(20)
        self.vars['inner_radius'].set(47.3)
        self.vars['outer_radius'].set(60.4)
        self.vars['z_ferramenta'].set(14)
        self.vars['rake_angle'].set(5)
        self.vars['clearance_angle'].set(6)
        self.vars['tool_material'].set("HSS-Co")
        self.vars['spm'].set(400)
        self.vars['stroke_length'].set(23.8)
        self.vars['circular_feed'].set(0.25)
        self.vars['radial_feed'].set(0.05)
        self.vars['depth'].set(3)
        self.vars['cooling'].set("Com fluido")
        # Seleciona o material "C45" pelo nome cadastrado no JSON (chave interna: C45)
        nome_c45 = next((n for n, k in self._mapa_materiais.items() if k == "C45"), None)
        if nome_c45:
            self.vars['material'].set(nome_c45)
        self._atualizar_kienzle()
        self.vars['friction_angle'].set(25)
        self.vars['shear_angle'].set(30)
        self.vars['stiffness_x'].set(1e7)
        self.vars['stiffness_y'].set(1e7)
        self.vars['mesh_resolution'].set(50)
    
    def get_params(self):
        """Retorna todos os parâmetros como dicionário"""
        params = {}
        for key, var in self.vars.items():
            try:
                params[key] = var.get()
            except:
                params[key] = None
        return params
    
    def _iniciar_simulacao(self):
        """Inicia a simulação com os parâmetros atuais"""
        params = self.get_params()
        
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
            self._atualizar_kienzle()
            self.main.set_status(f"Parâmetros carregados de {filename}")