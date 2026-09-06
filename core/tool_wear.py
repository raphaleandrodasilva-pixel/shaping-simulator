"""
Desgaste da Ferramenta - Baseado no artigo ETH Zurich (2022)
Equações: 34-47
"""

import numpy as np
from math import exp, sqrt, pi, tan, sin, cos, radians

class ToolWear:
    """
    Implementa o modelo de desgaste de Usui
    
    Referência: Zschippang et al. (2022)
    """
    
    def __init__(self, material='steel'):
        """
        Inicializa as constantes de desgaste
        """
        self.material = material
        
        # Constantes de Usui para aço (Eq. 35-36)
        self.C1_crater = 0.01198
        self.C2_crater = 21950  # K
        self.C1_flank = 7.8e-9
        self.C2_flank = 5301.6  # K
        
        # Constantes para o coeficiente de atrito (Eq. 45)
        self.T_star = 955  # °C
        self.T_m = 1500  # °C
        self.q = 1.7
    
    def crater_wear(self, sigma_t, v_c, T_chip, dt=1.0):
        """
        Eq. 35: Desgaste de cratera (Usui)
        
        dW/dt = C1 * σ_t * v_c * exp(-C2/T_chip)
        
        Args:
            sigma_t: Tensão normal na face de saída (N/mm²)
            v_c: Velocidade do cavaco (m/s)
            T_chip: Temperatura do cavaco (K)
            dt: Incremento de tempo (s)
        """
        if T_chip <= 0:
            return 0
        
        return (self.C1_crater * sigma_t * v_c * dt * 
                exp(-self.C2_crater / T_chip))
    
    def flank_wear(self, sigma_t, v, T_chip, dt=1.0):
        """
        Eq. 36: Desgaste de flanco (Usui)
        
        dW/dt = C1 * σ_t * v * exp(-C2/T_chip)
        """
        if T_chip <= 0:
            return 0
        
        return (self.C1_flank * sigma_t * v * dt * 
                exp(-self.C2_flank / T_chip))
    
    def normal_stress(self, F_s, beta_n, phi_sn, gamma_n, b, l_ct, xi_d=2):
        """
        Eq. 38: Tensão normal na aresta de corte
        
        σ_t0 = F_s * cos(β_n) / cos(φ_sn + β_n - γ_n) * (ξ_d + 1) / (b * l_ct)
        
        Args:
            F_s: Força de cisalhamento (N)
            beta_n: Ângulo de atrito (rad)
            phi_sn: Ângulo de cisalhamento (rad)
            gamma_n: Ângulo de saída (rad)
            b: Largura do cavaco (mm)
            l_ct: Comprimento de contato ferramenta-cavaco (mm)
            xi_d: Parâmetro de perfil (2 para aço)
        """
        if b * l_ct < 1e-10:
            return 0
        
        cos_beta = cos(beta_n)
        cos_phi_beta_gamma = cos(phi_sn + beta_n - gamma_n)
        
        if abs(cos_phi_beta_gamma) < 1e-10:
            return 0
        
        return (F_s * cos_beta / cos_phi_beta_gamma) * (xi_d + 1) / (b * l_ct)
    
    def chip_tool_contact_length(self, h, phi_sn, beta_n, gamma_n, xi_d=2):
        """
        Eq. 39: Comprimento de contato ferramenta-cavaco
        
        l_ct = h * (ξ_d + 2)/2 * sin(φ_sn + β_n - γ_n) / (sin(φ_sn) * cos(β_n))
        """
        sin_phi = sin(phi_sn)
        cos_beta = cos(beta_n)
        
        if abs(sin_phi * cos_beta) < 1e-10:
            return h  # Valor aproximado
        
        return (h * (xi_d + 2) / 2 * 
                sin(phi_sn + beta_n - gamma_n) / (sin_phi * cos_beta))
    
    def shear_strain(self, phi_sn, gamma_n):
        """
        Eq. 42: Deformação de cisalhamento
        
        γ_1 = tan(φ_sn - γ_n) + 1/tan(φ_sn)
        """
        tan_phi = tan(phi_sn)
        if abs(tan_phi) < 1e-10:
            return 1  # Valor aproximado
        
        return tan(phi_sn - gamma_n) + 1/tan_phi
    
    def chip_temperature(self, T_w, beta_TQ, rho, c, v, phi_sn, gamma_1, tau_0):
        """
        Eq. 41: Temperatura na saída da banda de cisalhamento
        
        T_chip1 = T_w + β_TQ/(ρ*c) * [ρ*(v*sin(φ_sn))^2 * γ_1^2/2 + τ_0*γ_1]
        """
        v_sin_phi = v * sin(phi_sn)
        
        term1 = beta_TQ / (rho * c)
        term2 = (rho * v_sin_phi**2 * gamma_1**2 / 2) + (tau_0 * gamma_1)
        
        return T_w + term1 * term2
    
    def friction_coefficient(self, T_chip):
        """
        Eq. 45: Coeficiente de atrito em função da temperatura
        
        μ(T) = {
            1 - 3.44e-4*T,        25°C ≤ T ≤ 955°C
            0.68*(1 - (T-T*)/(Tm-T*))^q,  955°C < T ≤ 1500°C
        }
        """
        T = T_chip  # °C
        
        if T < 25:
            return 0.99
        elif T <= self.T_star:
            return 1 - 3.44e-4 * T
        elif T <= self.T_m:
            return 0.68 * (1 - (T - self.T_star) / (self.T_m - self.T_star))**self.q
        else:
            return 0.1  # Valor mínimo
    
    def mean_friction_coefficient(self, sigma_t0, v_c, l_ct, T_chip1, 
                                   k, rho, c, xi_d=2):
        """
        Eq. 46: Coeficiente de atrito médio
        
        μ̄ = (σ_t0 * sqrt(v_c * l_ct) / sqrt(π * k * ρ * c)) * 
             Σ [2/(2i+1) * C * ...] + T_chip1
        """
        # Simplificação - resolve iterativamente
        mu = 0.5  # Valor inicial
        
        for i in range(10):
            T_mean = self._mean_temperature(mu, sigma_t0, v_c, l_ct, 
                                           T_chip1, k, rho, c, xi_d)
            mu_new = self.friction_coefficient(T_mean)
            
            if abs(mu_new - mu) < 1e-4:
                break
            mu = 0.9 * mu + 0.1 * mu_new
        
        return mu
    
    def _mean_temperature(self, mu, sigma_t0, v_c, l_ct, T_chip1, 
                          k, rho, c, xi_d=2):
        """
        Calcula a temperatura média simplificada
        """
        term = mu * sigma_t0 * sqrt(v_c * l_ct) / sqrt(pi * k * rho * c)
        return T_chip1 + term * 0.6  # Fator de correção
    
    def normal_stress_distribution(self, l, sigma_t0, l_ct, xi_d=2):
        """
        Eq. 37: Distribuição de tensão normal ao longo da face de saída
        
        σ_t(l) = σ_t0 * (1 - l/l_ct)^ξ_d
        """
        if l > l_ct:
            return 0
        return sigma_t0 * (1 - l / l_ct)**xi_d
    
    def estimar_desgaste_total(self, forcas, cinematica, material_params, 
                                dt_total, n_pontos=100):
        """
        Estima o desgaste total ao longo do processo
        
        Args:
            forcas: Forças de corte (N)
            cinematica: Parâmetros cinemáticos
            material_params: Parâmetros do material
            dt_total: Tempo total de corte (s)
            n_pontos: Número de pontos na discretização
        """
        # Parâmetros
        F_c = forcas.get('Fc', 1000)
        h = material_params.get('h', 0.1)  # mm
        b = material_params.get('b', 1)  # mm
        v = cinematica.get('v_c', 100)  # m/min
        
        # Ângulos típicos para shaping
        gamma_n = radians(material_params.get('rake_angle', 5))
        beta_n = radians(material_params.get('friction_angle', 25))
        phi_sn = radians(material_params.get('shear_angle', 30))
        
        # Desgaste acumulado
        wear_crater_total = 0
        wear_flank_total = 0
        
        # Discretização do tempo
        dt = dt_total / n_pontos
        
        for i in range(n_pontos):
            # Estimativa da espessura do cavaco variável
            h_t = h * (1 + 0.5 * np.sin(2 * pi * i / n_pontos))
            
            # Força de cisalhamento
            F_s = F_c * cos(phi_sn) - 0.3 * F_c * sin(phi_sn)
            
            # Comprimento de contato
            l_ct = self.chip_tool_contact_length(h_t, phi_sn, beta_n, gamma_n)
            
            # Tensão normal
            sigma_t0 = self.normal_stress(F_s, beta_n, phi_sn, gamma_n, b, l_ct)
            
            # Temperatura
            T_w = 25 + 273  # K
            T_chip = self.chip_temperature(
                T_w, 0.9, 7800, 460, 
                v / 60, phi_sn, 
                self.shear_strain(phi_sn, gamma_n),
                F_s / (b * h_t) * sin(phi_sn)
            )
            
            # Desgaste
            wear_crater_total += self.crater_wear(sigma_t0, v/60, T_chip, dt)
            wear_flank_total += self.flank_wear(sigma_t0, v/60, T_chip, dt)
        
        return {
            'crater_wear': wear_crater_total,
            'flank_wear': wear_flank_total,
            'total_wear': wear_crater_total + wear_flank_total
        }