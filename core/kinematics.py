"""
Cinemática do Shaping - Baseado no artigo ETH Zurich (2022)
Equações: 1-14
"""

import numpy as np
from math import pi, cos, sin, tan, sqrt

class ShapingKinematics:
    """
    Implementa as equações cinemáticas do artigo ETH
    
    Referência: Zschippang et al. (2022)
    Face-gear drive: Simulation of shaping as manufacturing process
    """
    
    def __init__(self, spm, stroke_length, crank_length=None):
        """
        Inicializa os parâmetros cinemáticos
        
        Args:
            spm: Golpes por minuto (strokes per minute)
            stroke_length: Comprimento do curso (mm)
            crank_length: Comprimento da manivela (mm) - opcional
        """
        self.spm = spm
        self.L_st = stroke_length  # mm
        self.L_crank = crank_length or stroke_length * 10  # mm
        self.f_st = spm / 60  # Hz (Eq. 3)
        self.omega_st = 2 * pi * self.f_st  # rad/s (Eq. 3)
        
    def posicao_curso(self, t, l_c_top=0):
        """
        Eq. 1: Posição do shaper cutter no tempo t
        
        l_c(t) = l_c_top - (L_st/2)(1 - cos(omega_st*t)) + 
                 sqrt(L_crank^2 - (L_st^2/4)*sin^2(omega_st*t)) - L_crank
        """
        if self.L_crank > self.L_st * 10:
            # Eq. 2: Simplificação para máquinas modernas
            return l_c_top - (self.L_st / 2) * (1 - cos(self.omega_st * t))
        else:
            # Eq. 1 completa (slider crank)
            term1 = self.L_st / 2 * (1 - cos(self.omega_st * t))
            term2 = sqrt(self.L_crank**2 - (self.L_st**2 / 4) * 
                        sin(self.omega_st * t)**2)
            return l_c_top - term1 + term2 - self.L_crank
    
    def velocidade_curso(self, t):
        """
        Velocidade instantânea do curso (derivada da Eq. 2)
        """
        return -(self.L_st / 2) * self.omega_st * sin(self.omega_st * t)
    
    def aceleracao_curso(self, t):
        """
        Aceleração instantânea do curso
        """
        return -(self.L_st / 2) * self.omega_st**2 * cos(self.omega_st * t)
    
    def velocidade_maxima(self):
        """
        Velocidade máxima no ponto médio (m/min)
        v_max = π * L_st * SPM / 1000
        """
        return pi * self.L_st * self.spm / 1000  # m/min
    
    def aceleracao_maxima(self):
        """
        Aceleração máxima (m/s²)
        """
        omega = pi * self.spm / 30
        return (omega**2 * self.L_st / 2) / 1000
    
    def velocidade_rotacao_peca(self, a_circ, N_c, N_2, r_c):
        """
        Eq. 4: Velocidade angular da face-gear
        
        ω2 = a_circ * f_st * m_2c / r_c
        
        Args:
            a_circ: Avanço circular (mm/golpe)
            N_c: Número de dentes da ferramenta
            N_2: Número de dentes da peça
            r_c: Raio primitivo da ferramenta (mm)
        """
        m_2c = N_c / N_2  # Eq. 5
        return a_circ * self.f_st * m_2c / r_c  # rad/s
    
    def angulo_rotacao_ferramenta(self, t, phi_2, N_c, N_2, helix_angle=0, r_c=1):
        """
        Eq. 7: Ângulo de rotação da ferramenta
        
        φc(t) = φ2(t)/m_2c + l_c(t) * p
        
        Para engrenagens helicoidais, p = tan(β) / r_c
        """
        m_2c = N_c / N_2
        phi_c = phi_2 / m_2c
        
        if helix_angle != 0:
            p = tan(helix_angle) / r_c  # Eq. 8
            l_c = self.posicao_curso(t)
            phi_c += l_c * p
            
        return phi_c
    
    def posicao_radial(self, t, d_r_start, d_r_end, a_r_start, a_r_end):
        """
        Eq. 9-14: Posição radial da ferramenta ao longo do tempo
        
        Args:
            t: Tempo (s)
            d_r_start: Posição radial inicial (mm)
            d_r_end: Posição radial final (mm)
            a_r_start: Avanço radial inicial (mm/golpe)
            a_r_end: Avanço radial final (mm/golpe)
        """
        v_r_start = a_r_start * self.f_st  # Eq. 9
        v_r_end = a_r_end * self.f_st  # Eq. 10
        
        # Eq. 11: Tempo para movimento radial
        t_r = (2 * (d_r_end - d_r_start)) / (v_r_start + v_r_end)
        
        # Eq. 12: Aceleração radial
        a_acc = (v_r_end - v_r_start) / t_r if t_r > 0 else 0
        
        # Eq. 14: Posição radial
        if t < t_r:
            return (a_acc / 2) * t**2 + v_r_start * t + d_r_start
        else:
            return d_r_end
    
    def perfil_velocidade_golpe(self, theta):
        """
        Perfil de velocidade dentro de um golpe
        v(θ) = v_max * sin(θ)
        
        Args:
            theta: Ângulo no golpe (0 a 180°)
        """
        theta_rad = np.radians(theta)
        v_max = self.velocidade_maxima()
        return v_max * np.sin(theta_rad)
    
    def perfil_posicao_golpe(self, theta):
        """
        Perfil de posição dentro de um golpe
        l(θ) = (L_st/2) * (1 - cos(θ))
        """
        theta_rad = np.radians(theta)
        return (self.L_st / 2) * (1 - np.cos(theta_rad))