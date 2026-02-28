import requests
import pandas as pd
import time
import os
import base64

# ==========================================
# CONFIGURAÇÕES DE LOGIN
# ==========================================
USUARIO = 'SeuLogin'
SENHA = 'SuaSenha'
# ==========================================

def fazer_login(usuario, senha):
    url_login = "https://web.appmykids.com.br/gileadeweb-api/api/kids/public/login"
    
    # Codificando usuário e senha em base64 como o frontend faz
    user_b64 = base64.b64encode(usuario.encode('utf-8')).decode('utf-8')
    senha_b64 = base64.b64encode(senha.encode('utf-8')).decode('utf-8')
    
    payload = {
        "user": user_b64,
        "password": senha_b64,
        "enc": True
    }
    
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://web.gileadesistemas.com.br',
        'Referer': 'https://web.gileadesistemas.com.br/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.post(url_login, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            if token:
                print("✔ Login efetuado com sucesso!\n")
                return token
            else:
                print("Token não encontrado na resposta.")
                return None
        else:
            print(f"Erro ao fazer login. Código: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"Erro inesperado no login: {e}")
        return None

def extrair_familias_excel():
    print("Efetuando login automático no sistema para obter o token...")
    token = fazer_login(USUARIO, SENHA)
    
    if not token:
        print("Cancelando extração por falha no login.")
        return

    # URL atualizada para buscar as Famílias
    url = 'https://web.appmykids.com.br/gileadeweb-api/api/grupo-kids/gquery?action=familia'
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-language': 'pt-BR',
        'content-type': 'application/json;charset=UTF-8',
        'gumgatoken': token,
        'origin': 'https://web.gileadesistemas.com.br',
        'referer': 'https://web.gileadesistemas.com.br/',
        'tela': '#!-familia-list',
        'timezone': 'America/Sao_Paulo',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
    }

    all_data = []
    page_size = 100 
    start = 0

    print("Iniciando extração de dados de Famílias da API...")

    while True:
        print(f"Buscando registros a partir da posição {start}...")
        payload = {
            "start": start,
            "pageSize": page_size,
            "gQuery": {"subQuerys": [], "joins": [], "selects": [], "logicalOperator": "SIMPLE"},
            "sortField": "nomeFonetico", # Atualizado conforme o cURL
            "sortDir": "asc"
        }

        try:
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code != 200:
                print(f"Erro na requisição. Código: {response.status_code}")
                print(response.text)
                break
                
            data = response.json()
            
            if isinstance(data, dict) and 'values' in data:
                items = data['values']
            elif isinstance(data, list):
                items = data
            else:
                items = []
                
            if not items:
                break
                
            all_data.extend(items)
            
            if len(items) < page_size:
                print("Última página atingida.")
                break
                
            start += page_size
            time.sleep(0.3)
            
        except Exception as e:
            print(f"Erro inesperado: {e}")
            break

    print(f"\nTotal de Famílias extraídas com sucesso: {len(all_data)}")

    if all_data:
        print("Estruturando os dados para Excel (achatar JSON)...")
        df = pd.json_normalize(all_data)
        
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, list) else x)

        cols = list(df.columns)
        # Ajustando algumas colunas que costumam ser principais em agrupamentos de pessoas/família
        primeiras_colunas = [c for c in ['id', 'nome', 'nomeFonetico', 'status', 'observacao'] if c in cols]
        outras_colunas = [c for c in cols if c not in primeiras_colunas]
        df = df[primeiras_colunas + outras_colunas]
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'dados_familias.xlsx')
        
        df.to_excel(file_path, index=False)
        print(f"✅ Arquivo Excel gerado com sucesso em: {file_path}")

if __name__ == '__main__':
    extrair_familias_excel()
