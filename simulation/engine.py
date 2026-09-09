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
        
        # Parâmetros reais (extraídos das fotos da máquina)
        self.tipo_engrenagem = params.get('tipo_engrenagem', 'Interna')
        self.cortes = params.get('cortes', [])
        
        # Inicializa módulos
        self.kinematics = ShapingKinematics(
            spm=params.get('spm', 450),  # Atualizado para valor real
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
            stiffness_x=params.get('stiffness_x', 1e6),  # Atualizado
            stiffness_y=params.get('stiffness_y', 1e6)   # Atualizado
        )
        
        # Estado da simulação
        self.stroke_count = 0
        self.total_time = 0
        self.history = defaultdict(list)
        
        # Inicializa a geometria (com valores reais)
        self.geometry = GearGeometry(
            modulo=params.get('modulo', 3.5),  # Atualizado
            z_peca=params.get('z_peca', 12),   # Atualizado
            z_ferramenta=params.get('z_ferramenta', 8)  # Atualizado
        )
        
        # Blank inicial
        self.blank = self._inicializar_blank()
        self.material_removido_total = 0
        
        # Controle de cortes
        self.corte_atual_idx = 0
        self.profundidade_por_corte = self._calcular_profundidade_por_corte()
    
    def _calcular_profundidade_por_corte(self):
        """Calcula a profundidade de cada corte baseado na porcentagem"""
        profundidade_total = self.params.get('depth', 3.318)
        cortes = self.params.get('cortes', [])
        
        if not cortes:
            # Se não houver cortes definidos, usa um único corte
            return [{'tipo': 'Único', 'profundidade': profundidade_total, 'avanco': self.params.get('radial_feed', 0.05)}]
        
        resultado = []
        for corte in cortes:
            prof = profundidade_total * (corte.get('profundidade', 50) / 100.0)
            resultado.append({
                'tipo': corte.get('tipo', 'Corte'),
                'profundidade': prof,
                'avanco': corte.get('avanco', 0.005)
            })
        return resultado
    
    def _inicializar_blank(self):
        """Inicializa o blank da engrenagem como uma malha de pontos"""
        # Para engrenagem interna, o material está entre o raio interno e externo
        r_inner = self.params.get('inner_radius', 39.6)   # Atualizado
        r_outer = self.params.get('outer_radius', 59.5)   # Atualizado
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
        """
        Simula um único golpe de corte
        
        Agora com suporte a:
        - Múltiplos cortes (desbaste + acabamento)
        - Engrenagens internas e externas
        """
        if t is None:
            t = self.total_time
        
        # Verifica se já terminou todos os cortes
        if self.corte_atual_idx >= len(self.profundidade_por_corte):
            # Fim da simulação
            return None
        
        corte_atual = self.profundidade_por_corte[self.corte_atual_idx]
        
        # 1. Cinemática - posição do curso
        l_c = self.kinematics.posicao_curso(t)
        v_c = self.kinematics.velocidade_curso(t)
        
        # 2. Posição angular da peça
        phi_2 = self.kinematics.velocidade_rotacao_peca(
            self.params.get('circular_feed', 0.730),  # Atualizado
            self.params.get('z_ferramenta', 8),
            self.params.get('z_peca', 12),
            self.geometry.r_primitivo_ferramenta
        ) * t
        
        # 3. Posição radial (avanço ao longo do tempo)
        profundidade_total = self.params.get('depth', 3.318)
        avanco_radial = corte_atual['avanco']
        
        # Calcula a posição radial atual (com base no corte atual)
        profundidade_restante = corte_atual['profundidade']
        d_r = min(profundidade_restante, self.stroke_count * avanco_radial)
        
        # Ajuste para engrenagem interna (corte de dentro para fora)
        if self.tipo_engrenagem == 'Interna':
            # Na interna, a ferramenta corta do centro para fora
            # A posição radial é medida a partir do raio interno
            r_inner = self.params.get('inner_radius', 39.6)
            d_r_interna = r_inner + d_r
            # O envelope precisa ser calculado com este ajuste
        else:
            # Externa: corte de fora para dentro
            r_outer = self.params.get('outer_radius', 59.5)
            d_r_externa = r_outer - d_r
        
        # 4. Envelope da ferramenta (com ajuste para interna/externa)
        envelope = self._calcular_envelope(t, phi_2, l_c, d_r)
        
        # 5. Material removido
        removed = self._remover_material(envelope)
        self.material_removido_total += removed['points_removed']
        
        # 6. Forças de corte (com base no material removido)
        forcas = self._calcular_forcas(removed, v_c, d_r, corte_atual)
        
        # 7. Desgaste
        desgaste = self._calcular_desgaste(forcas, v_c, removed)
        
        # 8. Deflexão
        deflexao = self.deflection.calcular_deflexao(forcas)
        
        # Atualiza contadores
        self.stroke_count += 1
        self.total_time = t + 1/self.kinematics.f_st
        
        # Verifica se terminou este corte
        if d_r >= profundidade_restante:
            self.corte_atual_idx += 1
            print(f"✅ Corte '{corte_atual['tipo']}' concluído! ({self.stroke_count} golpes)")
        
        resultado = {
            'stroke': self.stroke_count,
            'time': t,
            'tool_position': l_c,
            'velocity': v_c,
            'rotary_angle': phi_2,
            'radial_position': d_r,
            'corte_atual': corte_atual['tipo'],
            'corte_idx': self.corte_atual_idx,
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
        # Ajuste para engrenagem interna
        if self.tipo_engrenagem == 'Interna':
            raio_efetivo = r1 * 0.15 + (r2 - r1) * 0.05
            # Para interna, o raio efetivo é menor
            raio_efetivo = max(raio_efetivo, 1.5)
        else:
            raio_efetivo = r1 * 0.15 + (r2 - r1) * 0.05
            raio_efetivo = max(raio_efetivo, 2.0)
        
        # Cria um perfil que simula um dente
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
        
        # Posiciona na engrenagem (com ajuste para interna)
        if self.tipo_engrenagem == 'Interna':
            # Para interna, a ferramenta está dentro do anel
            x_final = x_rot + r2 * np.cos(alpha * 0.5) * 0.8
            y_final = y_rot + r2 * np.sin(alpha * 0.5) * 0.8
        else:
            # Externa: posicionamento normal
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
    
    def _calcular_forcas(self, removed, v_c, d_r, corte_atual):
        """
        Calcula as forças de corte
        
        Agora considera:
        - O tipo de corte (desbaste vs acabamento)
        - O avanço radial específico do corte
        """
        # Parâmetros do corte atual
        avanco = corte_atual.get('avanco', 0.005)
        tipo = corte_atual.get('tipo', 'Corte')
        
        # Profundidade total
        profundidade = self.params.get('depth', 3.318)
        
        # Fator de profundidade (progressão durante o corte)
        fator_profundidade = min(1.0, d_r / profundidade) if profundidade > 0 else 1.0
        
        # Força base (N) - ajustada para valores reais
        if tipo.lower() in ['desbaste', 'roughing']:
            # Desbaste: forças mais altas
            fc_base = 150 + fator_profundidade * 600
            ff_base = 30 + fator_profundidade * 120
            fp_base = 15 + fator_profundidade * 60
        else:
            # Acabamento: forças mais baixas
            fc_base = 80 + fator_profundidade * 350
            ff_base = 15 + fator_profundidade * 70
            fp_base = 10 + fator_profundidade * 35
        
        # Ajuste pelo avanço radial (avanço menor = força menor)
        fator_avanco = avanco / 0.005  # Normaliza em relação a 0.005
        fc_base *= min(1.0, fator_avanco * 1.2)
        ff_base *= min(1.0, fator_avanco * 1.2)
        fp_base *= min(1.0, fator_avanco * 1.2)
        
        # Variação devido ao material removido
        if removed['points_removed'] > 0:
            fc_base += removed['points_removed'] * 0.3
            ff_base += removed['points_removed'] * 0.06
            fp_base += removed['points_removed'] * 0.03
        
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
        fator = self.stroke_count / 100.0
        fator_forca = forcas['Fc'] / 500.0
        
        # Desgaste de cratera (crescente com o tempo)
        wear_crater = 0.2 * fator + 0.08 * fator_forca + 0.03 * math.sin(fator * 2)
        
        # Desgaste de flanco
        wear_flank = 0.15 * fator + 0.04 * fator_forca + 0.02 * math.cos(fator * 1.5)
        
        # Garante que não fica negativo
        wear_crater = max(0, wear_crater)
        wear_flank = max(0, wear_flank)
        
        return {
            'crater': wear_crater,
            'flank': wear_flank,
            'total': wear_crater + wear_flank
        }
    
    def get_summary(self):
        """Retorna um resumo da simulação"""
        if not self.history['strokes']:
            return None
        
        # Forças
        forcas = [s['forces'] for s in self.history['strokes']]
        fc_max = max([f['Fc'] for f in forcas]) if forcas else 0
        fc_media = np.mean([f['Fc'] for f in forcas]) if forcas else 0
        
        # Desgaste
        desgastes = [s['wear'] for s in self.history['strokes']]
        wear_crater = desgastes[-1]['crater'] if desgastes else 0
        wear_flank = desgastes[-1]['flank'] if desgastes else 0
        
        # Tempo
        tempo_total = self.total_time
        
        # Golpes por corte
        cortes_info = []
        for i, corte in enumerate(self.profundidade_por_corte):
            cortes_info.append({
                'tipo': corte['tipo'],
                'golpes': self.stroke_count // len(self.profundidade_por_corte) if self.profundidade_por_corte else 0,
                'profundidade': corte['profundidade']
            })
        
        return {
            'strokes': self.stroke_count,
            'total_time': tempo_total,
            'fc_max': fc_max,
            'fc_media': fc_media,
            'wear_crater': wear_crater,
            'wear_flank': wear_flank,
            'wear_total': wear_crater + wear_flank,
            'material_removed': self.material_removido_total,
            'cortes': cortes_info,
            'tipo_engrenagem': self.tipo_engrenagem
        }
    
    def simular_completo(self):
        """Executa a simulação completa até o fim"""
        print(f"🔄 Iniciando simulação para engrenagem {self.tipo_engrenagem}...")
        print(f"📊 {len(self.profundidade_por_corte)} corte(s) definido(s):")
        for i, corte in enumerate(self.profundidade_por_corte):
            print(f"   {i+1}. {corte['tipo']}: {corte['profundidade']:.3f}mm @ {corte['avanco']:.4f}mm/Bat")
        
        resultado = None
        while True:
            resultado = self.simular_golpe()
            if resultado is None:
                break
        
        print(f"✅ Simulação concluída!")
        print(f"   Total de golpes: {self.stroke_count}")
        print(f"   Tempo total: {self.total_time:.2f}s")
        
        return self.get_summary()