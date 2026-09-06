"""
Janela Principal da Interface Gráfica
"""

import tkinter as tk
from tkinter import ttk, messagebox
from gui.tabs.input_tab import InputTab
from gui.tabs.simulation_tab import SimulationTab
from gui.tabs.results_tab import ResultsTab
from gui.styles import configure_styles

class MainWindow:
    """
    Janela principal com abas
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Shaping Simulator Pro v2.0")
        self.root.geometry("1280x800")
        self.root.minsize(1024, 600)
        
        # Configura estilos
        configure_styles()
        
        # Cria o notebook (abas)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Abas
        self.tab_input = InputTab(self.notebook, self)
        self.tab_simulation = SimulationTab(self.notebook, self)
        self.tab_results = ResultsTab(self.notebook, self)
        
        self.notebook.add(self.tab_input, text="📐 Entrada de Dados")
        self.notebook.add(self.tab_simulation, text="⚙️ Simulação")
        self.notebook.add(self.tab_results, text="📊 Resultados")
        
        # Barra de status
        self.status_bar = ttk.Label(root, text="Pronto", relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x", padx=5, pady=2)
        
        # Menu
        self._criar_menu()
    
    def _criar_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        file_menu.add_command(label="Carregar Parâmetros", 
                             command=self.tab_input.carregar_parametros)
        file_menu.add_command(label="Salvar Parâmetros", 
                             command=self.tab_input.salvar_parametros)
        file_menu.add_separator()
        file_menu.add_command(label="Exportar Resultados (CSV)", 
                             command=self.tab_results.exportar_csv)
        file_menu.add_command(label="Gerar Relatório PDF", 
                             command=self.tab_results.gerar_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self.root.quit)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self._mostrar_sobre)
    
    def _mostrar_sobre(self):
        messagebox.showinfo(
            "Sobre",
            "Shaping Simulator Pro v2.0\n\n"
            "Baseado nos artigos:\n"
            "- NASA: Computer Simulation of Gear Tooth Manufacturing Processes (1990)\n"
            "- ETH: Face-gear drive: Simulation of shaping as manufacturing process (2022)"
        )
    
    def set_status(self, mensagem):
        """Atualiza a barra de status"""
        self.status_bar.config(text=mensagem)
        self.root.update_idletasks()
    
    def get_params(self):
        """Retorna os parâmetros atuais da aba de entrada"""
        return self.tab_input.get_params()