<div style="text-align: center; margin-bottom: 20px;">
  <h1>🏦 Skypro Financial Analytics Widget</h1>
  <p>
    <b>[ Python 3.14 ]</b> &nbsp;&nbsp;•&nbsp;&nbsp; 
    <b>[ Менеджер: Poetry ]</b> &nbsp;&nbsp;•&nbsp;&nbsp; 
    <b>[ Стандарт: PEP 8 ]</b>
  </p>
</div>

<hr>

<h2>📋 Описание проекта</h2>
<p>
  Информационно-аналитический виджет на Python, разработанный в рамках курсового проекта Skypro. 
  Приложение агрегирует банковские транзакции пользователя из локальных JSON-источников, обращается к внешним международным и СНГ API для получения актуальных курсов валют, формирует комплексный аналитический отчет и выводит его на экран в строго валидном JSON-формате согласно требованиям технического задания.
</p>

<h2>⚡ Ключевые возможности проекта (Выполнение ТЗ)</h2>
<ul>
  <li><b>Динамическое приветствие:</b> Автоматически подстраивается под временной интервал компьютера (Доброе утро / День / Вечер / Ночь).</li>
  <li><b>Фильтрация и сортировка ТОП-5:</b> Извлекает ровно 5 самых крупных транзакций по абсолютному значению (модулю) поля <code>amount</code>.</li>
  <li><b>Ультра-отказоустойчивый каскад API:</b> Последовательно опрашивает независимые финансовые шлюзы (<i>NBRB API, AwesomeAPI, Exchangerate Host</i>) для получения живых котировок USD/EUR.</li>
  <li><b>Защита от сетевых сбоев (Fallback):</b> Перехватывает любые тайм-ауты и ошибки сети (включая сбросы соединений <code>10054</code>), автоматически переключаясь на резервные источники или константы без падения скрипта.</li>
  <li><b>Глубокая аналитика расходов:</b> Группирует трат по категориям, вычисляет ТОП-7, отправляет остальные в «Остальное», а также изолированно агрегирует «Переводы» и «Наличные».</li>
  <li><b>Умный поиск по подстроке:</b> Регистронезависимый поиск по полям <code>category</code> и <code>description</code>.</li>
  <li><b>Маскирование персональных данных:</b> Универсальное приведение телефонных номеров из любых форматов к стандарту <code>+7 (9XX) XXX-XX-XX</code>.</li>
</ul>

<h2>📂 Архитектура и структура модулей</h2>
<p>Проект строго разделен на изолированные слои в соответствии с принципом <b>Single Responsibility</b>:</p>

<table style="width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 15px;">
  <thead>
    <tr style="background-color: rgba(0,0,0,0.05);">
      <th style="width: 30%; text-align: left; padding: 8px; border: 1px solid #ddd;">Модуль</th>
      <th style="width: 70%; text-align: left; padding: 8px; border: 1px solid #ddd;">Зона ответственности</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><code>src/main.py</code></td>
      <td style="padding: 8px; border: 1px solid #ddd;">Оригинальная точка входа в программу. Содержит конструкцию <code>if __name__ == "__main__": main()</code> и инициализирует фикс путей импорта.</td>
    </tr>
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><code>src/views.py</code></td>
      <td style="padding: 8px; border: 1px solid #ddd;">Слой интерфейса. Отвечает за сборку финальной структуры отчета, текстовый вывод интерактивных таблиц и демонстрацию примеров.</td>
    </tr>
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><code>src/processing.py</code></td>
      <td style="padding: 8px; border: 1px solid #ddd;">Модуль чистой бизнес-логики и математических расчетов. Все функции полностью изолированы от ввода/вывода (нет <code>print</code> и <code>input</code>) и покрыты подробными докстрингами PEP 257.</td>
    </tr>
    <tr>
      <td style="padding: 8px; border: 1px solid #ddd;"><code>src/utils.py</code></td>
      <td style="padding: 8px; border: 1px solid #ddd;">Слой работы с внешней средой. Отвечает за безопасное чтение файлов через <code>pathlib</code> и интеграцию с внешними веб-серверами через <code>requests</code>.</td>
    </tr>
  </tbody>
</table>

<h2>⚙️ Логирование по стандарту PEP 8</h2>
<p>
  В проекте настроено структурированное скрытое логирование событий. Логи записываются в файл <code>project.log</code> в корневой директории приложения и не засоряют основной консольный вывод пользователя.
</p>
<ul>
  <li><b>Уровень INFO:</b> Фиксирует успешные запуски модулей, чтение файлов и удачные ответы серверов API.</li>
  <li><b>Уровень WARNING / ERROR:</b> Перехватывает точечные исключения (<code>ReadTimeout</code>, <code>KeyError</code>, <code>ValueError</code>), детально описывая причину неполадок вместо использования «слепых» блоков <code>except Exception: pass</code>.</li>
  <li><b>Кодировка UTF-8:</b> Лог-файл корректно отображает кириллические системные сообщения Windows.</li>
</ul>

<h2>🛠️ Инструкция по установке и запуску</h2>

<h3>1. Клонирование репозитория и установка зависимостей</h3>
<pre><code>git clone https://github.com
cd fintech-insight-app
poetry install</code></pre>

<h3>2. Подготовка файлов данных</h3>
<p>Убедитесь, что в корне проекта или внутри папки <code>data/</code> находится ваш исходный файл с банковскими записями под именем <code>operations.json</code>.</p>

<h3>3. Запуск приложения</h3>
<pre><code>poetry run python src/main.py</code></pre>

<hr>

<div style="text-align: center; color: #555;">
  <p>Разработано в учебных целях. Код полностью готов к автоматическому тестированию с помощью <code>pytest</code>.</p>
</div>
