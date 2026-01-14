import threading
import time
from datetime import datetime, timedelta
import database
import scraper

class MonitorService:
    def __init__(self, log_callback):
        self.running = False
        self.log = log_callback
        self.thread = None

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            self.log("Monitor Iniciado 🚀")

    def stop(self):
        self.running = False
        self.log("Monitor Parado 🛑")

    def _loop(self):
        while self.running:
            self.log("🔍 Verificando ciclo de atualização...")
            produtos = database.carregar_dados()
            
            # Filtra ativos e que precisam de update (> 2 horas)
            candidatos = []
            agora = datetime.now()
            
            for p in produtos:
                if not p.get('ativo', True):
                    continue
                
                last_check_str = p.get('ultimo_check')
                try:
                    last_check = datetime.fromisoformat(last_check_str)
                except:
                    last_check = datetime.min
                
                # Regra das 2 horas
                if (agora - last_check) > timedelta(hours=2):
                    candidatos.append(p)
            
            # Ordena: O mais antigo primeiro (priority queue simples)
            candidatos.sort(key=lambda x: x['ultimo_check'])
            
            if candidatos:
                # Processa APENAS O PRIMEIRO da fila por ciclo para não sobrecarregar
                # e para respeitar o intervalo de checagem do loop
                prod = candidatos[0]
                self.log(f"♻️ Atualizando: {prod['nome'][:20]}... (Último check: {prod['ultimo_check']})")
                
                dados_novos, erro = scraper.extrair_dados_url(prod['url'])
                
                if dados_novos:
                    old_price = prod['preco_atual']
                    new_price = dados_novos['preco']
                    database.atualizar_preco_produto(prod['id'], new_price)
                    
                    if new_price < old_price:
                        self.log(f"⬇️ PREÇO CAIU! {prod['nome'][:15]} | {old_price} -> {new_price}")
                    elif new_price > old_price:
                        self.log(f"⬆️ SUBIU! {prod['nome'][:15]} | {old_price} -> {new_price}")
                    else:
                        self.log(f"✅ Preço mantido: {new_price}")
                else:
                    self.log(f"❌ Erro ao ler {prod['nome'][:15]}: {erro}")
            else:
                self.log("💤 Nenhum produto precisa de atualização (Todos < 2h).")

            # Aguarda 60 segundos (Minuto a minuto)
            for _ in range(60):
                if not self.running: break
                time.sleep(1)