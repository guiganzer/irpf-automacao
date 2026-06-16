import time
import logging
import os
from models import VisualAsset
from vision import VisionEngine
from hardware import HardwareController
from app_manager import AppManager
import pygetwindow as gw

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# CONFIGURAÇÕES GLOBAIS DE DIRETÓRIOS
# ==========================================
CAMINHO_IRPF = r"C:\Users\Administrator\Desktop\irpf-automacao\IRPF2026\IRPF2026.exe"
CAMINHO_DECLARACAO = r"C:\Users\Administrator\Desktop\irpf-automacao\saida\Declaracoes"
CAMINHO_RECIBO = r"C:\Users\Administrator\Desktop\irpf-automacao\saida\Recibos"
ARQUIVO_NOMES = "./assets/transmitidas.txt"

os.makedirs(CAMINHO_DECLARACAO, exist_ok=True)
os.makedirs(CAMINHO_RECIBO, exist_ok=True)

# ==========================================
# MAPEAMENTO DA INTERFACE (ASSETS)
# ==========================================
radio_imprimir = VisualAsset(name="Radio Imprimir", template_path="./assets/imprimir.png", threshold=0.90)
cabecalho_recibos = VisualAsset(name="Tela de Recibos", template_path="./assets/titulo_recibos.png", threshold=0.85)

btn_ok_bloqueado = VisualAsset(
    name="Botao OK (Bloqueado)", 
    template_path="./assets/botao_ok_bloqueado.png", 
    threshold=0.88
)

btn_ok_ativo = VisualAsset(
    name="Botao OK (Ativo)", 
    template_path="./assets/botao_ok_ativo.png", 
    threshold=0.88
)

def wait_and_click(engine: VisionEngine, hw: HardwareController, asset: VisualAsset, timeout: int = 10) -> bool:
    """Função utilitária de polling para localizar e clicar."""
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        coordenada = engine.find_target(asset)
        if coordenada:
            hw.click(coordenada[0], coordenada[1])
            return True
        time.sleep(0.5)
    raise TimeoutError(f"Timeout: Elemento [{asset.name}] não encontrado.")

def wait_for_target(engine: VisionEngine, asset: VisualAsset, timeout: int = 10) -> bool:
    """
    Faz polling até que um elemento visual apareça na tela, sem interagir com ele.
    Útil para garantir que uma tela terminou de carregar.
    """
    logging.info(f"Aguardando renderização de: [{asset.name}]...")
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        coordenada = engine.find_target(asset)
        if coordenada:
            logging.info(f"Renderização concluída: [{asset.name}]")
            return True
        time.sleep(0.5)
        
    raise TimeoutError(f"Timeout: Elemento [{asset.name}] não renderizou a tempo.")

def aguardar_janela_windows(titulo_janela: str, timeout: int = 30) -> bool:
    """
    Faz um polling na API do Windows aguardando uma janela específica abrir.
    """
    logging.info(f"Aguardando a janela '{titulo_janela}' abrir...")
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        # Busca janelas que contenham o título especificado
        janelas = gw.getWindowsWithTitle(titulo_janela)
        
        if janelas:
            # Pega a primeira janela encontrada
            janela = janelas[0]
            # Opcional: Garante que ela não está minimizada e tem foco
            if janela.isActive or not janela.isMinimized:
                logging.info(f"Janela '{titulo_janela}' detectada!")
                # Pequena pausa apenas para o Windows terminar a animação de fade-in
                time.sleep(0.3) 
                return True
                
        time.sleep(0.5)
        
    raise TimeoutError(f"Janela '{titulo_janela}' não abriu após {timeout} segundos.")

def verificar_estado_botao(engine: VisionEngine, asset_ativo: VisualAsset, asset_bloqueado: VisualAsset) -> str:
    """
    Verifica a tela atual e retorna se o botão está 'ATIVO', 'BLOQUEADO' ou 'AUSENTE'.
    Isso é instantâneo, sem os loops de polling do wait_and_click.
    """
    # Testa se a versão bloqueada está na tela
    if engine.find_target(asset_bloqueado):
        return "BLOQUEADO"
    
    # Testa se a versão ativa está na tela
    if engine.find_target(asset_ativo):
        return "ATIVO"
        
    return "AUSENTE"

def carregar_nomes() -> list:
    if not os.path.exists(ARQUIVO_NOMES):
        raise FileNotFoundError(f"Arquivo de nomes não encontrado em: {ARQUIVO_NOMES}")
    with open(ARQUIVO_NOMES, 'r', encoding='utf-8') as f:
        return [linha.strip() for linha in f if linha.strip()]

