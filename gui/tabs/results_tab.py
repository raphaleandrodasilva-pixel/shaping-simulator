"""
Aba de Resultados - Análise e Relatórios
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class ResultsTab(ttk.Frame):
    """
    Aba para exibição de resultados detalhados
    """
    
    def __init__(self, parent, main_window):
        super().__init__(parent)
        self.main = main_window
        self.resultados = None
        
        self._build_layout()
    
    def _build_layout(self):
        # Painel superior - resumo
        self.summary_frame = ttk.LabelFrame(self, text="Resumo da Simulação", padding=10)
        self.summary_frame.pack(fill="x", padx=5, pady=5)
        
        # Grid de resultados
        resultados = [
            ("Força Máxima de Corte", "fc_max", "--", "N"),
            ("Força Média de Corte", "fc_avg", "--", "N"),
            ("Desgaste Total (Cratera)", "wear_crater", "--", "µm"),
            ("Desgaste Total (Flanco)", "wear_flank", "--", "µm"),
            ("Tempo Total de Corte", "total_time", "--", "s"),
            ("Número de Golpes", "total_strokes", "--", ""),
        ]
        
        self._vars = {}
        for i, (label, key, default, unit) in enumerate(resultados):
            row = i // 3
            col = i % 3
            
            frame = ttk.Frame(self.summary_frame)
            frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=5)
            self.summary_frame.grid_columnconfigure(col, weight=1)
            
            ttk.Label(frame, text=label, font=("Segoe UI", 9, "bold")).pack(anchor="w")
            
            var = tk.StringVar(value=default)
            ttk.Label(frame, textvariable=var, font=("Segoe UI", 14)).pack(anchor="w")
            ttk.Label(frame, text=unit, font=("Segoe UI", 8), foreground="#666").pack(anchor="w")
            
            self._vars[key] = var
        
        # Gráficos
        graph_frame = ttk.Frame(self)
        graph_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Criar gráficos
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        self.fig.tight_layout(pad=3.0)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Configurar eixos
        self.ax1.set_title("Forças de Corte")
        self.ax1.set_xlabel("Golpes")
        self.ax1.set_ylabel("Força (N)")
        self.ax1.grid(True, alpha=0.3)
        
        self.ax2.set_title("Desgaste da Ferramenta")
        self.ax2.set_xlabel("Golpes")
        self.ax2.set_ylabel("Desgaste (µm)")
        self.ax2.grid(True, alpha=0.3)
        
        self.ax3.set_title("Distribuição do Desgaste")
        self.ax3.set_xlabel("Posição na aresta")
        self.ax3.set_ylabel("Desgaste (µm)")
        self.ax3.grid(True, alpha=0.3)
        
        self.ax4.set_title("Perfil Final")
        self.ax4.set_xlabel("X (mm)")
        self.ax4.set_ylabel("Y (mm)")
        self.ax4.set_aspect('equal')
        self.ax4.grid(True, alpha=0.3)
        
        # Botões de exportação
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=5, pady=10)
        
        ttk.Button(btn_frame, text="📊 Exportar CSV", 
                  command=self.exportar_csv).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📄 Gerar PDF", 
                  command=self.gerar_pdf).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🖨️ Imprimir", 
                  command=self.imprimir).pack(side="left", padx=5)
    
    def atualizar(self, resultados):
        """Atualiza os resultados exibidos"""
        self.resultados = resultados
        
        if resultados is None or len(resultados) == 0:
            return
        
        # Extrai dados
        fc = [r['forces']['Fc'] for r in resultados]
        wear = [r['wear']['total'] for r in resultados]
        
        # Atualiza resumo
        self._vars['fc_max'].set(f"{max(fc):.0f}")
        self._vars['fc_avg'].set(f"{np.mean(fc):.0f}")
        self._vars['wear_crater'].set(f"{resultados[-1]['wear']['crater']:.3f}")
        self._vars['wear_flank'].set(f"{resultados[-1]['wear']['flank']:.3f}")
        self._vars['total_time'].set(f"{resultados[-1]['time']:.1f}")
        self._vars['total_strokes'].set(f"{len(resultados)}")
        
        # Atualiza gráficos
        self._atualizar_graficos(resultados)
    
    def _atualizar_graficos(self, resultados):
        """Atualiza os gráficos com os resultados"""
        n = len(resultados)
        strokes = list(range(n))
        
        # Forças
        self.ax1.clear()
        fc = [r['forces']['Fc'] for r in resultados]
        ff = [r['forces']['Ff'] for r in resultados]
        fp = [r['forces']['Fp'] for r in resultados]
        
        self.ax1.plot(strokes, fc, 'b-', label='Fc', linewidth=2)
        self.ax1.plot(strokes, ff, 'g-', label='Ff', linewidth=2)
        self.ax1.plot(strokes, fp, 'r-', label='Fp', linewidth=2)
        self.ax1.set_xlabel("Golpes")
        self.ax1.set_ylabel("Força (N)")
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend()
        
        # Desgaste
        self.ax2.clear()
        wear_crater = [r['wear']['crater'] for r in resultados]
        wear_flank = [r['wear']['flank'] for r in resultados]
        wear_total = [r['wear']['total'] for r in resultados]
        
        self.ax2.plot(strokes, wear_crater, 'r-', label='Cratera', linewidth=2)
        self.ax2.plot(strokes, wear_flank, 'g-', label='Flanco', linewidth=2)
        self.ax2.plot(strokes, wear_total, 'b--', label='Total', linewidth=2)
        self.ax2.set_xlabel("Golpes")
        self.ax2.set_ylabel("Desgaste (µm)")
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend()
        
        # Distribuição do desgaste
        self.ax3.clear()
        if n > 0:
            edge_pos = np.linspace(0, 1, 20)
            wear_dist = [wear_total[-1] * (0.5 + 0.5 * np.sin(p * np.pi)) for p in edge_pos]
            self.ax3.bar(edge_pos, wear_dist, width=0.03, color='red', alpha=0.6)
        self.ax3.set_xlabel("Posição na aresta de corte")
        self.ax3.set_ylabel("Desgaste (µm)")
        self.ax3.grid(True, alpha=0.3)
        
        # Perfil final
        self.ax4.clear()
        if hasattr(self.main.tab_simulation, 'engine'):
            blank = self.main.tab_simulation.engine.blank
            X = blank['X']
            Y = blank['Y']
            active = blank['active']
            
            if active.any():
                X_active = X[active]
                Y_active = Y[active]
                if len(X_active) > 0:
                    angles = np.arctan2(Y_active.flatten(), X_active.flatten())
                    idx = np.argsort(angles)
                    self.ax4.plot(X_active.flatten()[idx], Y_active.flatten()[idx],
                                'b-', linewidth=1.5, alpha=0.8)
                    
                    r_outer = np.max(np.sqrt(X_active**2 + Y_active**2))
                    r_inner = np.min(np.sqrt(X_active**2 + Y_active**2))
                    theta = np.linspace(0, 2*np.pi, 100)
                    self.ax4.plot(r_outer*np.cos(theta), r_outer*np.sin(theta),
                                'r--', alpha=0.5, label='Diâmetro externo')
                    self.ax4.plot(r_inner*np.cos(theta), r_inner*np.sin(theta),
                                'g--', alpha=0.5, label='Diâmetro interno')
        
        self.ax4.set_xlabel("X (mm)")
        self.ax4.set_ylabel("Y (mm)")
        self.ax4.set_aspect('equal')
        self.ax4.grid(True, alpha=0.3)
        self.ax4.legend()
        
        self.fig.tight_layout()
        self.canvas.draw()
    
    def exportar_csv(self):
        """Exporta os resultados para CSV"""
        if self.resultados is None:
            messagebox.showwarning("Sem dados", "Nenhum resultado para exportar")
            return
        
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Golpe', 'Tempo', 'Fc', 'Ff', 'Fp', 'Wear_Crater', 'Wear_Flank'])
                for i, r in enumerate(self.resultados):
                    writer.writerow([
                        i, r['time'],
                        r['forces']['Fc'], r['forces']['Ff'], r['forces']['Fp'],
                        r['wear']['crater'], r['wear']['flank']
                    ])
            self.main.set_status(f"Dados exportados para {filename}")
    
    def gerar_pdf(self):
        """Gera um relatório PDF"""
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            
            filename = "relatorio_shaping.pdf"
            doc = SimpleDocTemplate(filename, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # Título
            elements.append(Paragraph("Relatório de Simulação - Shaping", styles['Title']))
            elements.append(Spacer(1, 20))
            
            # Parâmetros
            params = self.main.get_params()
            data = [['Parâmetro', 'Valor']]
            for key, val in params.items():
                data.append([str(key), str(val)])
            
            table = Table(data, colWidths=[100, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))
            
            # Resultados
            if self.resultados:
                data = [['Golpe', 'Fc (N)', 'Ff (N)', 'Fp (N)', 'Wear (µm)']]
                for i, r in enumerate(self.resultados[-20:]):
                    data.append([
                        str(i), f"{r['forces']['Fc']:.0f}", f"{r['forces']['Ff']:.0f}",
                        f"{r['forces']['Fp']:.0f}", f"{r['wear']['total']:.3f}"
                    ])
                table = Table(data, colWidths=[60, 60, 60, 60, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                elements.append(table)
            
            doc.build(elements)
            self.main.set_status(f"Relatório PDF gerado: {filename}")
            
        except ImportError:
            messagebox.showerror("Erro", "reportlab não instalado. Execute: pip install reportlab")
    
    def imprimir(self):
        """Imprime a janela de resultados"""
        messagebox.showinfo("Imprimir", "Função em desenvolvimento")
    
    def comparar_estrategias(self):
        """Compara diferentes estratégias de avanço"""
        messagebox.showinfo("Comparar Estratégias", "Função em desenvolvimento")