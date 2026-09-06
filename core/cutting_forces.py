"""
Forças de Corte - Baseado no artigo ETH Zurich (2022)
Equações: 20-30
"""

import numpy as np
from math import cos, sin, tan, radians, sqrt, pi

class CuttingForces:
    """
    Implementa o modelo de forças de Kienzle para shaping
    
    Referência: Zschippang et al. (2022)
    """
    
    def __init__(self, k_c1_1, m_c, k_f1_1, m_f, k_p1_1=0, m_p=0):
        """
        Inicializa os parâmetros de Kienzle
        
        Args:
            k_c1_1: Força específica de corte (N/mm²) para b=1, h=1
            m_c: Expoente da força de corte
            k_f1_1: Força específica de avanço (N/mm²)
            m_f: Expoente da força de avanço
            k_p1_1: Força específica passiva (N/mm²)
            m_p: Expoente da força passiva
        """
        self.k_c1_1 = k_c1_1
        self.m_c = m_c
        self.k_f1_1 = k_f1_1
        self.m_f = m_f
        self.k_p1_1 = k_p1_1
        self.m_p = m_p
        
        # Constantes para correção de velocidade
        self.v_ref = 100  # m/min (referência)
    
    def forcas_ortogonais(self, h, b, K_c=1.0, K_f=1.0, K_p=1.0):
        """
        Eq. 20: Forças de corte (Kienzle - corte ortogonal)
        
        F_c = k_c1_1 * h^(1-m_c) * b * K_c
        F_f = k_f1_1 * h^(1-m_f) * b * K_f
        F_p = k_p1_1 * h^(1-m_p) * b * K_p
        
        Args:
            h: Espessura do cavaco (mm)
            b: Largura do cavaco (mm)
            K_c, K_f, K_p: Fatores de correção
        """
        F_c = self.k_c1_1 * h**(1 - self.m_c) * b * K_c if h > 0 else 0
        F_f = self.k_f1_1 * h**(1 - self.m_f) * b * K_f if h > 0 else 0
        F_p = self.k_p1_1 * h**(1 - self.m_p) * b * K_p if h > 0 else 0
        
        return {'Fc': F_c, 'Ff': F_f, 'Fp': F_p}
    
    def shear_angle_lee_shaffer(self, gamma_n, beta_a):
        """
        Eq. 25: Ângulo de cisalhamento (Lee-Shaffer)
        
        φ_sn = π/4 + γ_n - β_a
        """
        return pi/4 + gamma_n - beta_a
    
    def shear_angle_merchant(self, gamma_n, beta_a):
        """
        Ângulo de cisalhamento (Merchant)
        
        φ_sn = π/4 + (γ_n - β_a)/2
        """
        return pi/4 + (gamma_n - beta_a)/2
    
    def forcas_obliquas(self, tau_s, b, h, phi_sn, beta_n, gamma_n, 
                        lambda_s, eta_c, K_ce=0, K_fe=0):
        """
        Eq. 27: Forças para corte oblíquo
        
        Transformação do corte ortogonal para oblíquo
        """
        sin_phi = sin(phi_sn)
        cos_phi = cos(phi_sn)
        
        # Denominador comum
        denom = sqrt(cos(phi_sn + beta_n - gamma_n)**2 + 
                     tan(eta_c)**2 * sin(beta_n)**2)
        
        if denom < 1e-10:
            denom = 1e-10
        
        # Força de corte (Eq. 27)
        F_c = (tau_s * b * h / sin_phi) * (
            cos(beta_n - gamma_n) + tan(lambda_s) * tan(eta_c) * sin(beta_n)
        ) / denom + K_ce * cos(lambda_s) * b
        
        # Força de avanço (Eq. 27)
        F_f = (tau_s * b * h / (sin_phi * cos(lambda_s))) * (
            sin(beta_n - gamma_n)
        ) / denom + K_fe * b
        
        # Força passiva (Eq. 27)
        F_p = (tau_s * b * h / sin_phi) * (
            cos(beta_n - gamma_n) * tan(lambda_s) - tan(eta_c) * sin(beta_n)
        ) / denom + K_ce * sin(lambda_s) * b
        
        return {'Fc': F_c, 'Ff': F_f, 'Fp': F_p}
    
    def fatores_correcao(self, gamma, gamma_0=6, v=100, K_sp=1.1, K_wear=1.0):
        """
        Eq. 48-50: Fatores de correção para Kienzle
        
        K_c = K_y * K_sp * K_v * K_wear
        
        Args:
            gamma: Ângulo de saída efetivo (graus)
            gamma_0: Ângulo de saída base (graus) - 6° para aço
            v: Velocidade de corte (m/min)
            K_sp: Fator de compressão do cavaco (1.1 para shaping)
            K_wear: Fator de desgaste da ferramenta
        """
        # Eq. 48: Correção do ângulo de saída
        K_y = 1 - (gamma - gamma_0) / 100 if abs(gamma - gamma_0) < 100 else 1.0
        
        # Eq. 49: Correção da velocidade
        K_v = (self.v_ref / v)**0.1 if v > 0 else 1.0
        
        # Eq. 50: Fator total
        K_total = K_y * K_sp * K_v * K_wear
        
        return K_total
    
    def tensao_cisalhamento(self, F_s, phi_sn, b, h):
        """
        Eq. 23: Tensão de cisalhamento na zona primária de deformação
        
        τ_s = (F_s * sin(φ_sn)) / (b * h)
        """
        if b * h < 1e-10:
            return 0
        return (F_s * sin(phi_sn)) / (b * h)
    
    def forca_cisalhamento(self, F_c, F_f, phi_sn):
        """
        Eq. 22: Força de cisalhamento
        
        F_s = F_c * cos(φ_sn) - F_f * sin(φ_sn)
        """
        return F_c * cos(phi_sn) - F_f * sin(phi_sn)
    
    def chip_flow_angle(self, phi_sn, beta_n, gamma_n, lambda_s):
        """
        Eq. 29: Ângulo de fluxo do cavaco (Armarego)
        
        tan(β_n + φ_sn) = (tan(λ_s) * cos(γ_n)) / (tan(η_c) - sin(γ_n) * tan(λ_s))
        """
        # Resolve para η_c
        tan_beta_phi = tan(beta_n + phi_sn)
        denom = sin(gamma_n) * tan(lambda_s)
        
        if abs(tan_beta_phi) < 1e-10:
            return 0
        
        eta_c = np.arctan((tan(lambda_s) * cos(gamma_n) / tan_beta_phi) + denom)
        return eta_c
    
    def calcular_forcas_totais(self, pontos_contato, v_c, gamma_n, lambda_s, 
                               material_params):
        """
        Calcula as forças totais atuando na ferramenta
        
        Args:
            pontos_contato: Lista de pontos de contato com suas espessuras
            v_c: Velocidade de corte (m/min)
            gamma_n: Ângulo de saída normal (rad)
            lambda_s: Ângulo de inclinação (rad)
            material_params: Parâmetros do material
        """
        # Parâmetros do material
        k_c1_1 = material_params.get('k_c1_1', 1680)
        m_c = material_params.get('m_c', 0.26)
        k_f1_1 = material_params.get('k_f1_1', 340)
        m_f = material_params.get('m_f', 0.68)
        
        # Fator de correção
        K = self.fatores_correcao(
            gamma=np.degrees(gamma_n),
            v=v_c
        )
        
        # Inicializa forças
        F_total = {'Fc': 0, 'Ff': 0, 'Fp': 0}
        
        # Para cada ponto de contato
        for ponto in pontos_contato:
            h = ponto.get('h', 0)  # Espessura do cavaco
            b = ponto.get('b', 1)  # Largura do cavaco
            
            if h < 1e-6:
                continue
            
            # Forças ortogonais
            F = self.forcas_ortogonais(h, b, K, K, K)
            
            # Soma
            F_total['Fc'] += F['Fc']
            F_total['Ff'] += F['Ff']
            F_total['Fp'] += F['Fp']
        
        return F_total