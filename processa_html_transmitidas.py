from bs4 import BeautifulSoup

# Arquivo HTML de entrada
arquivo_html = "transmitidas.html"

# Arquivo TXT de saída
arquivo_saida = "transmitidas.txt"

valores = []

# Lê o HTML
with open(arquivo_html, "r", encoding="utf-8") as f:
    html = f.read()

# Processa o HTML
soup = BeautifulSoup(html, "html.parser")

for tr in soup.find_all("tr"):

    tds = tr.find_all("td", recursive=False)

    # Ignora linhas que não tenham exatamente 12 TDs
    if len(tds) != 12:
        continue

    # ==========================================
    # NOVA VALIDAÇÃO: Verifica o 5º TD (índice 4)
    # ==========================================
    td_5 = tds[4]
    
    # Busca o texto dentro do span (padrão do JasperReports) ou direto no TD
    span_td_5 = td_5.find("span")
    valor_td_5 = span_td_5.get_text(strip=True) if span_td_5 else td_5.get_text(strip=True)
    
    # Se a string estiver vazia, ignora esta linha inteira e vai para a próxima
    if not valor_td_5:
        continue

    # ==========================================
    # EXTRAÇÃO DO NOME: 11º TD (índice 10)
    # ==========================================
    td_11 = tds[10]
    span_nome = td_11.find("span")

    if span_nome:
        valor_nome = span_nome.get_text(strip=True)

        # Evita linhas de cabeçalho
        if valor_nome and valor_nome != "NOME":
            valores.append(valor_nome)

# Grava os valores no arquivo transmitidas.txt
with open(arquivo_saida, "w", encoding="utf-8") as f:
    for valor in valores:
        f.write(valor + "\n")

print(f"{len(valores)} valores válidos (com recibo) gravados em {arquivo_saida}")