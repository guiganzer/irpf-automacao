import subprocess
import time
import logging
import os

class AppManager:
    """Gerencia o ciclo de vida de aplicativos externos do SO."""
    
    def __init__(self, app_path: str):
        self.app_path = app_path
        self._process = None
        # Extrai apenas o nome do arquivo (ex: 'IRPF2026.exe') para usar no fail-safe
        self._exe_name = os.path.basename(app_path)

    def start(self):
        """Inicia o aplicativo e salva a referência do processo."""
        if not os.path.exists(self.app_path):
            raise FileNotFoundError(f"Executável não encontrado: {self.app_path}")
            
        logging.info(f"Iniciando aplicativo: {self.app_path}")
        self._process = subprocess.Popen(self.app_path)
        
        # Tempo de respiro para a JVM do Java alocar memória e renderizar a splash screen
        time.sleep(6) 

    def stop(self):
        """
        Encerra o aplicativo contornando o comportamento de launcher do Java.
        """
        logging.info("Iniciando extermínio da interface do IRPF...")

        # 1ª Linha de Defesa: Matar pelo PID original (caso o launcher ainda esteja vivo segurando a árvore)
        if self._process:
            try:
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(self._process.pid)], 
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        # 2ª Linha de Defesa (A Cirúrgica): Matar pela identificação da Janela
        # A flag /FI (Filter) permite buscar processos cujo título da janela comece com "IRPF 2026"
        # O asterisco (*) no final é essencial para ignorar espaços em branco invisíveis.
        try:
            subprocess.run(['taskkill', '/F', '/FI', 'WINDOWTITLE eq IRPF 2026*'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("Sinal letal enviado para a janela 'IRPF 2026'.")
        except Exception as e:
            logging.debug(f"Erro silencioso no taskkill por título: {e}")

        # 3ª Linha de Defesa (A Nuclear): Matar o motor do Java
        # ATENÇÃO: Como estamos em um ambiente de automação dedicado, a forma mais garantida 
        # de limpar a memória é matar o executável 'javaw.exe'. 
        # (Se você rodar outras automações ou sistemas Java ao mesmo tempo nesta máquina, elas também cairão).
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'javaw.exe'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.info("Processo principal do Java (javaw.exe) exterminado da memória.")
        except Exception:
            pass

        self._process = None
        
        # Pausa de 2 segundos para dar tempo de o Windows sumir com o ícone da barra de tarefas
        time.sleep(2)
        logging.info("Limpeza de processos concluída com sucesso.")