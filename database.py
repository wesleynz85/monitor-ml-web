import json
import os
from datetime import datetime

DB_FILE = "produtos.json"

def carregar_dados():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def salvar_dados(dados):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def adicionar_produto(url, nome, preco):
    dados = carregar_dados()
    # Verifica duplicidade por URL limpa
    url_limpa = url.split('?')[0]
    for p in dados:
        if p['url'] == url_limpa:
            return False, "Produto já existe!"
    
    agora = datetime.now().isoformat()
    novo = {
        "id": int(datetime.now().timestamp()), # ID simples
        "nome": nome,
        "url": url_limpa,
        "preco_atual": preco,
        "ativo": True,
        "ultimo_check": agora,
        "historico": [{"data": agora, "preco": preco}]
    }
    dados.append(novo)
    salvar_dados(dados)
    return True, "Produto adicionado!"

def atualizar_preco_produto(id_prod, novo_preco):
    dados = carregar_dados()
    for p in dados:
        if p['id'] == id_prod:
            agora = datetime.now().isoformat()
            p['ultimo_check'] = agora
            
            # Só adiciona ao histórico se o preço mudou ou se o histórico está vazio
            if not p['historico'] or p['historico'][-1]['preco'] != novo_preco:
                p['historico'].append({"data": agora, "preco": novo_preco})
                # Limita histórico a 100 itens para não pesar
                if len(p['historico']) > 100:
                    p['historico'].pop(0)
            
            p['preco_atual'] = novo_preco
            break
    salvar_dados(dados)

def toggle_ativo(id_prod, status):
    dados = carregar_dados()
    for p in dados:
        if p['id'] == id_prod:
            p['ativo'] = status
            break
    salvar_dados(dados)

def remover_produto(id_prod):
    dados = carregar_dados()
    novos_dados = [p for p in dados if p['id'] != id_prod]
    salvar_dados(novos_dados)