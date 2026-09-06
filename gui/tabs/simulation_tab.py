"""
Aba de Simulação - Visualização em Tempo Real
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from simulation.engine import SimulationEngine

class SimulationTab(ttk.Frame):
    """
    Aba para visualização da simulação
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main = main_window
        self.engine = None
        self.running = False
        self.paused = False
        self.total_strokes = 50
        self.current_stroke = 0
        self.params = {}
        
        self._build_layout()
    
    def _build_layout(self):
        # Painel de controle superior
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=5, pady=5)
        
        # Botões
        self.btn_iniciar = ttk.Button(control_frame, text="▶ Iniciar", 
                                     command=self.iniciar_simulacao)
        self.btn_iniciar.pack(side="left", padx=2)
        
        self.btn_pausar = ttk.Button(control_frame, text="⏸ Pausar", 
                                    command=self.pausar_simulacao, state="disabled")
        self.btn_pausar.pack(side="left", padx=2)
        
        self.btn_parar = ttk.Button(control_frame, text="⏹ Parar", 
                                   command=self.parar_simulacao, state="disabled")
        self.btn_parar.pack(side="left", padx=2)
        
        # Progresso
        self.progress_var = tk.DoubleVar(value=0)
        self.progress = ttk.Progressbar(control_frame, variable=self.progress_var,
                                        maximum=100, length=200)
        self.progress.pack(side="left", padx=10)
        
        self.lbl_progresso = ttk.Label(control_frame, text="0%")
        self.lbl_progresso.pack(side="left", padx=5)
        
        # Label de status
        self.lbl_status = ttk.Label(control_frame, text="Pronto", foreground="#666")
        self.lbl_status.pack(side="right", padx=10)
        
        # Frame do gráfico
        graph_frame = ttk.Frame(self)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Cria os gráficos
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Configura os eixos
        self.ax1.set_title("Peça (Blank)")
        self.ax1.set_xlabel("X (mm)")
        self.ax1.set_ylabel("Y (mm)")
        self.ax1.set_aspect('equal')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_xlim(-70, 70)
        self.ax1.set_ylim(-70, 70)
        
        self.ax2.set_title("Forças de Corte")
        self.ax2.set_xlabel("Golpes")
        self.ax2.set_ylabel("Força (N)")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.set_xlim(0, 50)
        self.ax2.set_ylim(0, 600)
        
        self.ax3.set_title("Desgaste da Ferramenta")
        self.ax3.set_xlabel("Golpes")
        self.ax3.set_ylabel("Desgaste (µm)")
        self.ax3.grid(True, alpha=0.3)
        self.ax3.set_xlim(0, 50)
        self.ax3.set_ylim(0, 10)
        
        self.ax4.set_title("Perfil do Dente")
        self.ax4.set_xlabel("X (mm)")
        self.ax4.set_ylabel("Y (mm)")
        self.ax4.set_aspect('equal')
        self.ax4.grid(True, alpha=0.3)
        self.ax4.set_xlim(-70, 70)
        self.ax4.set_ylim(-70, 70)
        
        # Dados para gráficos
        self.historico_tempo = []
        self.historico_fc = []
        self.historico_ff = []
        self.historico_fp = []
        self.historico_wear = []
    
    def iniciar(self, params):
        """Inicia a simulação com os parâmetros fornecidos"""
        self.params = params
        
        print(f"📥 iniciar() chamado com params: {params}")
        
        # Cria o motor de simulação
        try:
            self.engine = SimulationEngine(params)
            print("✅ Motor de simulação criado com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar motor: {str(e)}")
            self.lbl_status.config(text=f"Erro ao criar motor: {str(e)}")
            return
        
        # Calcula número de golpes
        self.total_strokes = int(params.get('depth', 3) / max(params.get('radial_feed', 0.05), 0.001))
        self.total_strokes = max(self.total_strokes, 20)
        self.total_strokes = min(self.total_strokes, 200)
        
        print(f"📊 Total de golpes: {self.total_strokes}")
        
        self.running = False
        self.paused = False
        self.current_stroke = 0
        
        # Habilita/desabilita botões
        self.btn_iniciar.config(state="normal", text="▶ Iniciar")
        self.btn_pausar.config(state="disabled")
        self.btn_parar.config(state="disabled")
        
        # Limpa históricos
        self.historico_tempo = []
        self.historico_fc = []
        self.historico_ff = []
        self.historico_fp = []
        self.historico_wear = []
        
        # Configura status
        self.lbl_status.config(text=f"Pronto - {self.total_strokes} golpes")
        self.lbl_progresso.config(text="0%")
        self.progress_var.set(0)
        
        # Atualiza limites dos gráficos
        self.ax2.set_xlim(0, self.total_strokes)
        self.ax3.set_xlim(0, self.total_strokes)
        
        # Mostra o estado inicial
        self._mostrar_estado_inicial()
        
        self.lbl_status.config(text=f"Pronto - clique em ▶ Iniciar ({self.total_strokes} golpes)")
        print("✅ iniciar() concluído com sucesso!")
    
    def _mostrar_estado_inicial(self):
        """Mostra o estado inicial da peça"""
        if self.engine is None:
            return
        
        # Plota o blank inicial
        self.ax1.clear()
        blank = self.engine.blank
        X = blank['X']
        Y = blank['Y']
        active = blank['active']
        
        self.ax1.scatter(X[active].flatten(), Y[active].flatten(),
                        s=2, c='blue', alpha=0.5, label='Peça')
        self.ax1.set_title("Peça - Estado Inicial")
        self.ax1.set_xlabel("X (mm)")
        self.ax1.set_ylabel("Y (mm)")
        self.ax1.set_aspect('equal')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_xlim(-70, 70)
        self.ax1.set_ylim(-70, 70)
        self.ax1.legend(fontsize=8)
        
        self.ax2.clear()
        self.ax2.set_title("Forças de Corte")
        self.ax2.set_xlabel("Golpes")
        self.ax2.set_ylabel("Força (N)")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.set_xlim(0, self.total_strokes)
        self.ax2.set_ylim(0, 600)
        
        self.ax3.clear()
        self.ax3.set_title("Desgaste da Ferramenta")
        self.ax3.set_xlabel("Golpes")
        self.ax3.set_ylabel("Desgaste (µm)")
        self.ax3.grid(True, alpha=0.3)
        self.ax3.set_xlim(0, self.total_strokes)
        self.ax3.set_ylim(0, 10)
        
        self.ax4.clear()
        self.ax4.set_title("Perfil do Dente - Aguardando")
        self.ax4.set_xlabel("X (mm)")
        self.ax4.set_ylabel("Y (mm)")
        self.ax4.set_aspect('equal')
        self.ax4.grid(True, alpha=0.3)
        self.ax4.set_xlim(-70, 70)
        self.ax4.set_ylim(-70, 70)
        
        self.fig.tight_layout()
        self.canvas.draw()
        print("✅ Estado inicial desenhado")
    
    def iniciar_simulacao(self):
        """Inicia a simulação propriamente dita"""
        print("🔍 iniciar_simulacao() chamado")
        print(f"🔍 engine = {self.engine}")
        
        if self.engine is None:
            print("❌ engine é None!")
            messagebox.showwarning("Aviso", "Configure os parâmetros primeiro!\n\nClique em 'Iniciar Simulação' na aba de entrada.")
            return
        
        if self.running:
            print("⚠️ Simulação já está rodando")
            return
        
        print(f"✅ Engine OK, total_strokes = {self.total_strokes}")
        
        # Verifica se já terminou
        if self.current_stroke >= self.total_strokes:
            print("🔄 Reiniciando simulação...")
            self.current_stroke = 0
            self.historico_tempo = []
            self.historico_fc = []
            self.historico_ff = []
            self.historico_fp = []
            self.historico_wear = []
            self.engine = SimulationEngine(self.params)
        
        self.running = True
        self.paused = False
        
        self.btn_iniciar.config(state="disabled")
        self.btn_pausar.config(state="normal", text="⏸ Pausar")
        self.btn_parar.config(state="normal")
        
        self.lbl_status.config(text="Simulando...")
        print("▶ Iniciando execução dos passos...")
        
        self._executar_passos()
    
    def _executar_passos(self):
        """Executa um passo da simulação"""
        if not self.running:
            print("⏹ Simulação parada")
            return
        
        if self.paused:
            self.after(100, self._executar_passos)
            return
        
        if self.current_stroke >= self.total_strokes:
            print("✅ Simulação concluída!")
            self._finalizar_simulacao()
            return
        
        # Executa um golpe
        try:
            resultado = self.engine.simular_golpe()
            if self.current_stroke % 5 == 0:
                print(f"  Golpe {self.current_stroke+1}: Fc = {resultado['forces']['Fc']:.1f} N")
        except Exception as e:
            print(f"❌ Erro no golpe {self.current_stroke}: {e}")
            self.lbl_status.config(text=f"Erro: {str(e)}")
            self.running = False
            return
        
        # Atualiza históricos
        self.historico_tempo.append(self.current_stroke)
        self.historico_fc.append(resultado['forces']['Fc'])
        self.historico_ff.append(resultado['forces']['Ff'])
        self.historico_fp.append(resultado['forces']['Fp'])
        self.historico_wear.append(resultado['wear']['total'])
        
        # Atualiza progresso
        progresso = (self.current_stroke / self.total_strokes) * 100
        self.progress_var.set(progresso)
        self.lbl_progresso.config(text=f"{progresso:.0f}%")
        self.lbl_status.config(
            text=f"Golpe {self.current_stroke+1}/{self.total_strokes} - "
                 f"Fc: {resultado['forces']['Fc']:.1f} N"
        )
        
        # Atualiza gráficos
        self._atualizar_graficos(resultado)
        
        self.current_stroke += 1
        
        # Agenda próximo passo
        self.after(50, self._executar_passos)
    
    def _atualizar_graficos(self, resultado):
        """Atualiza os gráficos com o resultado atual"""
        # 1. Peça (Blank)
        self.ax1.clear()
        blank = self.engine.blank
        X = blank['X']
        Y = blank['Y']
        active = blank['active']
        
        if np.any(active):
            self.ax1.scatter(X[active].flatten(), Y[active].flatten(),
                            s=2, c='blue', alpha=0.5, label='Peça')
        
        # Mostra envelope da ferramenta
        if 'envelope' in resultado and resultado['envelope']:
            try:
                env = np.array(resultado['envelope'])
                if len(env) > 0:
                    self.ax1.plot(env[:,0], env[:,1], 'r-', linewidth=2, label='Ferramenta')
            except:
                pass
        
        self.ax1.set_title(f"Peça - Golpe {self.current_stroke+1}")
        self.ax1.set_xlabel("X (mm)")
        self.ax1.set_ylabel("Y (mm)")
        self.ax1.set_aspect('equal')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.set_xlim(-70, 70)
        self.ax1.set_ylim(-70, 70)
        self.ax1.legend(fontsize=8)
        
        # 2. Forças de Corte
        self.ax2.clear()
        if self.historico_fc:
            self.ax2.plot(self.historico_tempo, self.historico_fc, 'b-', label='Fc', linewidth=2)
            self.ax2.plot(self.historico_tempo, self.historico_ff, 'g-', label='Ff', linewidth=2)
            self.ax2.plot(self.historico_tempo, self.historico_fp, 'r-', label='Fp', linewidth=2)
        
        self.ax2.set_title("Forças de Corte")
        self.ax2.set_xlabel("Golpes")
        self.ax2.set_ylabel("Força (N)")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.set_xlim(0, max(10, self.total_strokes))
        self.ax2.legend(fontsize=8)
        
        # 3. Desgaste
        self.ax3.clear()
        if self.historico_wear:
            self.ax3.plot(self.historico_tempo, self.historico_wear, 'r-', linewidth=2)
        
        self.ax3.set_title("Desgaste da Ferramenta")
        self.ax3.set_xlabel("Golpes")
        self.ax3.set_ylabel("Desgaste (µm)")
        self.ax3.grid(True, alpha=0.3)
        self.ax3.set_xlim(0, max(10, self.total_strokes))
        
        # 4. Perfil do dente
        self.ax4.clear()
        if np.any(active):
            X_active = X[active]
            Y_active = Y[active]
            if len(X_active) > 0:
                angles = np.arctan2(Y_active.flatten(), X_active.flatten())
                idx = np.argsort(angles)
                self.ax4.plot(X_active.flatten()[idx], Y_active.flatten()[idx],
                            'b-', linewidth=1.5, alpha=0.8)
        
        self.ax4.set_title(f"Perfil do Dente - {np.sum(active)} pontos")
        self.ax4.set_xlabel("X (mm)")
        self.ax4.set_ylabel("Y (mm)")
        self.ax4.set_aspect('equal')
        self.ax4.grid(True, alpha=0.3)
        self.ax4.set_xlim(-70, 70)
        self.ax4.set_ylim(-70, 70)
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def _finalizar_simulacao(self):
        """Finaliza a simulação"""
        self.running = False
        
        self.btn_iniciar.config(state="normal", text="▶ Reiniciar")
        self.btn_pausar.config(state="disabled")
        self.btn_parar.config(state="disabled")
        
        if self.historico_fc:
            fc_max = max(self.historico_fc)
            fc_avg = sum(self.historico_fc) / len(self.historico_fc)
            wear_total = self.historico_wear[-1] if self.historico_wear else 0
            self.lbl_status.config(
                text=f"✅ Concluído! Fc_max: {fc_max:.0f} N, Fc_avg: {fc_avg:.0f} N, Desgaste: {wear_total:.2f} µm"
            )
            self.main.tab_results.atualizar(self.engine.history['strokes'])
        else:
            self.lbl_status.config(text="✅ Simulação concluída!")
    
    def pausar_simulacao(self):
        """Pausa a simulação"""
        self.paused = not self.paused
        if self.paused:
            self.btn_pausar.config(text="▶ Continuar")
            self.lbl_status.config(text="⏸ Pausado")
        else:
            self.btn_pausar.config(text="⏸ Pausar")
            self.lbl_status.config(text="Simulando...")
            self._executar_passos()
    
    def parar_simulacao(self):
        """Para a simulação"""
        self.running = False
        self.paused = False
        
        self.btn_iniciar.config(state="normal", text="▶ Iniciar")
        self.btn_pausar.config(state="disabled", text="⏸ Pausar")
        self.btn_parar.config(state="disabled")
        
        self.lbl_status.config(text="⏹ Parado")
    
    def otimizar(self):
        """Otimiza os parâmetros de avanço"""
        self.lbl_status.config(text="Otimizando parâmetros...")
        messagebox.showinfo("Otimização", "Função em desenvolvimento")