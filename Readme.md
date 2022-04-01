# BRIO assistant

![python version](https://img.shields.io/badge/python-3.8-brightgreen)
![languages](https://img.shields.io/github/languages/top/geekk0/BRIO_Assistant)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/3cc6c94a88dd41be9b84faf38e378752)](https://www.codacy.com/gh/geekk0/BRIO_assistant/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=geekk0/BRIO_assistant&amp;utm_campaign=Badge_Grade)![commit-activity](https://img.shields.io/github/commit-activity/y/geekk0/BRIO_Assistant)
![last-commit](https://img.shields.io/github/last-commit/geekk0/BRIO_Assistant)
![downloads](https://img.shields.io/github/downloads/geekk0/BRIO_assistant/total)
<br>Программа с графическим интерфейсом для автоматизации операций с файлами

## Описание

Эта программа разработана для автоматизации работы с файлами сервера записи видео на windows (может использоваться для работы с разными типами файлов). Разработка велась под конкретные условия, из-за чего названия папок-источников (BRIO) и структура целевых папок (ORIGINAL) фиксированы. Программа выполняет две функции:    
-  Автоматическое копирование файлов в целевые папки и размещение по датам, используя созданные правила и фильтры. 
-  Отслеживает свободное место на диске и уведомляет о достижении указанного минимального значения. Позволяет запустить настраиваемую очистку диска. 

Также имеется блок управления профилями, позволяющий каждому пользователю сохранять персональные настройки.
<br>Логирование событий и ошибок производится в папку log.

<a href="url"><img src="images/BRIO_assistant.png" align="right" width="540" ></a>

## Использование
Перед запуском файла **BRIO_assistant.exe**, указываем в файле **config.ini** 
суффикс (определяет расширение отслеживаемых файлов),
здесь же можно изменить расположение папок-источников и целевых папок
и некоторые дополнительные настройки.
После загрузки интерфейса программы создаем и загружаем новый профиль, после чего в настройках "автокопирования" и "свободного места" (колесико)
указываем желаемые настройки.  "Установить значения" для текущей сессии и "Сохранить настройки" для профиля.
<br>Добавляем фильтры (ключевые слова в названии файла) по которым программа копирует файл в определенную папку. <br>В целевой папке файл появляется с именем _"Файл копируется...**имя_файла**_", после завершения копирования переименовывается по исходному файлу.

## Используемые библиотеки

tkinter
<br>psutil, configparser, logging, queue, threading, locale, pythoncom, win32com.shell.
