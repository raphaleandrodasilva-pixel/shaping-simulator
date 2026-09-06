"""
Teoria do Envelope - Baseado no artigo NASA (1990)
Seções 3 e 4
"""

import numpy as np
from scipy.optimize import fsolve
from scipy.interpolate import interp1d

class EnvelopeTheory:
    """
    Implementa a teoria do envelope do artigo NASA
    
    Referência: Mavriplis & Huston (1990)
    Computer Simulation of Gear Tooth Manufacturing Processes
    """
    
    @staticmethod
    def familia_curvas(x, y, t, params):
        """
        Define a família de curvas f(x,y,t) = 0
        t é o parâmetro (posição da ferramenta)
        """
        r_base = params.get('r_base', 10)
        phi_0 = params.get('phi_0', 0)
        phi = phi_0 + t
        
        # Equação paramétrica do involuto (Eq. 4.2.6-7)
        x_tool = r_base * (np.sin(phi) - phi * np.cos(phi))
        y_tool = r_base * (np.cos(phi) + phi * np.sin(phi))
        
        return x - x_tool, y - y_tool
    
    @staticmethod
    def condicao_envelope(x, y, t, params):
        """
        Condição de envelope: ∂f/∂t = 0
        """
        r_base = params.get('r_base', 10)
        phi_0 = params.get('phi_0', 0)
        phi = phi_0 + t
        
        dx_dt = r_base * phi * np.sin(phi)
        dy_dt = -r_base * phi * np.cos(phi)
        
        return dx_dt, dy_dt
    
    @staticmethod
    def encontrar_envelope(params, t_range, n_points=100):
        """
        Encontra o envelope da família de curvas
        
        Resolve o sistema:
            f(x,y,t) = 0
            ∂f/∂t = 0
        """
        envelope_points = []
        
        for t in t_range:
            def equations(vars):
                x, y = vars
                f1, f2 = EnvelopeTheory.familia_curvas(x, y, t, params)
                df1, df2 = EnvelopeTheory.condicao_envelope(x, y, t, params)
                return [f1, f2, df1, df2]
            
            try:
                sol = fsolve(equations, [0, 0], maxfev=1000)
                if abs(sol[0]) < 100 and abs(sol[1]) < 100:
                    envelope_points.append(sol[:2])
            except:
                continue
        
        return np.array(envelope_points)
    
    @staticmethod
    def envelope_curva(ferramenta, movimento, params):
        """
        Calcula o envelope para uma ferramenta genérica
        
        Args:
            ferramenta: Função que retorna a posição da ferramenta
            movimento: Função que retorna o movimento da ferramenta
            params: Parâmetros adicionais
        """
        t_range = np.linspace(0, 2*np.pi, 100)
        envelope = []
        
        for t in t_range:
            # Posição da ferramenta
            tool_pos = ferramenta(t, params)
            
            # Transformação devido ao movimento
            pos = movimento(tool_pos, t, params)
            envelope.append(pos)
        
        return np.array(envelope)


class InvoluteEnvelope:
    """
    Implementa a derivação do envelope do involuto
    NASA Seção 4.5 - Equações 4.5.13 a 4.5.16
    
    O footprint de um cutter involuto em uma engrenagem em branco
    também é um involuto!
    """
    
    @staticmethod
    def perfil_cutter(r1, r2, phi, alpha):
        """
        Eq. 4.5.13: Perfil do cutter no sistema da peça
        
        Args:
            r1: Raio do cutter
            r2: Raio da peça
            phi: Ângulo do involuto
            alpha: Ângulo de rolamento
        """
        # Posição do ponto no cutter (Eq. 4.5.13.a-b)
        phi_alpha = phi - alpha
        
        x_cutter = r2 * (np.sin(phi_alpha) - phi * np.cos(phi_alpha))
        y_cutter = r2 * (np.cos(phi_alpha) + phi * np.sin(phi_alpha))
        
        # Translação devido ao rolamento
        r_sum = r1 + r2
        theta = (r1 / r_sum) * alpha
        
        x = x_cutter + r_sum * np.sin(theta)
        y = y_cutter - r_sum * np.cos(theta)
        
        return x, y
    
    @staticmethod
    def envelope_involuto(r1, r2, phi_range, alpha):
        """
        Eq. 4.5.16: O envelope também é um involuto!
        
        β = (r2/r1) * φ
        
        x = r1 * (sin(β) - β * cos(β))
        y = -r1 * (cos(β) + β * sin(β))
        """
        beta = (r2 / r1) * phi_range
        
        x = r1 * (np.sin(beta) - beta * np.cos(beta))
        y = -r1 * (np.cos(beta) + beta * np.sin(beta))
        
        return x, y
    
    @staticmethod
    def gerar_perfil_gear(r1, r2, n_points=50, phi_max=2*np.pi):
        """
        Gera o perfil completo de uma engrenagem gerada por shaping
        
        Args:
            r1: Raio do cutter
            r2: Raio da peça
            n_points: Número de pontos
            phi_max: Ângulo máximo do involuto
        """
        phi_range = np.linspace(0, phi_max, n_points)
        alpha = np.linspace(0, 2*np.pi, n_points)
        
        # Calcula o envelope para cada posição de rolamento
        perfis = []
        for a in alpha:
            x, y = InvoluteEnvelope.envelope_involuto(r1, r2, phi_range, a)
            perfis.append(np.column_stack([x, y]))
        
        return perfis
    
    @staticmethod
    def ponto_contato(r1, r2, phi, alpha):
        """
        Calcula o ponto de contato entre cutter e peça
        """
        # Posição do ponto no cutter
        phi_alpha = phi - alpha
        
        x_contato = r2 * (np.sin(phi_alpha) - phi * np.cos(phi_alpha))
        y_contato = r2 * (np.cos(phi_alpha) + phi * np.sin(phi_alpha))
        
        return x_contato, y_contato