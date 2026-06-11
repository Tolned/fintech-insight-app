import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from src.main import main


def test_main_function_calls_run_app():
    """Тест проверяет, что вызов функции main() запускает run_app()."""
    with patch("src.main.run_app") as mock_run_app:
        main()
        mock_run_app.assert_called_once()


def test_main_execution_block_as_subprocess():
    """Тест проверяет работу блока инициализации if __name__ == '__main__' через подпроцесс."""
    # Получаем абсолютный путь к вашему файлу main.py
    main_file_path = str(Path(__file__).resolve().parent / ".." / "src" / "main.py")

    # Запускаем скрипт в отдельном процессе, симулируя ввод пользователя (передаем пустую строку)
    process = subprocess.Popen(
        [sys.executable, main_file_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    # Передаем симуляцию ввода Enter, чтобы программа не зависла на input() в run_app()
    stdout, stderr = process.communicate(input="\n")

    # Проверяем, что процесс запустился и вывел приветственное сообщение из run_app
    assert "АКТУАЛЬНЫЙ КУРС ВАЛЮТ" in stdout
    # Убеждаемся, что код завершения процесса — 0 (выполнено без критических ошибок)
    assert process.returncode == 0
