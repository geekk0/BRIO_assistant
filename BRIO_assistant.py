import os
import threading

from tkinter import *
from tkinter import messagebox
from funcs_and_classes import *


config = configparser.ConfigParser()                # Импорт переменных из config.ini
config.read('config.ini')
users = config['PROFILES']['users']
users_list = users.split(' ')

space_limit = 72                                    # Задаем значения по умолчанию для свободного места
autocopy_pause_time_check = 0
autocopy_delta_time = 10000
days_old = 7

black_list_lifetime = BLACK_LIST_DELTA_INT          # Задаем значения по умолчанию для автоматического копирования
filters_peregony = PEREGONY
filters_efir = NOVOSTI
filters_studia = STUDIA

autocopy_running = False
free_space_running = False
alarm = ''
autocopy_stop = False
ac_command = queue.SimpleQueue()
autocopy_files_list = ''

sources = src_init(RAW_SOURCE_LIST)                  # Определение папок-источников и целевых папок:
if not sources:
    sources = [os.path.join(os.getcwd(), "BRIO")]
destination = dest_init(RAW_ORIGINAL_LIST)
if not destination:
    destination = os.path.join(os.getcwd(), "ORIGINAL")

gui = Tk()
gui.title("BRIO assistant")
gui.geometry('800x760+350+20')
gui.resizable(width=FALSE, height=FALSE)
gui.configure(bg='darkgrey')

active_user = 'Default'


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
    global autocopy_pause_time_check
    global filters_peregony
    global filters_efir
    global filters_studia
    global black_list_lifetime

    options = configparser.ConfigParser()
    options['SPACE_LIMIT'] = {'space_limit': str(space_limit)}
    options['DAYS_OLD'] = {'days_old': str(days_old)}
    options['AUTOCOPY'] = {'autocopy_pause_time_check': autocopy_pause_time_check,
                           'autocopy_delta_time': autocopy_delta_time, 'filters_peregony': filters_peregony,
                           'filters_efir': filters_efir, 'filters_studia': filters_studia,
                           'black_list_lifetime': black_list_lifetime}

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
        global autocopy_pause_time_check
        global autocopy_delta_time
        global filters_peregony
        global filters_efir
        global filters_studia
        global black_list_lifetime

        active_user = selected_item
        active_profile_name_lbl.configure(text=active_user, width=20, bg='lightgrey', activebackground='green')
        config.read(os.path.join('profiles', selected_item+'.ini'))
        try:
            space_limit = int(config['SPACE_LIMIT']['space_limit'])
        except ValueError:
            space_limit = space_limit
        try:
            days_old = int(config['DAYS_OLD']['days_old'])
        except ValueError:
            days_old = days_old
        try:
            autocopy_pause_time_check = int(config['AUTOCOPY']['autocopy_pause_time_check'])
        except ValueError:
            autocopy_pause_time_check = autocopy_pause_time_check
        try:
            autocopy_delta_time = int(config['AUTOCOPY']['autocopy_delta_time'])
        except ValueError:
            autocopy_delta_time = autocopy_delta_time
        try:
            filters_peregony = ast.literal_eval(config['AUTOCOPY']['filters_peregony'])
        except ValueError:
            filters_peregony = filters_peregony
        try:
            filters_efir = ast.literal_eval(config['AUTOCOPY']['filters_efir'])
        except ValueError:
            filters_efir = filters_efir
        try:
            filters_studia = ast.literal_eval(config['AUTOCOPY']['filters_studia'])
        except ValueError:
            filters_studia = filters_efir
        try:
            black_list_lifetime = int(config['AUTOCOPY']['black_list_lifetime'])
        except ValueError:
            black_list_lifetime = BLACK_LIST_DELTA_INT
        load_profile_window.destroy()


