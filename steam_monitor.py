#!/usr/bin/env python
# coding: utf-8

# In[17]:


import time
import datetime
import os
import re
import winreg
from typing import List, Tuple, Optional


def get_steam_path() -> str:
    """
    Получает путь установки Steam из реестра Windows.

    Returns:
        str: Абсолютный путь к директории Steam.

    Raises:
        Exception: Если Steam не найден в реестре.
    """
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Valve\Steam"
        )
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        return steam_path
    except FileNotFoundError:
        raise Exception("Steam не найден в реестре")


def read_log_lines(log_file: str) -> List[str]:
    """
    Считывает строки из лог-файла Steam.

    Args:
        log_file (str): Путь к файлу content_log.txt.

    Returns:
        List[str]: Список строк из лог-файла.
    """
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def parse_download_state(lines: List[str]) -> Tuple[Optional[float], bool, str]:
    """
    Анализирует лог Steam и определяет состояние загрузки.

    Args:
        lines (List[str]): Строки лог-файла.

    Returns:
        Tuple[Optional[float], bool, str]:
            - скорость загрузки (Mbps) или None
            - флаг паузы (True — пауза или загрузки нет)
            - AppID загружаемой игры
    """
    download_rate: Optional[float] = None
    paused: bool = True
    appid: str = "Неизвестен"

    for line in reversed(lines):
        if "Current download rate" in line:
            ts_match = re.search(r"\[(.*?)\]", line)
            if not ts_match:
                continue

            log_time = datetime.datetime.strptime(
                ts_match.group(1), "%Y-%m-%d %H:%M:%S"
            )

            if (datetime.datetime.now() - log_time).total_seconds() <= 60:
                try:
                    download_rate = float(line.split()[-2])
                    paused = False
                except ValueError:
                    pass
                break

    for line in reversed(lines):
        if "AppID" in line:
            match = re.search(r"AppID\s+(\d+)", line)
            if match:
                appid = match.group(1)
            break

    return download_rate, paused, appid


def get_game_name(steam_path: str, appid: str) -> str:
    """
    Возвращает название игры по AppID, читая appmanifest в steamapps.
    Если файл не найден — возвращает AppID.

    Args:
        steam_path (str): Путь к Steam.
        appid (str): ID игры.

    Returns:
        str: Название игры или AppID.
    """
    manifest_file = os.path.join(steam_path, "steamapps", f"appmanifest_{appid}.acf")
    if not os.path.exists(manifest_file):
        return f"AppID {appid}"

    try:
        with open(manifest_file, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if '"name"' in line:
                    name_match = re.search(r'"name"\s+"(.+)"', line)
                    if name_match:
                        return name_match.group(1)
    except Exception:
        pass

    return f"AppID {appid}"


def main() -> None:
    """
    Основной цикл мониторинга загрузок Steam.
    """
    steam_path = get_steam_path()
    log_file = os.path.join(steam_path, "logs", "content_log.txt")

    interval: int = 60
    duration: int = 5

    print("Мониторинг загрузок Steam запущен")
    print("Steam найден в:", steam_path)
    print("=" * 33, "\n")

    for minute in range(1, duration + 1):
        lines = read_log_lines(log_file)
        rate_mbps, paused, appid = parse_download_state(lines)

        print(f"[{minute} минута]")

        if paused or rate_mbps is None:
            print("Загрузка на паузе или отсутствует\n")
        else:
            rate_mb_s = rate_mbps / 8 
            game_name = get_game_name(steam_path, appid)
            print(f"{game_name}")
            print(f"Скорость загрузки: {rate_mb_s:.2f} MB/s\n")

        time.sleep(interval)

    print("Мониторинг завершён!")


if __name__ == "__main__":
    main()


# In[ ]:




