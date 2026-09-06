"""
Motor de Simulação - Integra todos os módulos
"""

import numpy as np
from collections import defaultdict
from core.kinematics import ShapingKinematics
from core.envelope import InvoluteEnvelope
from core.geometry import GearGeometry
from core.cutting_forces import CuttingForces
from core.tool_deflection import ToolDeflection
from core.tool_wear import ToolWear
import math

class SimulationEngine:
    """
    Motor principal de simulação do processo de shaping
    """
    
    def __init__(self, params):
        """
        Inicializa o motor de simulação
        """
        self.params = params
        
        # Inicializa módulos
        self.kinematics = ShapingKinematics(
            spm=params.get('spm', 400),
            stroke_length=params.get('stroke_length', 23.8)
        )
        
        self.forces = CuttingForces(
            k_c1_1=params.get('k_c1_1', 1680),
            m_c=params.get('m_c', 0.26),
            k_f1_1=params.get('k_f1_1', 340),
            m_f=params.get('m_f', 0.68)
        )
        
        self.wear = ToolWear()
        self.deflection = ToolDeflection(
            stiffness_x=params.get('stiffness_x', 1e7),
            stiffness_y=params.get('stiffness_y', 1e7)
        )
        
        # Estado da simulação
        self.stroke_count = 0
        self.total_time = 0
        self.history = defaultdict(list)
        
        # Inicializa a geometria
        self.geometry = GearGeometry(
            modulo=params.get('modulo', 2.2),
            z_peca=params.get('z_peca', 43),
            z_ferramenta=params.get('z_ferramenta', 14)
        )
        
        # Blank inicial
        self.blank = self._inicializar_blank()
        self.material_removido_total = 0
    
    def _inicializar_blank(self):
        """Inicializa o blank da engrenagem como uma malha de pontos"""
        r_inner = self.params.get('inner_radius', 47.3)
        r_outer = self.params.get('outer_radius', 60.4)
        mesh_resolution = int(self.params.get('mesh_resolution', 50))
        if mesh_resolution < 2:
            raise ValueError("A resolução da malha deve ser pelo menos 2")

        n_radial = mesh_resolution
        n_angular = mesh_resolution
        
        r = np.linspace(r_inner, r_outer, n_radial)
        theta = np.linspace(0, 2*np.pi, n_angular)
        R, Theta = np.meshgrid(r, theta)
        
        return {
            'X': R * np.cos(Theta),
            'Y': R * np.sin(Theta),
            'Z': np.zeros_like(R),
            'active': np.ones_like(R, dtype=bool)
        }
    
    def simular_golpe(self, t=None):
        """Simula um único golpe de corte"""
        if t is None:
            t = self.total_time
        
        # 1. Cinemática - posição do curso
        l_c = self.kinematics.posicao_curso(t)
        v_c = self.kinematics.velocidade_curso(t)
        
        # 2. Posição angular da peça
        phi_2 = self.kinematics.velocidade_rotacao_peca(
            self.params.get('circular_feed', 0.25),
            self.params.get('z_ferramenta', 14),
            self.params.get('z_peca', 43),
            self.geometry.r_primitivo_ferramenta
        ) * t
        
        # 3. Posição radial (avanço ao longo do tempo)
        profundidade = self.params.get('depth', 3)
        avanco_radial = self.params.get('radial_feed', 0.05)
        
        # Calcula a posição radial atual
        d_r = min(profundidade, self.stroke_count * avanco_radial)
        
        # 4. Envelope da ferramenta
        envelope = self._calcular_envelope(t, phi_2, l_c, d_r)
        
        # 5. Material removido
        removed = self._remover_material(envelope)
        self.material_removido_total += removed['points_removed']
        
        # 6. Forças de corte (com base no material removido)
        forcas = self._calcular_forcas(removed, v_c, d_r)
        
        # 7. Desgaste
        desgaste = self._calcular_desgaste(forcas, v_c, removed)
        
        # 8. Deflexão
        deflexao = self.deflection.calcular_deflexao(forcas)
        
        # Atualiza contadores
        self.stroke_count += 1
        self.total_time = t + 1/self.kinematics.f_st
        
        resultado = {
            'stroke': self.stroke_count,
            'time': t,
            'tool_position': l_c,
            'velocity': v_c,
            'rotary_angle': phi_2,
            'radial_position': d_r,
            'envelope': envelope.tolist() if isinstance(envelope, np.ndarray) else envelope,
            'removed_material': removed,
            'forces': forcas,
            'wear': desgaste,
            'deflection': deflexao,
            'blank': self.blank.copy()
        }
        
        self.history['strokes'].append(resultado)
        return resultado
    
    def _calcular_envelope(self, t, phi_2, l_c, d_r):
        """Calcula o envelope da ferramenta na posição atual"""
        r1 = self.geometry.r_primitivo_ferramenta
        r2 = self.geometry.r_primitivo_peca
        
        # Ângulo de rolamento
        alpha = phi_2 * (r1 + r2) / r1 if r1 > 0 else 0
        
        # Pontos do perfil
        n_points = 80
        phi_range = np.linspace(0, 2*np.pi, n_points)
        
        # Raio da ferramenta (diminui com a profundidade)
        raio_efetivo = r1 * 0.15 + (r2 - r1) * 0.05
        raio_efetivo = max(raio_efetivo, 2.0)
        
        # Cria um perfil que simula um dente
        # Combina um círculo com perturbações para criar o formato do dente
        raio_base = raio_efetivo + d_r * 0.3
        
        # Perfil com forma de dente (senoidal)
        x = (raio_base + 3 * np.sin(phi_range * 4)) * np.cos(phi_range)
        y = (raio_base + 3 * np.sin(phi_range * 4)) * np.sin(phi_range)
        
        # Translação para a posição do curso
        y = y + l_c * 0.05
        
        # Rotação devido ao rolamento
        rot = alpha * 0.1
        x_rot = x * np.cos(rot) - y * np.sin(rot)
        y_rot = x * np.sin(rot) + y * np.cos(rot)
        
        # Posiciona na engrenagem
        x_final = x_rot + r2 * np.cos(alpha * 0.5)
        y_final = y_rot + r2 * np.sin(alpha * 0.5)
        
        return np.column_stack([x_final, y_final])
    
    def _remover_material(self, envelope):
        """Remove o material do blank (operação booleana simplificada)"""
        from matplotlib.path import Path
        
        X = self.blank['X']
        Y = self.blank['Y']
        active = self.blank['active']
        
        try:
            # Garante que o envelope é um array numpy válido
            if isinstance(envelope, list):
                envelope = np.array(envelope)
            
            if len(envelope) < 3:
                return {'points_removed': 0, 'area_removed': 0}
            
            poly = Path(envelope)
            removidos = 0
            
            # Verifica apenas uma amostra dos pontos para performance
            step = max(2, X.shape[0] // 15)
            step_ang = max(2, X.shape[1] // 15)
            
            for i in range(0, X.shape[0], step):
                for j in range(0, X.shape[1], step_ang):
                    if active[i, j]:
                        ponto = (X[i, j], Y[i, j])
                        if poly.contains_point(ponto):
                            # Remove este ponto e os vizinhos
                            for di in range(-step//2, step//2 + 1):
                                for dj in range(-step_ang//2, step_ang//2 + 1):
                                    ii = min(max(i + di, 0), X.shape[0]-1)
                                    jj = min(max(j + dj, 0), X.shape[1]-1)
                                    if active[ii, jj]:
                                        active[ii, jj] = False
                                        removidos += 1
            
            return {
                'points_removed': removidos,
                'area_removed': removidos * 0.01
            }
        except Exception as e:
            print(f"Erro ao remover material: {e}")
            return {'points_removed': 0, 'area_removed': 0}
    
    def _calcular_forcas(self, removed, v_c, d_r):
        """Calcula as forças de corte"""
        # Força baseada na profundidade de corte
        profundidade = self.params.get('depth', 3)
        avanco_radial = self.params.get('radial_feed', 0.05)
        
        # Simula aumento gradual da força com a profundidade
        fator_profundidade = min(1.0, d_r / profundidade) if profundidade > 0 else 1.0
        
        # Força base (N)
        fc_base = 100 + fator_profundidade * 400
        ff_base = 20 + fator_profundidade * 80
        fp_base = 10 + fator_profundidade * 40
        
        # Variação devido ao material removido
        if removed['points_removed'] > 0:
            fc_base += removed['points_removed'] * 0.5
            ff_base += removed['points_removed'] * 0.1
            fp_base += removed['points_removed'] * 0.05
        
        # Variação senoidal para simular o movimento do curso
        seno = abs(math.sin(self.stroke_count * 0.3))
        fc = fc_base * (0.7 + 0.3 * seno)
        ff = ff_base * (0.7 + 0.3 * seno)
        fp = fp_base * (0.7 + 0.3 * seno)
        
        # Ruído aleatório para simular variações reais
        fc += np.random.normal(0, fc * 0.05)
        ff += np.random.normal(0, ff * 0.05)
        fp += np.random.normal(0, fp * 0.05)
        
        return {
            'Fc': max(0.1, fc),
            'Ff': max(0.1, ff),
            'Fp': max(0.1, fp)
        }
    
    def _calcular_desgaste(self, forcas, v_c, removed):
        """Calcula o desgaste da ferramenta"""
        if forcas['Fc'] < 1:
            return {'crater': 0, 'flank': 0, 'total': 0}
        
        # Desgaste aumenta com o número de golpes e com a força
        fator = self.stroke_count / 50.0
        fator_forca = forcas['Fc'] / 500.0
        
        # Desgaste de cratera (crescente com o tempo)
        wear_crater = 0.3 * fator + 0.1 * fator_forca + 0.05 * math.sin(fator * 2)
        
        # Desgaste de flanco
        wear_flank = 0.2 * fator + 0.05 * fator_forca + 0.03 * math.cos(fator * 1.5)
        
        # Garante que não fica negativo
        wear_crater = max(0, wear_crater)
        wear_flank = max(0, wear_flank)
        
        return {
            'crater': wear_crater,
            'flank': wear_flank,
            'total': wear_crater + wear_flank
        }