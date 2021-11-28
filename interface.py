import configparser
import ctypes
import os
import queue
import threading
import traceback


from tkinter import *
from tkinter import messagebox
from funcs_and_classes import *
# Импорт переменных из config.ini

config = configparser.ConfigParser()
config.read('config.ini')
users = config['PROFILES']['users']    # Список профилей
users_list = users.split(' ')

# Задаем значения по умолчанию

space_limit = int('72')
autocopy_time_check = int('30')
days_old = int('14')

autocopy_running = False
free_space_running = False
alarm = ''
autocopy_stop = False
ac_command = queue.SimpleQueue()

# Инициализация:
sources = src_init(RAW_SOURCE_LIST)
if not sources:
    alarm = 'Диск BRIO не найден'
destination = dest_init(RAW_ORIGINAL_LIST)
if not destination:
    alarm += '\nДиск ORIGINAL не найден'

gui = Tk()
gui.title("BRIO assistant")
gui.geometry('800x760+350+20')
gui.resizable(width=FALSE, height=FALSE)
gui.configure(bg='darkgrey')

active_user = 'Default'

# Создаем фреймы

profile = LabelFrame(gui, text='Профиль')
profile.configure(bg='grey', height=180, width=800, font=15)
profile.pack()

autocopy = LabelFrame(gui, text='Автоматическое копирование')
autocopy.configure(bg='grey', height=280, width=800, font=15)
autocopy.pack()

free_space = LabelFrame(gui, text='Свободное место')
free_space.configure(bg='grey', height=300, width=800, font=15)
free_space.pack()


def add_profile():
    add_profile_window = Toplevel(gui)
    add_profile_window.title('Новый профиль')
    add_profile_window.geometry('400x100+600+200')
    add_profile_window.resizable(width=FALSE, height=FALSE)
    add_profile_window.configure(bg='darkgrey')
    add_profile_window.focus()

    add_profile_frame = LabelFrame(add_profile_window, text='Введите имя нового профиля')
    add_profile_frame.pack(sid='top', padx=10, pady=10)

    add_profile_entry = Entry(add_profile_window)
    add_profile_entry.pack(sid='top', padx=10)

    btn_set_check_time = Button(add_profile_window, height=1, width=30, text="Сохранить новый профиль",
                                command=lambda: save_profile(add_profile_entry.get()))
    btn_set_check_time.pack(sid='top', pady=10, padx=10)

    def save_profile(profile_name):
        add_profile_entry.delete(0, "end")
        add_profile_entry.insert(0, 'Профиль сохранен!')
        users_list.append(profile_name)
        users_config = users + ' ' + str(profile_name)
        config['PROFILES'] = {'users': users_config}
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
            configfile.close()

        new_config = open(os.path.join(os.getcwd(), 'profiles', profile_name)+'.ini', 'w')
        new_config.close()


def save_values():
    global active_user
    global space_limit
    global autocopy_time_check

    options = configparser.ConfigParser()
    options['SPACE_LIMIT'] = {'space_limit': space_limit}
    options['DAYS_OLD'] = {'days_old': days_old}
    options['AUTOCOPY'] = {'autocopy_time_check': autocopy_time_check}

    with open(os.path.join('profiles', active_user + '.ini'), 'w') as configfile:
        options.write(configfile)


def load_profile():
    load_profile_window = Toplevel(gui)
    load_profile_window.title('Загрузить профиль')
    load_profile_window.geometry('600x400+450+200')
    load_profile_window.resizable(width=FALSE, height=FALSE)
    load_profile_window.configure(bg='darkgrey')
    load_profile_window.focus()

    profile_list = Listbox(load_profile_window, width=50, height=40)
    profile_list.pack(sid='left', padx=20, pady=30)

    for USERS in users_list:
        profile_list.insert(END, USERS)

    load_selected_profile_button = Button(load_profile_window, height=1, width=30,
                                          text="Загрузить этот профиль", command=lambda:
                                          load_selected_profile(profile_list.get(profile_list.curselection())))
    load_selected_profile_button.pack(sid='top', pady=60, padx=10)

    def load_selected_profile(selected_item):
        global active_user
        global space_limit
        global days_old
        global autocopy_time_check

        active_user = selected_item
        active_profile_name_lbl.configure(text=active_user, width=20, bg='lightgrey', activebackground='green')
        config.read(os.path.join('profiles', selected_item+'.ini'))
        try:
            space_limit = config['SPACE_LIMIT']['space_limit']
        except:
            space_limit = space_limit
        try:
            days_old = config['DAYS_OLD']['days_old']
        except:
            days_old = days_old
        try:
            autocopy_time_check = config['AUTOCOPY']['autocopy_time_check']
        except:
            autocopy_time_check = autocopy_time_check
        load_profile_window.destroy()


