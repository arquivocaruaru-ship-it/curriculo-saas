import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def processar_curriculo(texto):

    prompt = f"""
Extraia os dados do currículo abaixo e retorne em JSON.

REGRAS IMPORTANTES:

- Sempre incluir o campo "cidade"
- Se não encontrar cidade, retornar como ""
- O currículo deve caber em 1 página A4
- Seja direto, objetivo e profissional
- NÃO escrever textos longos
- NÃO inventar informações
- NÃO repetir informações

RESUMO PROFISSIONAL:
- Deve conter exatamente 4 linhas
- Linguagem forte, objetiva e profissional
- NÃO mencionar tempo de experiência
- Substituir tempo por termos como: "ampla experiencia", "solida experiencia", "vivencia"

EXPERIENCIAS:
- Gerar no maximo 6 experiencias
- Ordenar da mais recente para a mais antiga

ATIVIDADES:
- Padrao: 3 atividades por experiencia
- Nunca menos que 2

FORMACAO:
- Listar TODAS as formacoes academicas
- Campos OBRIGATORIOS: nivel, instituicao, curso, ano_conclusao
- nivel DEVE conter o nome COMPLETO do curso
- Exemplo correto:
  "nivel": "Pos-graduacao em Enfermagem do Trabalho"
  "instituicao": "Faculdade IDE"
  "curso": "Enfermagem do Trabalho"
  "ano_conclusao": "2023"

- Exemplo incorreto (NAO FAZER):
  "nivel": "Pos-graduacao"  (sem o nome do curso)

- Se a formacao for Graduacao, colocar o nome do curso no campo nivel
- Exemplo: "nivel": "Bacharelado em Enfermagem"

CURSOS:
- Listar TODOS os cursos e capacitacoes (sem limite)
- Incluir nome do curso

HABILIDADES:
- Até 4 habilidades

Formato JSON esperado:

{{
  "nome": "",
  "data_nascimento": "",
  "estado_civil": "",
  "cidade": "",
  "cnh": "",
  "telefone": "",
  "email": "",
  "resumo": "",
  "experiencias": [
    {{
      "cargo": "",
      "empresa": "",
      "periodo": "",
      "atividades": []
    }}
  ],
  "formacao": [
    {{
      "nivel": "",
      "instituicao": "",
      "curso": "",
      "ano_conclusao": ""
    }}
  ],
  "cursos": [],
  "habilidades": []
}}

Texto do candidato:
{texto}
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    content = response.choices[0].message.content.strip()

    print("RESPOSTA IA BRUTA:", content)

    if content.startswith("```"):
        content = content.replace("```json", "").replace("```", "").strip()

    try:
        dados = json.loads(content)

        if "cidade" not in dados:
            dados["cidade"] = ""

        return dados

    except Exception as e:
        print("ERRO JSON:", e)
        return None