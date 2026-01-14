import requests
from bs4 import BeautifulSoup
import re
import time
import random
from config import get_headers

def extrair_dados_url(url):
    """Retorna (titulo, preco) ou (None, erro)"""
    time.sleep(random.uniform(1, 3)) # Delay ético
    
    try:
        resp = requests.get(url, headers=get_headers(), timeout=10)
        if resp.status_code != 200:
            return None, f"Erro HTTP {resp.status_code}"
            
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # 1. Título
        titulo = ""
        h1 = soup.find('h1', class_='ui-pdp-title')
        if not h1: h1 = soup.find('h1')
        if h1: titulo = h1.get_text(strip=True)
        else: titulo = "Produto Sem Título"
        
        # 2. Preço (Lógica simplificada e robusta)
        preco = 0.0
        # Tenta meta tag (geralmente a mais confiável)
        meta_price = soup.find('meta', {'itemprop': 'price'})
        if meta_price:
            try: preco = float(meta_price['content'])
            except: pass
            
        # Tenta JSON script se meta falhar
        if preco == 0:
            match = re.search(r'\"price\":(\d+\.?\d*)', resp.text)
            if match:
                try: preco = float(match.group(1))
                except: pass
        
        # Tenta classes visuais
        if preco == 0:
            tag = soup.find('span', class_='andes-money-amount__fraction')
            if tag:
                try: preco = float(tag.text.replace('.', '').replace(',', '.'))
                except: pass
                
        if preco > 0:
            return {"nome": titulo, "preco": preco}, None
        else:
            return None, "Preço não encontrado (Bloqueio ou Layout novo)"
            
    except Exception as e:
        return None, str(e)