def open_autocopy_settings():

    check_time = StringVar()
    check_time.set(autocopy_time_check)

    autocopy_settings_window = Toplevel(gui)
    autocopy_settings_window.title('Настройки автокопирования')
    autocopy_settings_window.geometry('600x400+450+200')
    autocopy_settings_window.resizable(width=FALSE, height=FALSE)
    autocopy_settings_window.configure(bg='darkgrey')
    autocopy_settings_window.focus()

    set_check_time_label_name = Label(autocopy_settings_window, text='Через сколько секунд после остановки записи '
                                                                     'файл начинает копироваться ')
    set_check_time_label_name.pack(sid='top', padx=10, pady=10)

    time_check_setting = Entry(autocopy_settings_window, textvariable=check_time)
    time_check_setting.pack(sid='top', padx=10)

    btn_set_check_time = Button(autocopy_settings_window, height=1, width=10, text="Установить",
                                command=lambda: set_check_time(check_time.get()))
    btn_set_check_time.pack(sid='top', pady=10, padx=10)

    def set_check_time(time_value):
        global autocopy_time_check

        time_check_setting.delete(0, "end")
        time_check_setting.insert(0, time_value)
        check_time.set(time_value)

        autocopy_time_check = time_value
        autocopy_settings_window.destroy()


def open_free_space_settings():

    global space_limit
    global days_old

    free_space_settings_window = Toplevel(gui)
    free_space_settings_window.title('Настройки очистки')
    free_space_settings_window.geometry('600x400+450+200')
    free_space_settings_window.resizable(width=FALSE, height=FALSE)
    free_space_settings_window.configure(bg='darkgrey')
    free_space_settings_window.focus()

    set_space_limit_label_name = Label(free_space_settings_window, text='Лимит свободного места на диске в Гб:')
    set_space_limit_label_name.pack(sid='top', padx=10, pady=10)

    current_space_limit = IntVar()
    current_space_limit.set(space_limit)

    space_limit_setting = Entry(free_space_settings_window, textvariable=current_space_limit, width=23)
    space_limit_setting.pack(sid='top', padx=10)

    set_days_old_label_name = Label(free_space_settings_window, text='Старше скольки дней удаляем файлы:')
    set_days_old_label_name.pack(sid='top', padx=10, pady=20)

    current_days_old = IntVar()
    current_days_old.set(days_old)

    days_old_setting = Entry(free_space_settings_window, textvariable=current_days_old, width=23)
    days_old_setting.pack(sid='top', padx=10)

    btn_set_space_limit = Button(free_space_settings_window, height=1, width=10, text="Установить",
                                 command=lambda: set_clean_settings(space_limit_setting.get(), days_old_setting.get()))
    btn_set_space_limit.pack(sid='top', pady=10, padx=10)

    def set_clean_settings(limit, days):
        global space_limit
        global days_old

        space_limit_setting.delete(0, "end")
        space_limit_setting.insert(0, limit)

        space_limit = limit
        days_old = days
        free_space_settings_window.destroy()


def run_autocopy_switcher():
    global autocopy_stop
    global autocopy_running
    if alarm:
        autocopy_messages.set(alarm)
    else:
        autocopy_thread = threading.Thread(None, target=autocopy_starter, daemon=False)
        if autocopy_running is False:
            autocopy_messages.set('...Выполнение операций...')
            autocopy_run_button.configure(text='Активно', activebackground='red', bg='green')
            autocopy_running = True
            autocopy_stop = False
            ac_command.put_nowait(item=autocopy_stop)
            autocopy_thread.start()
        else:
            autocopy_messages.set('...Завершение операций...')
            autocopy_run_button.configure(text='Запустить', activebackground='green', bg='lightgrey')
            autocopy_running = False
            autocopy_stop = True
            ac_command.put_nowait(item=autocopy_stop)



"""def command_print(counter=0):
    autocopy_messages.set(counter)
    if autocopy_running:
        gui.after(1000, lambda: command_print(counter+1))"""


def autocopy_starter():
    while True:
        try:
            for source in sources:
                for i in os.walk(source):
                    for j in i[2]:
                        if j.endswith('mp4'):
                            file = Files(j, i[0])
                            if file.m_time_check():
                                if file.black_list_check():
                                    if file.file_exist_check(destination):
                                        if file.file_stopped_check(i[0], j):
                                            full_path = os.path.join(file.rec_name_folder(destination),
                                                                     file.rec_month_folder(),
                                                                     file.rec_date_folder())
                                            if not os.path.isdir(full_path):
                                                os.makedirs(full_path)
                                            print(full_path)
                                            print(source)
                                            copy_status = file.copy(full_path, source)  # Вызываем копирование

                                            if copy_status == 'aborted':
                                                # При отмене копирования добавляем в black_list
                                                abortion_time = str(datetime.datetime.now())
                                                abortion_time = abortion_time.partition('.')[0]
                                                black_list[abortion_time] = j
        except BaseException as error:
            full_traceback = traceback.format_exc()
            logger.error(full_traceback)
        global autocopy_running
        global autocopy_stop
        time.sleep(1)
        if autocopy_stop:
            break


