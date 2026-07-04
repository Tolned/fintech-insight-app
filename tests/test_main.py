import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from src.main import main

# 1. Принудительно прописываем корень проекта в память Python ПЕРЕД импортами
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def test_main_function_calls_run_app():
    """Тест проверяет, что вызов функции main() запускает run_app()."""
    with patch("src.main.run_app") as mock_run_app:
        main()
        mock_run_app.assert_called_once()


def test_main_execution_block_as_subprocess():
    """Тест проверяет работу блока инициализации if __name__ == '__main__' через подпроцесс."""
    import os  # <-- ВСТАВЬТЕ ЭТУ СТРОКУ СЮДА

    # Дальше идёт ваш старый код без изменений:
    main_file_path = str(Path(__file__).resolve().parent / ".." / "src" / "main.py")

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Создаем копию системного окружения и форсируем UTF-8 для Python
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        [sys.executable, main_file_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env  # <-- Передаем правильное окружение с кодировкой
    )

    # Передаем симуляцию ввода Enter, чтобы программа не зависла на input() в run_app()
    stdout, stderr = process.communicate(input="\n")

    # Проверяем, что процесс запустился и вывел приветственное сообщение из run_app
    assert "АКТУАЛЬНЫЙ КУРС ВАЛЮТ" in stdout
    # Убеждаемся, что код завершения процесса — 0 (выполнено без критических ошибок)
    assert process.returncode == 0
