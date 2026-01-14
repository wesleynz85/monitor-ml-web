from db_conn import supabase
from datetime import datetime

# Não precisamos mais de ARQUIVO_JSON

def carregar_dados():
    """Busca todos os produtos do Supabase ordenados por ID"""
    try:
        response = supabase.table("produtos").select("*").order("id").execute()
        return response.data
    except Exception as e:
        print(f"Erro ao carregar dados: {e}")
        return []

def adicionar_produto(url, nome, preco):
    """Insere um novo produto na nuvem"""
    # Verifica duplicidade
    try:
        # Busca se já existe URL igual
        check = supabase.table("produtos").select("id").eq("url", url.split('?')[0]).execute()
        if check.data:
            return False, "Produto já existe no banco!"

        agora = datetime.now().isoformat()
        novo_produto = {
            "nome": nome,
            "url": url.split('?')[0],
            "preco_atual": preco,
            "ativo": True,
            "ultimo_check": agora,
            "historico": [{"data": agora, "preco": preco}] # Supabase aceita JSON direto
        }
        
        supabase.table("produtos").insert(novo_produto).execute()
        return True, "Produto adicionado na Nuvem!"
    except Exception as e:
        return False, str(e)

def atualizar_preco_produto(id_prod, novo_preco):
    """Atualiza preço e histórico no Supabase"""
    try:
        # 1. Busca o histórico atual
        res = supabase.table("produtos").select("historico, preco_atual").eq("id", id_prod).execute()
        if not res.data: return

        produto = res.data[0]
        historico = produto.get('historico', [])
        agora = datetime.now().isoformat()

        # Só atualiza histórico se mudou preço ou está vazio
        if not historico or historico[-1]['preco'] != novo_preco:
            historico.append({"data": agora, "preco": novo_preco})
            # Limita tamanho do histórico para não estourar o banco (opcional)
            if len(historico) > 100:
                historico.pop(0)

        # 2. Envia atualização
        dados_update = {
            "preco_atual": novo_preco,
            "ultimo_check": agora,
            "historico": historico
        }
        
        supabase.table("produtos").update(dados_update).eq("id", id_prod).execute()
        
    except Exception as e:
        print(f"Erro ao atualizar ID {id_prod}: {e}")

def toggle_ativo(id_prod, status):
    """Liga/Desliga monitoramento na nuvem"""
    try:
        supabase.table("produtos").update({"ativo": status}).eq("id", id_prod).execute()
    except Exception as e:
        print(f"Erro ao mudar status: {e}")

def remover_produto(id_prod):
    """Deleta do banco"""
    try:
        supabase.table("produtos").delete().eq("id", id_prod).execute()
    except Exception as e:
        print(f"Erro ao deletar: {e}")