def open_autocopy_settings():

    check_time = IntVar()
    check_time.set(autocopy_pause_time_check)

    delta_time = IntVar()
    delta_time.set(int(autocopy_delta_time/60/60))

    black_list_time = IntVar()
    black_list_time.set(int(black_list_lifetime/60/60))

    autocopy_settings_window = Toplevel(gui)
    autocopy_settings_window.title('Настройки автокопирования')
    autocopy_settings_window.geometry('600x500+450+200')
    autocopy_settings_window.resizable(width=FALSE, height=FALSE)
    autocopy_settings_window.configure(bg='darkgrey')
    autocopy_settings_window.focus()

    set_check_time_label_name = Label(autocopy_settings_window, text='Через сколько секунд после остановки записи '
                                                                     'файл начинает копироваться: ')   # Rename time
    set_check_time_label_name.pack(sid='top', padx=10, pady=10)

    time_check_setting = Entry(autocopy_settings_window, textvariable=check_time)
    time_check_setting.pack(sid='top', padx=10)

    set_delta_time_label_name = Label(autocopy_settings_window,
                                      text='Насколько старые файлы будем копировать (в часах):')  # Delta
    set_delta_time_label_name.pack(sid='top', padx=10, pady=20)

    delta_time_setting = Entry(autocopy_settings_window, textvariable=delta_time)
    delta_time_setting.pack(sid='top', padx=10)

    set_black_list_time_label = Label(autocopy_settings_window,
                                      text='При отмене копирования файла, через сколько часов попытка возобновится:')
    set_black_list_time_label.pack(sid='top', padx=10, pady=20)

    black_list_time_setting = Entry(autocopy_settings_window, textvariable=black_list_time)
    black_list_time_setting.pack(sid='top', padx=10)

    btn_set_values = Button(autocopy_settings_window, height=1, width=20, text="Установить значения",
                            command=lambda: set_autocopy_settings(check_time.get(), delta_time.get(),
                                                                  black_list_time.get()))
    btn_set_values.pack(sid='top', pady=30, padx=0)

    set_filters_peregony_label = Label(autocopy_settings_window, text='Настроить фильтры для копирования:')  # Filters
    set_filters_peregony_label.pack(sid='top', padx=0, pady=20)

    btn_filters_peregony = Button(autocopy_settings_window, height=1, width=15, text="ПЕРЕГОНЫ",
                                  command=lambda: show_filters_peregony())
    btn_filters_peregony.pack(sid='top', pady=0, padx=0)

    btn_filters_efir = Button(autocopy_settings_window, height=1, width=15, text="ЗАПИСЬ ЭФИРА",
                              command=lambda: show_filters_efir())
    btn_filters_efir.pack(sid='top', pady=10, padx=30)

    btn_filters_studia = Button(autocopy_settings_window, height=1, width=15, text="ЗАПИСЬ СТУДИЙ",
                                command=lambda: show_filters_studia())
    btn_filters_studia.pack(sid='top', pady=0, padx=60)

    def set_autocopy_settings(time_value, local_delta_time, local_black_list_time):
        global autocopy_pause_time_check
        global autocopy_delta_time
        global black_list_lifetime

        time_check_setting.delete(0, "end")
        time_check_setting.insert(0, time_value)
        check_time.set(time_value)

        delta_time_setting.delete(0, "end")
        delta_time_setting.insert(0, delta_time)

        black_list_time_setting.delete(0, "end")
        black_list_time_setting.insert(0, local_black_list_time)

        autocopy_pause_time_check = time_value
        autocopy_delta_time = local_delta_time*60*60
        black_list_lifetime = local_black_list_time*60*60

        autocopy_settings_window.destroy()

    def show_filters_peregony():
        global active_user
        global filters_peregony

        new_filter_peregony = StringVar()

        filters_peregony_window = Toplevel(autocopy_settings_window)
        filters_peregony_window.title('Фильтры для ПЕРЕГОНЫ')
        filters_peregony_window.geometry('550x300+475+250')
        filters_peregony_window.resizable(width=FALSE, height=FALSE)
        filters_peregony_window.configure(bg='darkgrey')
        filters_peregony_window.focus()

        filters_peregony_list = Listbox(filters_peregony_window, width=50, height=40)
        filters_peregony_list.pack(sid='left', padx=20, pady=30)

        config.read(os.path.join('profiles', active_user + '.ini'))

        set_new_filter_peregony_label = Label(filters_peregony_window, text='Введите новый фильтр:')
        set_new_filter_peregony_label.pack(sid='top', padx=10, pady=20)

        new_filter_peregony_entry = Entry(filters_peregony_window, textvariable=new_filter_peregony)
        new_filter_peregony_entry.pack(sid='top', padx=0)

        add_filter_peregony_btn = Button(filters_peregony_window, text="Добавить",
                                         command=lambda: add_filter_peregony(new_filter_peregony.get()))
        add_filter_peregony_btn.pack(sid="top", pady=5)

        delete_filter_peregony_btn = Button(filters_peregony_window, text="Удалить выбранный фильтр",
                                            command=lambda: delete_filter_peregony((filters_peregony_list.curselection()
                                                                                    )))
        delete_filter_peregony_btn.pack(sid='top', pady=10)

        for single_filter in filters_peregony:
            filters_peregony_list.insert(END, single_filter)

        def add_filter_peregony(local_new_filter_peregony):
            global filters_peregony
            filters_peregony_list.insert(END, local_new_filter_peregony)
            filters_peregony.append(local_new_filter_peregony)

        def delete_filter_peregony(selected_item):
            filters_peregony.remove(filters_peregony_list.get(selected_item))
            filters_peregony_list.delete(selected_item)

    def show_filters_efir():
        global active_user
        global filters_efir

        new_filter_efir = StringVar()

        filters_efir_window = Toplevel(autocopy_settings_window)
        filters_efir_window.title('Фильтры для ЗАПИСЬ ЭФИРА')
        filters_efir_window.geometry('550x300+475+250')
        filters_efir_window.resizable(width=FALSE, height=FALSE)
        filters_efir_window.configure(bg='darkgrey')
        filters_efir_window.focus()

        filters_efir_list = Listbox(filters_efir_window, width=50, height=40)
        filters_efir_list.pack(sid='left', padx=20, pady=30)

        config.read(os.path.join('profiles', active_user + '.ini'))

        set_new_filter_efir_label = Label(filters_efir_window,
                                          text='Введите новый фильтр:')  # Delta
        set_new_filter_efir_label.pack(sid='top', padx=10, pady=20)

        new_filter_efir_entry = Entry(filters_efir_window, textvariable=new_filter_efir)
        new_filter_efir_entry.pack(sid='top', padx=0)

        add_filter_efir_btn = Button(filters_efir_window, text="Добавить",
                                     command=lambda: add_filter_efir(new_filter_efir.get()))
        add_filter_efir_btn.pack(sid="top", pady=5)

        delete_filter_efir_btn = Button(filters_efir_window, text="Удалить выбранный фильтр",
                                        command=lambda: delete_filter_efir((filters_efir_list.curselection())))
        delete_filter_efir_btn.pack(sid='top', pady=10)

        for single_filter in filters_efir:
            filters_efir_list.insert(END, single_filter)

        def add_filter_efir(local_new_filter_efir):
            global filters_efir
            filters_efir_list.insert(END, local_new_filter_efir)
            filters_efir.append(local_new_filter_efir)

        def delete_filter_efir(selected_item):
            filters_efir.remove(filters_efir_list.get(selected_item))
            filters_efir_list.delete(selected_item)

    def show_filters_studia():
        global active_user
        global filters_studia

        new_filter_studia = StringVar()

        filters_studia_window = Toplevel(autocopy_settings_window)
        filters_studia_window.title('Фильтры для записи студий')
        filters_studia_window.geometry('550x300+475+250')
        filters_studia_window.resizable(width=FALSE, height=FALSE)
        filters_studia_window.configure(bg='darkgrey')
        filters_studia_window.focus()

        filters_studia_list = Listbox(filters_studia_window, width=50, height=40)
        filters_studia_list.pack(sid='left', padx=20, pady=30)

        config.read(os.path.join('profiles', active_user + '.ini'))

        set_new_filter_studia_label = Label(filters_studia_window,
                                            text='Введите новый фильтр:')  # Delta
        set_new_filter_studia_label.pack(sid='top', padx=10, pady=20)

        new_filter_studia_entry = Entry(filters_studia_window, textvariable=new_filter_studia)
        new_filter_studia_entry.pack(sid='top', padx=0)

        add_filter_studia_btn = Button(filters_studia_window, text="Добавить",
                                       command=lambda: add_filter_studia(new_filter_studia.get()))
        add_filter_studia_btn.pack(sid="top", pady=5)

        delete_filter_studia_btn = Button(filters_studia_window, text="Удалить выбранный фильтр",
                                          command=lambda: delete_filter_studia((filters_studia_list.curselection())))
        delete_filter_studia_btn.pack(sid='top', pady=10)

        for single_filter in filters_studia:
            filters_studia_list.insert(END, single_filter)

        def add_filter_studia(local_new_filter_studia):
            global filters_studia
            filters_studia_list.insert(END, local_new_filter_studia)
            filters_studia.append(local_new_filter_studia)

        def delete_filter_studia(selected_item):
            filters_studia.remove(filters_studia_list.get(selected_item))
            filters_studia_list.delete(selected_item)


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
    global autocopy_files_list

    if alarm:
        autocopy_messages.set(alarm)
    else:
        autocopy_thread = threading.Thread(None, target=autocopy_starter, daemon=True)
        if autocopy_running is False:
            autocopy_messages.set('...Автоматическое копирование запущено...')
            autocopy_run_button.configure(text='Активно', activebackground='red', bg='green')
            autocopy_running = True
            autocopy_stop = False
            ac_command.put_nowait(item=autocopy_stop)
            autocopy_thread.start()
        else:
            autocopy_messages.set(autocopy_files_list+'\nАвтоматическое копирование завершено.')
            autocopy_run_button.configure(text='Запустить', activebackground='green', bg='lightgrey')
            autocopy_running = False
            autocopy_stop = True
            ac_command.put_nowait(item=autocopy_stop)
            autocopy_files_list = ''
            autocopy_thread.do_run = "False"


