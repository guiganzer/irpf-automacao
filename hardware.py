import pyautogui
import logging

class HardwareController:
    @staticmethod
    def click(x: int, y: int, duration: float = 0.2):
        pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
        pyautogui.click()

    @staticmethod
    def write(text: str, interval: float = 0.01):
        # O intervalo previne que o SO engula caracteres se a VM estiver lenta
        pyautogui.write(text, interval=interval)

    @staticmethod
    def press(key: str, presses: int = 1, interval: float = 0.1):
        pyautogui.press(key, presses=presses, interval=interval)

    @staticmethod
    def hotkey(*args):
        pyautogui.hotkey(*args)