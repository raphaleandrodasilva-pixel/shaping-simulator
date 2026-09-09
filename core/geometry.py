"""
Geometria de Engrenagens - Baseado nos artigos NASA e ETH
"""

import numpy as np
from math import cos, sin, tan, radians, pi

class GearGeometry:
    """
    Geometria de engrenagens para shaping
    """
    
    def __init__(self, modulo, z_peca, z_ferramenta, angulo_pressao=20):
        """
        Inicializa a geometria da engrenagem
        
        Args:
            modulo: Módulo (mm)
            z_peca: Número de dentes da peça
            z_ferramenta: Número de dentes da ferramenta
            angulo_pressao: Ângulo de pressão (graus)
        """
        self.m = modulo
        self.z1 = z_peca
        self.z2 = z_ferramenta
        self.alpha = radians(angulo_pressao)
    
    @property
    def d_primitivo_peca(self):
        """Diâmetro primitivo da peça (mm)"""
        return self.m * self.z1
    
    @property
    def d_primitivo_ferramenta(self):
        """Diâmetro primitivo da ferramenta (mm)"""
        return self.m * self.z2
    
    @property
    def r_primitivo_peca(self):
        """Raio primitivo da peça (mm)"""
        return self.d_primitivo_peca / 2
    
    @property
    def r_primitivo_ferramenta(self):
        """Raio primitivo da ferramenta (mm)"""
        return self.d_primitivo_ferramenta / 2
    
    @property
    def d_base_peca(self):
        """Diâmetro de base da peça (mm)"""
        return self.d_primitivo_peca * cos(self.alpha)
    
    @property
    def d_base_ferramenta(self):
        """Diâmetro de base da ferramenta (mm)"""
        return self.d_primitivo_ferramenta * cos(self.alpha)
    
    @property
    def d_externo_peca(self):
        """Diâmetro externo da peça (mm)"""
        return self.m * (self.z1 + 2)
    
    @property
    def d_interno_peca(self):
        """Diâmetro interno da peça (mm)"""
        return self.m * (self.z1 - 2.5)
    
    def altura_dente(self):
        """Altura total do dente (mm)"""
        return 2.25 * self.m
    
    def addendum(self):
        """Altura da cabeça do dente (mm)"""
        return self.m
    
    def dedendum(self):
        """Altura do pé do dente (mm)"""
        return 1.25 * self.m
    
    def passo_circular(self):
        """Passo circular (mm)"""
        return pi * self.m
    
    def espessura_dente(self):
        """Espessura do dente no círculo primitivo (mm)"""
        return self.passo_circular() / 2
    
    def comprimento_engate(self):
        """
        Comprimento de engate teórico (mm)
        Conforme DIN 3992
        """
        r1 = self.r_primitivo_peca
        r2 = self.r_primitivo_ferramenta
        ra1 = self.d_externo_peca / 2
        ra2 = self.d_base_ferramenta / 2
        
        # Comprimento de engate
        L = np.sqrt(ra1**2 - (r1 * cos(self.alpha))**2) + \
            np.sqrt(ra2**2 - (r2 * cos(self.alpha))**2) - \
            (r1 + r2) * sin(self.alpha)
        
        return max(L, 0)
    
    def relacao_transmissao(self):
        """Relação de transmissão (ferramenta/peça)"""
        return self.z2 / self.z1
    
    def matriz_transformacao(self, phi_c, phi_2, gamma, E, H_2, d_r, dx=0, dy=0):
        """
        Eq. 16 do artigo ETH: Matriz de transformação M_{2c}(t)
        Com deflexão da ferramenta (Eq. 32)
        
        Args:
            phi_c: Ângulo de rotação do cutter
            phi_2: Ângulo de rotação da peça
            gamma: Ângulo do eixo (rad)
            E: Offset do eixo (mm)
            H_2: Altura do dente da face-gear (mm)
            d_r: Posição radial (mm)
            dx, dy: Deflexão da ferramenta (mm)
        """
        c_p = cos(phi_c)
        s_p = sin(phi_c)
        c_2 = cos(phi_2)
        s_2 = sin(phi_2)
        c_g = cos(gamma)
        s_g = sin(gamma)
        
        E_eff = E + dx
        H_eff = H_2 - d_r + dy
        
        # Matriz 4x4 de transformação
        M = np.array([
            [c_p*c_2 + s_p*s_2*c_g, -s_p*c_2 + c_p*s_2*c_g, -s_2*s_g, -E_eff*c_2],
            [-c_p*s_2 + s_p*c_2*c_g, s_p*s_2 + c_p*c_2*c_g, -c_2*s_g, E_eff*s_2],
            [s_p*s_g, c_p*s_g, c_g, H_eff/s_g if abs(s_g) > 1e-6 else H_eff],
            [0, 0, 0, 1]
        ])
        
        return M
    
    def ponto_transformado(self, ponto, M):
        """
        Eq. 18: Transforma um ponto da ferramenta para o sistema da peça
        """
        r = np.array([ponto[0], ponto[1], ponto[2], 1])
        return M @ r
    
    def condicao_interseccao(self, x, y, z, gamma, l_2_ref):
        """
        Eq. 19: Verifica se o ponto está na seção correta
        """
        if abs(gamma - pi/2) < 1e-6:
            return np.sqrt(x**2 + y**2) - l_2_ref
        else:
            return cos(gamma) * (x + tan(gamma) * np.sqrt(x**2 + y**2)) - l_2_ref
    
    def involuto_parametrico(self, phi, r_base, sentido=1):
        """
        Gera pontos de um involuto paramétrico
        
        Args:
            phi: Ângulo do involuto (rad)
            r_base: Raio da base
            sentido: 1 para direita, -1 para esquerda
        """
        x = r_base * (np.sin(phi) - phi * np.cos(phi))
        y = r_base * (np.cos(phi) + phi * np.sin(phi))
        
        if sentido == -1:
            x = -x
        
        return x, y
    
    def perfil_dente(self, z, r_base, phi_max, n_points=50):
        """
        Gera o perfil completo de um dente
        """
        phi = np.linspace(0, phi_max, n_points)
        
        # Lado direito do dente
        x_r, y_r = self.involuto_parametrico(phi, r_base, 1)
        
        # Lado esquerdo do dente (espelhado e rotacionado)
        theta = 2 * pi / z  # Ângulo entre dentes
        phi_esq = np.linspace(0, phi_max, n_points)
        x_l, y_l = self.involuto_parametrico(phi_esq, r_base, -1)
        
        # Rotaciona para a posição correta
        x_l_rot = x_l * cos(theta) - y_l * sin(theta)
        y_l_rot = x_l * sin(theta) + y_l * cos(theta)
        
        return np.column_stack([x_r, y_r]), np.column_stack([x_l_rot, y_l_rot])