def executar_pipeline():
    """
    Executa o fluxo principal. 
    Retorna True se processou toda a lista sem quebrar.
    Retorna False se um Timeout ou erro de UI ocorreu.
    """
    app = AppManager(CAMINHO_IRPF)
    engine = VisionEngine(debug_mode=False) 
    hw = HardwareController()

    try:
        app.start()
        
        logging.info("Maximizando a janela do IRPF...")
        hw.hotkey('win', 'up')
        time.sleep(1.5) 

        nomes_para_processar = carregar_nomes()
        logging.info(f"Total de registros carregados: {len(nomes_para_processar)}")

        for idx, nome in enumerate(nomes_para_processar):
            logging.info(f"--- Processando Contribuinte [{idx + 1}/{len(nomes_para_processar)}]: {nome} ---")

            # 1. Pré-calcula os caminhos absolutos dos arquivos que deveriam existir
            path_declaracao = os.path.join(CAMINHO_DECLARACAO, f"{nome}.pdf")
            path_recibo = os.path.join(CAMINHO_RECIBO, f"{nome}.pdf")

            # 2. Verifica o estado atual no disco
            precisa_declaracao = not os.path.exists(path_declaracao)
            precisa_recibo = not os.path.exists(path_recibo)

            # Se os dois arquivos já existem, pula as interações de UI, mas mantém o loop rodando
            if not precisa_declaracao and not precisa_recibo:
                logging.info(f"➜ Declaração e Recibo já encontrados no disco para '{nome}'. Pulando automação.")
                continue
            
            logging.info(f"--- Processando Contribuinte [{idx + 1}/{len(nomes_para_processar)}]: {nome} ---")

            # ==========================================
            # FLUXO 1: IMPRIMIR DECLARAÇÃO
            # ==========================================
            if precisa_declaracao:
                logging.info(f"Gerando Declaração...")
                hw.hotkey('ctrl', 'p')
                time.sleep(1.0) 
                hw.hotkey('alt', 'r')
                time.sleep(0.3)
                hw.press('tab')
                time.sleep(0.2)
                hw.write(nome)
                hw.press('tab', presses=2, interval=0.2)
                time.sleep(0.3)
                hw.hotkey('alt', 'o')
                time.sleep(1.0) 
                
                wait_and_click(engine, hw, radio_imprimir, timeout=8)
                
                hw.hotkey('alt', 'o')
                aguardar_janela_windows("Salvar Saída de Impressão como") 
                hw.write(path_declaracao)
                hw.press('enter')
                time.sleep(4.0)

            # ==========================================
            # FLUXO 2: IMPRIMIR RECIBO
            # ==========================================
            if precisa_recibo:
                logging.info(f"Gerando Recibo...")
                hw.hotkey('ctrl', 'r')
                wait_for_target(engine, cabecalho_recibos, 15)

                hw.write(nome)
                hw.press('tab', presses=2, interval=0.2)
                time.sleep(0.3)

                wait_and_click(engine, hw, radio_imprimir, timeout=4)
                hw.hotkey('alt', 'o')

                estado_botao = verificar_estado_botao(engine, btn_ok_ativo, btn_ok_bloqueado)
                if estado_botao == "BLOQUEADO":
                    logging.error(f"Botão de imprimir bloqueado para '{nome}'. A tela pode ter travado ou carregado incompleta.")
                    # O comando 'raise' cria um erro intencional. 
                    # Isso aborta o loop e joga o script direto para o 'finally' (app.stop())
                    raise RuntimeError(f"Travamento detectado no contribuinte {nome} (Botão Bloqueado). Forçando reinício da instância.")
                
                aguardar_janela_windows("Salvar Saída de Impressão como") 
                hw.write(path_recibo)
                hw.press('enter')
                time.sleep(1.5)
            
            logging.info(f"Processamento de {nome} concluído com sucesso.")

        # Se o for terminar sem disparar exceções, o lote inteiro foi concluído
        return True

    except Exception as e:
        # A exceção é capturada, a gente loga a falha, e retorna False para o orquestrador
        logging.error(f"Fluxo interrompido por erro de UI/Timeout: {str(e)}")
        return False
        
    finally:
        # O bloco finally GARANTE que o IRPF será assassinado no SO
        # independentemente se o try deu True ou se o except deu False.
        app.stop()
        engine.close()

# ==========================================
# ORQUESTRADOR DE RESILIÊNCIA (LOOP INFINITO)
# ==========================================
if __name__ == "__main__":
    tentativa = 1
    
    # Substituímos o limite por um laço incondicional
    while True:
        logging.info(f"=== INICIANDO ESTEIRA DE AUTOMAÇÃO (Tentativa {tentativa}) ===")
        
        # O fluxo abre uma nova instância limpa do IRPF. 
        # Se quebrar, o 'finally' interno mata o processo antes de retornar False.
        sucesso_total = executar_pipeline()
        
        if sucesso_total:
            logging.info("🎉 Automação finalizada! Todos os registros foram processados com sucesso.")
            break # Esta é a única rota de fuga do loop: concluir a lista de nomes.
            
        else:
            logging.warning("⚠️ Falha detectada no fluxo. A instância atual do IRPF foi encerrada.")
            logging.info("Aguardando 5 segundos para liberação de processos no Windows antes do reinício...")
            time.sleep(5)
            
            tentativa += 1