def run_free_space_switcher():
    global free_space_running
    if alarm:
        free_space_messages.set(alarm)
    else:
        if free_space_running is False:
            free_space_messages.set('...Включено отслеживание свободного места на BRIO...')
            free_space_run_button.configure(text='Активно', activebackground='red', bg='green')
            free_space_running = True
            free_space_on()
        else:
            free_space_messages.set('...Завершение операций...')
            free_space_run_button.configure(text='Запустить', activebackground='green', bg='lightgrey')
            free_space_running = False


def free_space_on():
    if free_space_running:
        status = free_space_tracing(sources, space_limit)
        if status == 'alarm':
            messagebox.showwarning(parent=gui, title='Свободное место на BRIO', message="На диске BRIO осталось меньше " +
                                                                            str(space_limit) + ' Гб, пора запустить очистку')

        gui.after(2000, lambda: free_space_on())


def clean_space():
    if alarm:
        free_space_messages.set(alarm)
    else:
        first_delete_list = first_del_list(days_old)
        logger.debug(first_delete_list)
        output = 'Первоначальный список на удаление: ' + str(first_delete_list)
        free_space_messages.set(output)
        final_list = exist_check(first_delete_list, destination)
        output += '\nФинальный список на удаление:' + str(final_list)
        free_space_messages.set(output)
        output_text = remove(final_list, sources)
        output += '\n' + output_text
        free_space_messages.set(output)




# Фрейм профиль


profile_frame_name = LabelFrame(profile)
profile_frame_name.configure(text='Активный:', width=150, height=60, bg='lightgrey')
profile_frame_name.pack(sid='left', padx=30)
profile.pack_propagate(0)


active_profile_name = StringVar()
active_profile_name.set(active_user)


active_profile_name_lbl = Label(profile_frame_name, text='Default')
active_profile_name_lbl.configure(width=16, bg='lightgrey', font=16)
active_profile_name_lbl.pack()
profile_frame_name.pack_propagate(0)


save_values_button = Button(profile, command=save_values)
save_values_button.configure(text='Сохранить значения', width=20, bg='lightgrey', activebackground='green')
save_values_button.pack(sid='left', pady=50, padx=125)
save_values_button.pack_propagate(0)

add_profile_button = Button(profile, command=add_profile)
add_profile_button.configure(text='Добавить профиль', width=20, bg='lightgrey', activebackground='green')
add_profile_button.pack(sid='top', pady=30)
add_profile_button.pack_propagate(0)

load_profile_button = Button(profile, command=load_profile)
load_profile_button.configure(text="Загрузить профиль", width=20, bg='lightgrey', activebackground='green')
load_profile_button.pack(sid='top', pady=20, padx=20)
load_profile_button.pack_propagate(0)

# Фрейм автоматического копирования

autocopy_run_button = Button(autocopy, command=run_autocopy_switcher)
autocopy_run_button.configure(text='Запустить', width=20, bg='lightgrey', activebackground='green')
autocopy.pack_propagate(0)
autocopy_run_button.pack(sid='left', padx=40)

autocopy_settings_btn = PhotoImage(file='settings_new.png')
img_label = Label(image=autocopy_settings_btn)
dummy_button = Button(autocopy, image=autocopy_settings_btn, command=open_autocopy_settings, borderwidth=0, bg='grey',
                      activebackground='grey')
dummy_button.pack(sid='right', padx=60)

autocopy_messages = StringVar()
autocopy_messages.set('Здесь отображаются действия с файлами')

autocopy_messages_label = Label(autocopy)
autocopy_messages_label.configure(textvariable=autocopy_messages, width=50, height=13, bg='lightgrey')
autocopy_messages_label.pack(sid='left', padx=20)


# Фрейм свободного места

space_limit_sv = StringVar()
space_limit_sv.set(space_limit)

free_space_run_button = Button(free_space, command=clean_space)
free_space_run_button.configure(text='Освободить место', width=14, bg='lightgrey', activebackground='green')
free_space.pack_propagate(0)
free_space_run_button.pack(sid='left', padx=10)

free_space_run_button = Button(free_space, command=run_free_space_switcher)
free_space_run_button.configure(text='Запустить', width=14, bg='lightgrey', activebackground='green')
free_space.pack_propagate(0)
free_space_run_button.pack(sid='left', padx=0)

free_space_settings_btn = PhotoImage(file='settings_new.png')
free_space_img_label = Label(image=free_space_settings_btn)
free_space_dummy_button = Button(free_space, image=free_space_settings_btn, command=open_free_space_settings,
                                 borderwidth=0, bg='grey', activebackground='grey')
free_space_dummy_button.pack(sid='right', padx=60)

free_space_messages = StringVar()
free_space_messages.set('Здесь отображаются действия с файлами')

free_space_messages_label = Label(free_space)
free_space_messages_label.configure(textvariable=free_space_messages, width=50, height=13, bg='lightgrey', wraplength=330)
free_space_messages_label.pack(sid='left', padx=19)


print(active_user, space_limit)

gui.mainloop()