def autocopy_starter():
    ac_thread = threading.currentThread()
    while getattr(ac_thread, "do_run", True):
        try:
            for source in sources:
                for i in os.walk(source):
                    for j in i[2]:
                        if j.endswith(SUFFIX):
                            file = Files(j, i[0])
                            if file.m_time_check(autocopy_pause_time_check, autocopy_delta_time):
                                if file.black_list_check(black_list_lifetime):
                                    if file.file_exist_check(destination, filters_peregony, filters_efir,
                                                             filters_studia):
                                        if file_stopped_check(i[0], j):
                                            full_path = os.path.join(file.rec_name_folder(destination, filters_peregony,
                                                                                          filters_efir, filters_studia),
                                                                     rec_month_folder(), rec_date_folder())
                                            global autocopy_stop
                                            if autocopy_stop:
                                                break

                                            if not os.path.isdir(full_path):
                                                os.makedirs(full_path)

                                            if not check_thread_is_running(file.name):

                                                logger.debug("Запущено копирование файла: "+j)

                                                copy_status = 'in_progress'
                                                copy_thread = threading.Thread(None, copy_monitor,
                                                                               args=(file.name, copy_status), daemon=False)

                                                copy_thread.name = file.name
                                                copy_thread.start()

                                                copy_status = file.copy(full_path, source)  # Вызываем копирование

                                                if copy_status == 'aborted':
                                                    # При отмене копирования добавляем в black_list
                                                    abortion_time = str(datetime.datetime.now())
                                                    abortion_time = abortion_time.partition('.')[0]
                                                    black_list[abortion_time] = j

                                                    logger.debug('Копирование файла ' + j + ' отменено')

                                                elif copy_status == "complete":

                                                    logger.debug('Файл ' + j + ' скопирован')

                                                copy_thread_result = threading.Thread(None, copy_monitor,
                                                                                      args=(file.name, copy_status),
                                                                                      daemon=False)
                                                copy_thread_result.start()


        except FileExistsError:
            full_traceback = traceback.format_exc()
            logger.error(full_traceback)
        global autocopy_running
        if autocopy_stop:
            break
        time.sleep(2)


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
            free_space_messages.set('Отслеживание свободного места завершено.')
            free_space_run_button.configure(text='Запустить', activebackground='green', bg='lightgrey')
            free_space_running = False


