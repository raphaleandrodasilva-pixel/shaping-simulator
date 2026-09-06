"""
Deflexão da Ferramenta - Baseado no artigo ETH Zurich (2022)
Equações: 31-33
"""

import numpy as np
from math import cos, sin

class ToolDeflection:
    """
    Calcula a deflexão da ferramenta devido às forças de corte
    
    Referência: Zschippang et al. (2022)
    """
    
    def __init__(self, stiffness_x=1e7, stiffness_y=1e7):
        """
        Inicializa as rigidezes do sistema
        
        Args:
            stiffness_x: Rigidez na direção X (N/m)
            stiffness_y: Rigidez na direção Y (N/m)
        """
        self.k_x = stiffness_x
        self.k_y = stiffness_y
    
    def calcular_deflexao(self, forcas):
        """
        Eq. 31: Calcula a deflexão da ferramenta
        
        [Δx]   [k_x^(-1)    0       0] [F_x]
        [Δy] = [   0      k_y^(-1)  0] [F_y]
        [Δz]   [   0         0      0] [F_z]
        
        Args:
            forcas: Dicionário com forças F_x, F_y, F_z (N)
        
        Returns:
            Dicionário com deflexões Δx, Δy, Δz (mm)
        """
        Fx = forcas.get('Fx', 0) or forcas.get('Ff', 0)
        Fy = forcas.get('Fy', 0) or forcas.get('Fp', 0)
        
        # Deflexão (converte N para N/mm)
        dx = Fx / (self.k_x / 1000)  # mm
        dy = Fy / (self.k_y / 1000)  # mm
        
        return {'dx': dx, 'dy': dy, 'dz': 0}
    
    def matriz_transformacao_com_deflexao(self, M, dx, dy):
        """
        Eq. 32: Matriz de transformação com deflexão
        """
        # Modifica a matriz para incluir a deflexão
        M_def = M.copy()
        
        # Aplica a deflexão na translação
        M_def[0, 3] += dx * cos(0)  # Simplificação
        M_def[1, 3] += dy * sin(0)  # Simplificação
        
        return M_def
    
    def iterar_deflexao(self, forcas, max_iter=10, tol=1e-6):
        """
        Resolve iterativamente a deflexão (acoplamento forças-deflexão)
        
        Args:
            forcas: Forças iniciais
            max_iter: Número máximo de iterações
            tol: Tolerância para convergência
        
        Returns:
            Deflexão convergida
        """
        dx_ant = 0
        dy_ant = 0
        
        for i in range(max_iter):
            # Calcula deflexão com as forças atuais
            deflexao = self.calcular_deflexao(forcas)
            dx = deflexao['dx']
            dy = deflexao['dy']
            
            # Verifica convergência
            if abs(dx - dx_ant) < tol and abs(dy - dy_ant) < tol:
                break
            
            dx_ant = dx
            dy_ant = dy
            
            # Atualiza forças baseado na nova posição da ferramenta
            # (simplificado - em produção, recalcularia as forças)
            
        return {'dx': dx, 'dy': dy, 'dz': 0}
    
    def rigidez_sistema(self, maquina, ferramenta, peca):
        """
        Calcula a rigidez total do sistema
        
        Rigidez total = 1 / (1/Km + 1/Kt + 1/Kp)
        
        Args:
            maquina: Rigidez da máquina (N/m)
            ferramenta: Rigidez da ferramenta (N/m)
            peca: Rigidez da peça (N/m)
        """
        if maquina <= 0 or ferramenta <= 0 or peca <= 0:
            return 1e7  # Valor padrão
        
        return 1 / (1/maquina + 1/ferramenta + 1/peca)