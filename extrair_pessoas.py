import requests
import pandas as pd
import time
import os

def extrair_dados_excel():
    url = 'https://web.appmykids.com.br/gileadeweb-api/api/pessoacadastro/gquery'
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-language': 'pt-BR',
        'content-type': 'application/json;charset=UTF-8',
        'gumgatoken': '1126619L8612E1787779698566C177222769856600O8387.8612.I',
        'origin': 'https://web.gileadesistemas.com.br',
        'referer': 'https://web.gileadesistemas.com.br/',
        'tela': '#!-pessoacadastro-list',
        'timezone': 'America/Sao_Paulo',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36'
    }

    all_data = []
    page_size = 100 
    start = 0

    print("Iniciando extração de dados da API...")

    while True:
        print(f"Buscando registros a partir da posição {start}...")
        payload = {
            "start": start,
            "pageSize": page_size,
            "gQuery": {"subQuerys": [], "joins": [], "selects": [], "logicalOperator": "SIMPLE"},
            "sortField": "nome",
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

    print(f"\nTotal de registros extraídos com sucesso: {len(all_data)}")

    if all_data:
        print("Estruturando os dados para Excel (achatar JSON)...")
        # Usamos json_normalize para transformar objetos ({ "endereco": {"rua": ...} }) em colunas (endereco.rua)
        df = pd.json_normalize(all_data)
        
        # Converter listas internas para strings para que o Excel aceite salvar
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, list) else x)

        # Reorganizar as colunas para as que costumam ser mais importantes aparecerem primeiro
        cols = list(df.columns)
        primeiras_colunas = [c for c in ['id', 'nome', 'cpf', 'telefone', 'email', 'status'] if c in cols]
        outras_colunas = [c for c in cols if c not in primeiras_colunas]
        df = df[primeiras_colunas + outras_colunas]
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'dados_pessoas.xlsx')
        
        # Salvar em Excel puro
        df.to_excel(file_path, index=False)
        print(f"✅ Arquivo Excel gerado com sucesso em: {file_path}")

if __name__ == '__main__':
    extrair_dados_excel()