def free_space_on():
    if free_space_running:
        status = free_space_tracing(sources, space_limit)
        if status == 'alarm':
            messagebox.showwarning(parent=gui, title='Свободное место на BRIO',
                                   message="На диске BRIO осталось меньше " + str(space_limit) +
                                           ' Гб, пора запустить очистку')

        gui.after(2000, lambda: free_space_on())


def clean_space():
    if alarm:
        free_space_messages.set(alarm)
    else:
        first_delete_list = first_del_list(int(days_old))
        output = ''
        free_space_messages.set(output)
        final_list = exist_check(first_delete_list, destination)
        free_space_messages.set(output)
        output_text = remove(final_list, sources)
        output += '\n' + output_text
        free_space_messages.set(output)


def copy_monitor(filename, status):
    global autocopy_files_list

    if 'in_progress' in status:
        autocopy_files_list += '\nКопируется файл ' + filename
    elif 'aborted' in status:
        autocopy_files_list += '\nКопирование файла '+filename+' прервано'
    elif 'complete' in status:
        autocopy_files_list += '\nФайл ' + filename+' скопирован'


    autocopy_messages.set(autocopy_files_list)


def check_thread_is_running(file_name):
    for thread in threading.enumerate():
        if thread.name == file_name:
            return True
        else:
            return False


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
save_values_button.configure(text='Сохранить настройки', width=20, bg='lightgrey', activebackground='green')
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

autocopy_settings_btn = PhotoImage(file='images/settings_new.png')
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

space_limit_sv = IntVar()
space_limit_sv.set(space_limit)

free_space_run_button = Button(free_space, command=clean_space)
free_space_run_button.configure(text='Освободить место', width=14, bg='lightgrey', activebackground='green')
free_space.pack_propagate(0)
free_space_run_button.pack(sid='left', padx=10)

free_space_run_button = Button(free_space, command=run_free_space_switcher)
free_space_run_button.configure(text='Запустить', width=14, bg='lightgrey', activebackground='green')
free_space.pack_propagate(0)
free_space_run_button.pack(sid='left', padx=0)

free_space_settings_btn = PhotoImage(file='images/settings_new.png')
free_space_img_label = Label(image=free_space_settings_btn)
free_space_dummy_button = Button(free_space, image=free_space_settings_btn, command=open_free_space_settings,
                                 borderwidth=0, bg='grey', activebackground='grey')
free_space_dummy_button.pack(sid='right', padx=60)

free_space_messages = StringVar()
free_space_messages.set('Здесь отображаются действия с файлами')

free_space_messages_label = Label(free_space)
free_space_messages_label.configure(textvariable=free_space_messages, width=50, height=13, bg='lightgrey',
                                    wraplength=330)
free_space_messages_label.pack(sid='left', padx=19)

gui.mainloop()
