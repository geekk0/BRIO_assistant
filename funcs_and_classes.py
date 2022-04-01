import configparser
import datetime
import logging
import os
import queue
import time
import locale
import calendar
import ast

import psutil as psutil
import pythoncom

from win32com.shell import shell, shellcon

black_list = {}

current_path = os.getcwd()

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

cute_format = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S' )

debug_log = logging.FileHandler(os.path.join(current_path, 'logs/debug.log'))     # to log debug messages
debug_log.setLevel(logging.DEBUG)
debug_log.setFormatter(cute_format)

error_log = logging.FileHandler(os.path.join(current_path, 'logs/error.log'))     # to log errors messages
error_log.setLevel(logging.ERROR)
error_log.setFormatter(cute_format)

logger.addHandler(debug_log)
logger.addHandler(error_log)

config = configparser.ConfigParser()
config.read(os.path.join(os.getcwd(), "config.ini"))
config.sections()

RAW_SOURCE_LIST = ast.literal_eval(config["PATHS"]["Disk_BRIO"])
RAW_ORIGINAL_LIST = ast.literal_eval(config["PATHS"]["Disk_ORIGINAL"])
SUFFIX = config.get("PATHS", "suffix")
DELTA_CHECK_INT = config.getint(section="COPY", option="delta_check_int")
PAUSE_TIME_INT = config.getint("COPY", "PAUSE_TIME_INT")
BLACK_LIST_DELTA_INT = config.getint("COPY", "BLACK_LIST_DELTA_INT")

PEREGONY = ast.literal_eval(config["COPY"]["PEREGONY"])
NOVOSTI = ast.literal_eval(config["COPY"]["NOVOSTI"])
STUDIA = ast.literal_eval(config["COPY"]["STUDIA"])
FILE_STOPPED_CHECK_INT = config.getint("COPY", "FILE_STOPPED_CHECK_INT")

q = queue.Queue()

deleted_files = 0
optimized_memory = 0
cant_delete = 0
file_stopped = False


def src_init(raw_dirs_list):  # Находим диски BRIO
    srcs_list = []
    for s in raw_dirs_list:
        if os.path.isdir(s):
            srcs_list.append(s)
            logger.debug("Найдены диски BRIO "+s)
    if not srcs_list:
        # logger.debug("Диски BRIO не найдены")
        return False
    return srcs_list


def dest_init(raw_dirs_list):  # Находим диски ORIGINAL
    dest_path = ''
    for d in raw_dirs_list:
        if os.path.isdir(d):
            dest_path = d
            logger.debug("ORIGINAL на диске "+d)
    if not dest_path:
        # logger.debug("ORIGINAL не найден")
        return False
    return dest_path


def rec_month_folder():
    try:
        locale.setlocale(locale.LC_ALL, "")

        month = datetime.datetime.now().strftime("%B").upper()
        return month

    except Exception as e:
        print(e)


def rec_date_folder():
    today = datetime.datetime.today()
    str_folder_date = str(today)
    return str_folder_date[8] + str_folder_date[9]  # Формируем имя папки под число


def file_stopped_check(folder, name):
    global file_stopped
    try:
        size_first = os.path.getsize(os.path.join(folder, name))
        time.sleep(FILE_STOPPED_CHECK_INT)
        size_second = os.path.getsize(os.path.join(folder, name))
    except Exception as e:
        logger.debug(e)
        size_first = None
        size_second = None

    if size_first == size_second:
        file_stopped = True
        return True


def first_del_list(days_old):   # Первоначальный список на удаление (по дате создания)

    srcs_list = src_init(RAW_SOURCE_LIST)

    first_delete_list = []

    for directory in srcs_list:

        for i in os.walk(directory):

            for j in i[2]:

                if j.endswith(SUFFIX):
                    path = os.path.join(os.path.abspath(i[0]), j)
                    file_create_date = time.ctime(os.path.getctime(path))
                    with calendar.different_locale('C'):
                        converted_file_create_date = datetime.datetime.strptime\
                            (file_create_date, '%a %b %d %H:%M:%S %Y').date()
                        now = datetime.date.today()
                        time_check = datetime.timedelta(days=days_old)

                        if (now - converted_file_create_date) > time_check:
                            if 'не удалять' not in path and 'НЕ УДАЛЯТЬ' not in path:
                                first_delete_list.append(j)

    logger.debug('Первоначальный список файлов на удаление ' + str(first_delete_list))

    return first_delete_list


def exist_check(first_delete_list, destination):

    final_list = []


    source_dirs = ['ИСХОДНИКИ ПЕРЕГОНЫ', "ИСХОДНИКИ ЗАПИСЬ ЭФИРА", "ИСХОДНИКИ ЗАПИСИ СТУДИЙ"]

    for directory in source_dirs:
        source_files_directory = os.path.join(destination, directory)

        for i in os.walk(source_files_directory):
            for j in i[2]:
                if j in first_delete_list and j not in final_list:
                    final_list.append(j)

    logger.debug('Финальный список на удаление '+str(final_list))
    return final_list


