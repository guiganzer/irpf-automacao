import cv2
import numpy as np
import mss
import logging
import os
from typing import Tuple, Optional, Dict
from models import VisualAsset

class VisionEngine:
    def __init__(self, debug_mode: bool = False, debug_dir: str = "./debug"):
        self.sct = mss.mss()
        self._template_cache: Dict[str, np.ndarray] = {}
        self.debug_mode = debug_mode
        self.debug_dir = debug_dir
        
        if self.debug_mode:
            os.makedirs(self.debug_dir, exist_ok=True)
            logging.info(f"Engine de Visão iniciada em MODO DEBUG. Imagens serão salvas em: {self.debug_dir}")

    def _get_template(self, path: str) -> np.ndarray:
        if path not in self._template_cache:
            template = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise FileNotFoundError(f"Template não encontrado: {path}")
            self._template_cache[path] = template
        return self._template_cache[path]

    def find_target(self, asset: VisualAsset, monitor_idx: Optional[int] = None) -> Optional[Tuple[int, int]]:
        template = self._get_template(asset.template_path)
        t_height, t_width = template.shape

        # Pega a lista de monitores disponíveis. Ignoramos o índice 0 pois ele junta todas as telas.
        # list(self.sct.monitors) retorna [0, 1, 2] se você tem 2 monitores. 
        monitores_disponiveis = [i for i in range(1, len(self.sct.monitors))]
        
        # Se você não passar um monitor específico, ele vai varrer todos
        monitores_para_verificar = [monitor_idx] if monitor_idx else monitores_disponiveis

        for idx in monitores_para_verificar:
            try:
                monitor_config = self.sct.monitors[idx]
                screenshot_bgra = np.array(self.sct.grab(monitor_config))
                screenshot_gray = cv2.cvtColor(screenshot_bgra, cv2.COLOR_BGRA2GRAY)

                result = cv2.matchTemplate(screenshot_gray, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if self.debug_mode:
                    # Anexa o número do monitor no nome do arquivo de debug
                    debug_name = f"{asset.name}_Monitor_{idx}"
                    self._save_debug_frame(screenshot_bgra, debug_name, max_loc, max_val, asset.threshold, t_width, t_height)

                if max_val >= asset.threshold:
                    top_left_x, top_left_y = max_loc
                    center_x = top_left_x + (t_width // 2)
                    center_y = top_left_y + (t_height // 2)
                    
                    # O "left" e "top" da configuração do mss já tratam a matemática de telas negativas
                    # caso seu monitor 2 esteja posicionado à esquerda ou acima do monitor principal no Windows
                    final_x = center_x + asset.offset_x + monitor_config["left"]
                    final_y = center_y + asset.offset_y + monitor_config["top"]
                    
                    logging.debug(f"Elemento {asset.name} encontrado no Monitor {idx} com score {max_val:.3f}")
                    return (int(final_x), int(final_y))
            
            except Exception as e:
                logging.warning(f"Falha ao processar captura no Monitor {idx}: {str(e)}")

        return None

    def _save_debug_frame(self, bgra_frame: np.ndarray, asset_name: str, best_loc: tuple, max_val: float, threshold: float, width: int, height: int):
        """Desenha um retângulo no melhor match e salva a imagem para auditoria."""
        debug_img = bgra_frame.copy()
        
        # Cor do quadrado: Verde se passou no threshold, Vermelho se falhou
        color = (0, 255, 0) if max_val >= threshold else (0, 0, 255) 
        
        # Desenha o quadrado em volta do que o OpenCV achou mais parecido
        top_left = best_loc
        bottom_right = (top_left[0] + width, top_left[1] + height)
        cv2.rectangle(debug_img, top_left, bottom_right, color, 2)
        
        # Escreve os dados na tela
        texto = f"Score: {max_val:.3f} | Min: {threshold:.3f}"
        cv2.putText(debug_img, texto, (top_left[0], top_left[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # Salva o arquivo sobrescrevendo o anterior (para não lotar o disco no polling)
        filename = os.path.join(self.debug_dir, f"debug_{asset_name.replace(' ', '_')}.png")
        cv2.imwrite(filename, debug_img)

    def close(self):
        self.sct.close()