"""
Geometria de Engrenagens - Baseado nos artigos NASA e ETH
Suporte a engrenagens externas e internas
"""

import numpy as np
from math import cos, sin, tan, radians, pi, sqrt

class GearGeometry:
    """
    Geometria de engrenagens para shaping
    Suporte a engrenagens externas e internas (ring gears)
    """
    
    def __init__(self, modulo, z_peca, z_ferramenta, angulo_pressao=30, tipo='Interna'):
        """
        Inicializa a geometria da engrenagem
        
        Args:
            modulo: Módulo (mm) - valor real: 3.5
            z_peca: Número de dentes da peça - valor real: 12
            z_ferramenta: Número de dentes da ferramenta - valor real: 8
            angulo_pressao: Ângulo de pressão (graus) - valor real: 30°
            tipo: 'Externa' ou 'Interna'
        """
        self.m = modulo
        self.z1 = z_peca
        self.z2 = z_ferramenta
        self.alpha = radians(angulo_pressao)
        self.tipo = tipo
        
        # Verificação de consistência
        if self.tipo == 'Interna' and self.z1 <= self.z2:
            print(f"⚠️ Atenção: Para engrenagem interna, Z_peca ({self.z1}) deve ser > Z_ferramenta ({self.z2})")
    
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
        """
        Diâmetro externo da peça (mm)
        
        Para engrenagem EXTERNA: dentes estão na superfície externa
        Para engrenagem INTERNA: dentes estão na superfície interna
        """
        if self.tipo == 'Interna':
            # Para interna, o diâmetro externo é o raio do anel (sem dentes)
            # Valor real: 59.5 mm (da foto do desenho)
            return self.m * (self.z1 + 2) * 1.1  # Aproximação
        else:
            # Externa: fórmula padrão
            return self.m * (self.z1 + 2)
    
    @property
    def d_interno_peca(self):
        """
        Diâmetro interno da peça (mm)
        
        Para engrenagem INTERNA: onde estão os dentes (valor real: 39.6 mm)
        Para engrenagem EXTERNA: furo central
        """
        if self.tipo == 'Interna':
            # Para interna, o diâmetro interno é onde estão os dentes
            # Valor real: 39.6 mm (da foto do desenho)
            return self.m * (self.z1 - 2.5) * 0.95  # Aproximação
        else:
            # Externa: fórmula padrão
            return self.m * (self.z1 - 2.5)
    
    @property
    def d_externo_ferramenta(self):
        """Diâmetro externo da ferramenta (mm)"""
        return self.m * (self.z2 + 2)
    
    @property
    def d_interno_ferramenta(self):
        """Diâmetro interno da ferramenta (mm)"""
        return self.m * (self.z2 - 2.5)
    
    def altura_dente(self):
        """
        Altura total do dente (mm)
        
        Para engrenagem interna, a altura do dente é medida do fundo ao topo
        """
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
    
    def folga_entre_dentes(self):
        """Folga entre dentes (mm)"""
        return self.dedendum() - self.addendum()
    
    def profundidade_corte(self):
        """
        Profundidade de corte efetiva (mm)
        
        Para engrenagem interna, a profundidade é a altura do dente
        Valor real: 3.318 mm (da foto da máquina)
        """
        return self.altura_dente() * 0.95  # Aproximação realista
    
    def raio_curvatura_flanco(self, rho):
        """
        Raio de curvatura do flanco do dente
        """
        r_b = self.d_base_peca / 2
        return r_b * tan(rho)
    
    def matriz_transformacao(self, phi_c, phi_2, gamma, E, H_2, d_r, dx=0, dy=0, tipo='Externa'):
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
            tipo: 'Externa' ou 'Interna'
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
    
    def condicao_interseccao(self, x, y, z, gamma, l_2_ref, tipo='Externa'):
        """
        Eq. 19: Verifica se o ponto está na seção correta
        
        Para engrenagem interna, a condição é invertida
        """
        r_xy = sqrt(x**2 + y**2)
        
        if abs(gamma - pi/2) < 1e-6:
            if tipo == 'Interna':
                # Para interna, o ponto deve estar dentro do anel
                return r_xy - l_2_ref
            else:
                return r_xy - l_2_ref
        else:
            valor = cos(gamma) * (x + tan(gamma) * r_xy) - l_2_ref
            if tipo == 'Interna':
                return -valor  # Inverte para interna
            return valor
    
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
    
    def perfil_dente(self, z, r_base, phi_max, n_points=50, tipo='Externa'):
        """
        Gera o perfil completo de um dente
        
        Args:
            z: Número de dentes
            r_base: Raio da base
            phi_max: Ângulo máximo do involuto
            n_points: Número de pontos
            tipo: 'Externa' ou 'Interna'
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
        
        if tipo == 'Interna':
            # Para interna, o perfil é invertido (dentes para dentro)
            x_r = -x_r
            x_l_rot = -x_l_rot
        
        return np.column_stack([x_r, y_r]), np.column_stack([x_l_rot, y_l_rot])
    
    def gerar_perfil_completo(self, n_points=50, raio_ajuste=0):
        """
        Gera o perfil completo da engrenagem (todos os dentes)
        
        Args:
            n_points: Número de pontos por dente
            raio_ajuste: Ajuste de raio para engrenagens internas (mm)
        """
        z = self.z1
        r_base = self.d_base_peca / 2
        phi_max = self.altura_dente() / r_base if r_base > 0 else 0.5
        
        # Gera um dente
        dente_dir, dente_esq = self.perfil_dente(
            z, r_base, phi_max, n_points, self.tipo
        )
        
        # Combina os lados do dente
        dente = np.vstack([dente_dir[::-1], dente_esq])
        
        # Repete para todos os dentes
        perfis = []
        for i in range(z):
            theta = 2 * pi * i / z
            rotacao = np.array([
                [cos(theta), -sin(theta)],
                [sin(theta), cos(theta)]
            ])
            
            dente_rot = dente @ rotacao.T
            
            if self.tipo == 'Interna':
                # Para interna, os dentes estão no raio interno
                r_inner = self.d_interno_peca / 2 + raio_ajuste
                dente_rot[:, 0] += r_inner * cos(theta)
                dente_rot[:, 1] += r_inner * sin(theta)
            else:
                # Externa: dentes no raio externo
                r_outer = self.d_externo_peca / 2
                dente_rot[:, 0] += r_outer * cos(theta)
                dente_rot[:, 1] += r_outer * sin(theta)
            
            perfis.append(dente_rot)
        
        return np.vstack(perfis)
    
    def get_dados_reais(self):
        """
        Retorna os dados reais da peça (baseado nas fotos da máquina)
        """
        return {
            'tipo': self.tipo,
            'modulo': self.m,
            'z_peca': self.z1,
            'z_ferramenta': self.z2,
            'angulo_pressao': np.degrees(self.alpha),
            'diametro_externo': self.d_externo_peca,
            'diametro_interno': self.d_interno_peca,
            'profundidade_corte': self.profundidade_corte(),
            'altura_dente': self.altura_dente(),
            'relacao_transmissao': self.relacao_transmissao()
        }
    
    def relacao_transmissao(self):
        """Relação de transmissão (ferramenta/peça)"""
        return self.z2 / self.z1
    
    def print_resumo(self):
        """Imprime um resumo da geometria"""
        print("=" * 50)
        print(f"📐 GEOMETRIA DA ENGRENAGEM - {self.tipo}")
        print("=" * 50)
        print(f"  Módulo: {self.m:.3f} mm")
        print(f"  Nº dentes (peça): {self.z1}")
        print(f"  Nº dentes (ferramenta): {self.z2}")
        print(f"  Ângulo de pressão: {np.degrees(self.alpha):.1f}°")
        print(f"  Diâmetro externo: {self.d_externo_peca:.2f} mm")
        print(f"  Diâmetro interno: {self.d_interno_peca:.2f} mm")
        print(f"  Altura do dente: {self.altura_dente():.3f} mm")
        print(f"  Relação transmissão: {self.relacao_transmissao():.3f}")
        print("=" * 50)