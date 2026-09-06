"""
Gerenciador de dados de materiais e ferramentas.
Centraliza leitura/escrita dos arquivos data/materials.json e data/tools.json,
para que toda a aplicacao (combos, cadastro, simulacao) use a mesma fonte.
"""

import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATERIALS_PATH = os.path.join(BASE_DIR, "data", "materials.json")
TOOLS_PATH = os.path.join(BASE_DIR, "data", "tools.json")


# ---------------------------------------------------------------------
# Materiais
# ---------------------------------------------------------------------
def load_materials():
    """Retorna o dict {chave: {campos...}} de materiais."""
    with open(MATERIALS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("materials", {})


def save_materials(materials_dict):
    with open(MATERIALS_PATH, "w", encoding="utf-8") as f:
        json.dump({"materials": materials_dict}, f, indent=2, ensure_ascii=False)


def upsert_material(chave, dados):
    """Adiciona ou atualiza um material. 'chave' e o identificador interno (ex: SAE_1045)."""
    materials = load_materials()
    materials[chave] = dados
    save_materials(materials)


def delete_material(chave):
    materials = load_materials()
    if chave in materials:
        del materials[chave]
        save_materials(materials)


# ---------------------------------------------------------------------
# Ferramentas
# ---------------------------------------------------------------------
def load_tools():
    """Retorna o dict {chave: {campos...}} de ferramentas."""
    with open(TOOLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f).get("tools", {})


def save_tools(tools_dict):
    with open(TOOLS_PATH, "w", encoding="utf-8") as f:
        json.dump({"tools": tools_dict}, f, indent=2, ensure_ascii=False)


def upsert_tool(chave, dados):
    tools = load_tools()
    tools[chave] = dados
    save_tools(tools)


def delete_tool(chave):
    tools = load_tools()
    if chave in tools:
        del tools[chave]
        save_tools(tools)


# ---------------------------------------------------------------------
# Campos esperados por tipo (usado para montar o formulario de cadastro)
# ---------------------------------------------------------------------
CAMPOS_MATERIAL = [
    ("nome", "Nome de exibicao", str, ""),
    ("dureza_brinell", "Dureza Brinell (HB)", float, 0),
    ("k_c", "k_c1.1 - forca especifica de corte (N/mm2)", float, 0),
    ("m_c", "m_c - expoente de Kienzle (corte)", float, 0),
    ("k_f", "k_f1.1 - forca especifica de avanco (N/mm2)", float, 0),
    ("m_f", "m_f - expoente de Kienzle (avanco)", float, 0),
    ("densidade", "Densidade (kg/m3)", float, 7850),
    ("condutividade_termica", "Condutividade termica (W/m.K)", float, 45),
    ("calor_especifico", "Calor especifico (J/kg.K)", float, 460),
]

CAMPOS_FERRAMENTA = [
    ("nome", "Nome de exibicao", str, ""),
    ("fator_vc", "Fator de velocidade de corte (relativo a HSS=1.0)", float, 1.0),
    ("fator_desgaste", "Fator de desgaste (relativo, menor = mais resistente)", float, 1.0),
    ("temperatura_maxima", "Temperatura maxima antes de queima (graus C)", float, 600),
    ("durabilidade_base", "Durabilidade base (minutos)", float, 60),
    ("aplicacao", "Aplicacao recomendada", str, ""),
]
