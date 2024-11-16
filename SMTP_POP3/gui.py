import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from SMTP_POP3.main import EmailClient
import re


class EmailClientGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Почтовый клиент")
        self.root.geometry("800x600")

        self.email_client = EmailClient()

        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=5, pady=5)

        # Создаем вкладки
        self.setup_tab = ttk.Frame(self.notebook)
        self.send_tab = ttk.Frame(self.notebook)
        self.receive_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.setup_tab, text='Настройки')
        self.notebook.add(self.send_tab, text='Отправка')
        self.notebook.add(self.receive_tab, text='Получение')

        self._setup_config_tab()
        self._setup_send_tab()
        self._setup_receive_tab()

    def _setup_config_tab(self):
        # SMTP настройки
        smtp_frame = ttk.LabelFrame(self.setup_tab, text='Настройки SMTP')
        smtp_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(smtp_frame, text='Сервер:').grid(row=0, column=0, padx=5, pady=5)
        self.smtp_server = ttk.Entry(smtp_frame)
        self.smtp_server.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(smtp_frame, text='Порт:').grid(row=1, column=0, padx=5, pady=5)
        self.smtp_port = ttk.Entry(smtp_frame)
        self.smtp_port.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(smtp_frame, text='Логин:').grid(row=2, column=0, padx=5, pady=5)
        self.smtp_username = ttk.Entry(smtp_frame)
        self.smtp_username.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(smtp_frame, text='Пароль:').grid(row=3, column=0, padx=5, pady=5)
        self.smtp_password = ttk.Entry(smtp_frame, show='*')
        self.smtp_password.grid(row=3, column=1, padx=5, pady=5)

        self.use_smtp_tls = tk.BooleanVar(value=True)
        ttk.Checkbutton(smtp_frame, text='Использовать TLS',
                        variable=self.use_smtp_tls).grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Button(smtp_frame, text='Подключиться',
                   command=self._connect_smtp).grid(row=5, column=0, columnspan=2, pady=10)

        # POP3 настройки
        pop3_frame = ttk.LabelFrame(self.setup_tab, text='Настройки POP3')
        pop3_frame.pack(fill='x', padx=5, pady=5)

        ttk.Label(pop3_frame, text='Сервер:').grid(row=0, column=0, padx=5, pady=5)
        self.pop3_server = ttk.Entry(pop3_frame)
        self.pop3_server.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(pop3_frame, text='Порт:').grid(row=1, column=0, padx=5, pady=5)
        self.pop3_port = ttk.Entry(pop3_frame)
        self.pop3_port.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(pop3_frame, text='Логин:').grid(row=2, column=0, padx=5, pady=5)
        self.pop3_username = ttk.Entry(pop3_frame)
        self.pop3_username.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(pop3_frame, text='Пароль:').grid(row=3, column=0, padx=5, pady=5)
        self.pop3_password = ttk.Entry(pop3_frame, show='*')
        self.pop3_password.grid(row=3, column=1, padx=5, pady=5)

        self.use_pop3_ssl = tk.BooleanVar(value=True)
        ttk.Checkbutton(pop3_frame, text='Использовать SSL',
                        variable=self.use_pop3_ssl).grid(row=4, column=0, columnspan=2, pady=5)

        ttk.Button(pop3_frame, text='Подключиться',
                   command=self._connect_pop3).grid(row=5, column=0, columnspan=2, pady=10)

    def _setup_send_tab(self):
        # Форма отправки письма
        ttk.Label(self.send_tab, text='От кого:').pack(anchor='w', padx=5, pady=2)
        self.from_entry = ttk.Entry(self.send_tab)
        self.from_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(self.send_tab, text='Кому:').pack(anchor='w', padx=5, pady=2)
        self.to_entry = ttk.Entry(self.send_tab)
        self.to_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(self.send_tab, text='Тема:').pack(anchor='w', padx=5, pady=2)
        self.subject_entry = ttk.Entry(self.send_tab)
        self.subject_entry.pack(fill='x', padx=5, pady=2)

        ttk.Label(self.send_tab, text='Сообщение:').pack(anchor='w', padx=5, pady=2)
        self.message_text = scrolledtext.ScrolledText(self.send_tab, height=15)
        self.message_text.pack(fill='both', expand=True, padx=5, pady=5)

        ttk.Button(self.send_tab, text='Отправить',
                   command=self._send_email).pack(pady=10)

    def _setup_receive_tab(self):
        # Панель управления
        control_frame = ttk.Frame(self.receive_tab)
        control_frame.pack(fill='x', padx=5, pady=5)

        ttk.Button(control_frame, text='Обновить список',
                   command=self._refresh_messages).pack(side='left', padx=5)
        ttk.Button(control_frame, text='Удалить выбранное',
                   command=self._delete_selected).pack(side='left', padx=5)

        # Список писем с расширенными колонками
        self.messages_tree = ttk.Treeview(self.receive_tab,
                                          columns=('number', 'subject', 'from', 'date', 'size'),
                                          show='headings')

        # Настройка заголовков колонок
        self.messages_tree.heading('number', text='№')
        self.messages_tree.heading('subject', text='Тема')
        self.messages_tree.heading('from', text='От кого')
        self.messages_tree.heading('date', text='Дата')
        self.messages_tree.heading('size', text='Размер')

        # Настройка ширины колонок
        self.messages_tree.column('number', width=50)
        self.messages_tree.column('subject', width=200)
        self.messages_tree.column('from', width=200)
        self.messages_tree.column('date', width=150)
        self.messages_tree.column('size', width=100)

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(self.receive_tab, orient="vertical", command=self.messages_tree.yview)
        self.messages_tree.configure(yscrollcommand=scrollbar.set)

        # Размещаем список и скроллбар
        self.messages_tree.pack(side='left', fill='both', expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side='right', fill='y', padx=(0, 5), pady=5)

        self.messages_tree.bind('<<TreeviewSelect>>', self._on_select_message)

        # Фрейм для просмотра письма
        message_frame = ttk.LabelFrame(self.receive_tab, text='Содержимое письма')
        message_frame.pack(fill='both', expand=True, padx=5, pady=5)

        # Добавляем поля для отображения заголовков письма
        headers_frame = ttk.Frame(message_frame)
        headers_frame.pack(fill='x', padx=5, pady=5)

        self.message_headers = {
            'From': ttk.Label(headers_frame, text='От: '),
            'To': ttk.Label(headers_frame, text='Кому: '),
            'Subject': ttk.Label(headers_frame, text='Тема: '),
            'Date': ttk.Label(headers_frame, text='Дата: ')
        }

        for i, (key, label) in enumerate(self.message_headers.items()):
            label.grid(row=i, column=0, sticky='w', padx=5, pady=2)

        # Просмотр содержимого письма
        self.message_view = scrolledtext.ScrolledText(message_frame, height=10)
        self.message_view.pack(fill='both', expand=True, padx=5, pady=5)

    def _connect_smtp(self):
        try:
            server = self.smtp_server.get()
            port = int(self.smtp_port.get())
            username = self.smtp_username.get()
            password = self.smtp_password.get()
            use_tls = self.use_smtp_tls.get()

            if self.email_client.setup_smtp(server, port, username, password, use_tls):
                messagebox.showinfo("Успех", "SMTP подключение установлено")
            else:
                messagebox.showerror("Ошибка", "Не удалось подключиться к SMTP серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")

    def _connect_pop3(self):
        try:
            server = self.pop3_server.get()
            port = int(self.pop3_port.get())
            username = self.pop3_username.get()
            password = self.pop3_password.get()
            use_ssl = self.use_pop3_ssl.get()

            if self.email_client.setup_pop3(server, port, username, password, use_ssl):
                messagebox.showinfo("Успех", "POP3 подключение установлено")
                self._refresh_messages()
            else:
                messagebox.showerror("Ошибка", "Не удалось подключиться к POP3 серверу")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")

    def _send_email(self):
        if not self.email_client.smtp_authenticated:
            messagebox.showerror("Ошибка", "Сначала настройте SMTP подключение")
            return

        from_addr = self.from_entry.get()
        to_addr = self.to_entry.get()
        subject = self.subject_entry.get()
        message = self.message_text.get('1.0', tk.END)

        # Простая валидация email
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, from_addr) or not re.match(email_pattern, to_addr):
            messagebox.showerror("Ошибка", "Неверный формат email адреса")
            return

        if self.email_client.send_email(from_addr, to_addr, subject, message):
            messagebox.showinfo("Успех", "Письмо отправлено")
            # Очищаем поля
            self.subject_entry.delete(0, tk.END)
            self.message_text.delete('1.0', tk.END)
        else:
            messagebox.showerror("Ошибка", "Не удалось отправить письмо")

    def _refresh_messages(self):
        if not self.email_client.pop3_authenticated:
            messagebox.showerror("Ошибка", "Сначала настройте POP3 подключение")
            return

        # Очищаем список
        for item in self.messages_tree.get_children():
            self.messages_tree.delete(item)

        try:
            # Получаем список писем
            messages = self.email_client.list_messages()

            if messages:
                for msg_num, msg_size, headers in messages:
                    try:
                        # Обработка заголовков с учетом возможного отсутствия данных
                        subject = headers.get('Subject', '(Без темы)')
                        from_addr = headers.get('From', '(Неизвестный отправитель)')
                        date = headers.get('Date', '(Дата неизвестна)')

                        # Форматируем размер для читаемости
                        if msg_size > 1024 * 1024:
                            size_str = f"{msg_size / (1024 * 1024):.1f} MB"
                        elif msg_size > 1024:
                            size_str = f"{msg_size / 1024:.1f} KB"
                        else:
                            size_str = f"{msg_size} B"

                        # Вставляем данные в дерево
                        self.messages_tree.insert('', 'end',
                                                  values=(msg_num, subject, from_addr, date, size_str))
                    except Exception as e:
                        print(f"Ошибка при обработке сообщения {msg_num}: {str(e)}")
                        continue
            else:
                print("Список сообщений пуст")
                messagebox.showinfo("Информация", "Нет доступных сообщений")

        except Exception as e:
            print(f"Ошибка при получении списка писем: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось получить список писем: {str(e)}")

    def _on_select_message(self, event):
        selection = self.messages_tree.selection()
        if not selection:
            return

        item = self.messages_tree.item(selection[0])
        msg_num = item['values'][0]

        try:
            # Очищаем просмотрщик
            self.message_view.delete('1.0', tk.END)

            # Получаем и отображаем содержимое письма
            if self.email_client.pop3_authenticated:
                # Получаем заголовки и содержимое письма
                headers = self.email_client.get_message_headers(msg_num)
                content = self.email_client.read_message(msg_num)

                # Обновляем заголовки
                if headers:
                    for key, label in self.message_headers.items():
                        value = headers.get(key, '')
                        label.configure(text=f'{key}: {value}')

                # Отображаем содержимое
                if content:
                    self.message_view.insert('1.0', content)
                else:
                    self.message_view.insert('1.0', 'Не удалось загрузить содержимое письма')
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить письмо: {str(e)}")

    def _delete_selected(self):
        selection = self.messages_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите письмо для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Удалить выбранное письмо?"):
            item = self.messages_tree.item(selection[0])
            msg_num = item['values'][0]

            if self.email_client.pop3_authenticated:
                self.email_client.delete_message(msg_num)
                self.messages_tree.delete(selection[0])
                messagebox.showinfo("Успех", f"Письмо #{msg_num} удалено")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = EmailClientGUI()
    app.run()
