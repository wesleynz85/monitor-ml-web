import json
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Referer": "https://www.mercadolivre.com.br/",
    "Connection": "keep-alive"
}

ARQUIVO_CONFIG = "config_sistema.json"

def get_headers():
    if os.path.exists(ARQUIVO_CONFIG):
        try:
            with open(ARQUIVO_CONFIG, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
                cookie = cfg.get("cookie", "")
                if cookie:
                    HEADERS["Cookie"] = cookie
        except: pass
    return HEADERS

def salvar_cookie(cookie_str):
    with open(ARQUIVO_CONFIG, 'w', encoding='utf-8') as f:
        json.dump({"cookie": cookie_str}, f)