def remove(final_list, sources):

    for directory in sources:

        for i in os.walk(directory):
            for j in i[2]:
                if j in final_list:

                    cache_memory = os.path.getsize(os.path.join(os.path.abspath(i[0]), j))  # Память удаляемого файла

                    del_file_path = os.path.join(os.path.abspath(i[0]), j)
                    os.remove(del_file_path)

                    global deleted_files
                    global optimized_memory

                    deleted_files += 1
                    optimized_memory += cache_memory

    logger.debug('Скрипт очистки завершен.')

    output_text = 'Очистка закончена. Удалено ' + str(deleted_files) + ' файлов, освободилось '+ \
                  str(int(optimized_memory / 1024 / 1024 / 1024)) + ' Гб '+ str(cant_delete)+' файлов только для чтения'
    return output_text


def free_space_tracing(sources, space_limit):
    disks = []
    for source in sources:
        disk = source[:3]
        if os.path.isdir(disk):
            disks.append(disk)

        for disk in disks:
            free = psutil.disk_usage(disk).free / (1024 * 1024 * 1024)
            if free < int(space_limit):
                return 'alarm'


class Files:

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def file_size(self):
        file_path = os.path.join(self.path, self.name)
        return os.path.getsize(file_path)

    def file_mtime(self):
        with calendar.different_locale('C'):
            return datetime.datetime.strptime(time.ctime(os.path.getmtime(self.path + '/' + self.name)),
                                              "%a %b %d %H:%M:%S %Y")

    def m_time_check(self, autocopy_pause_time_check=PAUSE_TIME_INT, autocopy_delta_time=DELTA_CHECK_INT):  # Проверка на подходящее время изменения файла
        today = datetime.datetime.today()
        delta = (today - self.file_mtime())

        delta_check = datetime.timedelta(seconds=autocopy_delta_time)
        pause_time = datetime.timedelta(seconds=autocopy_pause_time_check)

        if (delta < delta_check) and (delta > pause_time):
            return True

    def black_list_check(self, black_list_lifetime):

        match = False
        tmp_black_list = black_list.copy()

        for key in tmp_black_list.keys():
            black_list_add_time = datetime.datetime.strptime(key, '%Y-%m-%d %H:%M:%S')
            delta = datetime.timedelta(seconds=black_list_lifetime)
            if (datetime.datetime.now() - black_list_add_time) > delta:
                del black_list[key]
            item = black_list.get(key)

            if item == self.name:  # Проверка есть ли файл в списке удаленных
                match = True
                break
        if not match:
            return True
        else:
            return False

    def rec_name_folder(self, destination, filters_peregony, filters_efir, filters_studia):
        match = False
        for x in filters_peregony:
            if x in self.name.upper():
                match = True
                return os.path.join(os.path.abspath(destination), r'ИСХОДНИКИ ПЕРЕГОНЫ')

        if not match:
            for y in filters_efir:
                if y in self.name.upper():
                    match = True
                    return os.path.join(os.path.abspath(destination), r'ИСХОДНИКИ ЗАПИСЬ ЭФИРА')
        if not match:
            for z in filters_studia:
                if z in self.name.upper():
                    match = True
                    return os.path.join(os.path.abspath(destination), r'ИСХОДНИКИ ЗАПИСИ СТУДИЙ')
        if not match:
            return False

    def file_exist_check(self, destination, filters_peregony, filters_efir, filters_studia):

        try:
            full_path = os.path.join(self.rec_name_folder(destination, filters_peregony, filters_efir, filters_studia),
                                     rec_month_folder(), rec_date_folder())
        except FileExistsError as error:
            logger.debug(error)
            full_path = None
        if full_path:
            if os.path.isfile(os.path.join(full_path, self.name)):
                return False
            else:
                return True

    def copy(self, full_path, source):
        try:
            pythoncom.CoInitializeEx(0)
            pfo = pythoncom.CoCreateInstance(shell.CLSID_FileOperation, None, pythoncom.CLSCTX_ALL,
                                             shell.IID_IFileOperation)
            pfo.SetOperationFlags(shellcon.FOF_NOCONFIRMATION)
            dst = shell.SHCreateItemFromParsingName(full_path, None, shell.IID_IShellItem)
            shell_src = os.path.join(os.path.abspath(source), self.name)
            src = shell.SHCreateItemFromParsingName(shell_src, None, shell.IID_IShellItem)

            pfo.CopyItem(src, dst, 'Файл копируется.....' + self.name)  # Schedule an operation to be performed
            success = pfo.PerformOperations()
            print(type(success))
            aborted = pfo.GetAnyOperationsAborted()
            print(type(aborted))
            os.rename(os.path.join(full_path, 'Файл копируется.....' + self.name), os.path.join(full_path, self.name))

            return 'complete'
        except BaseException as error:
            msg = 'aborted'
            logger.error(error)
            return msg


if __name__ == "__main__":



    input()

