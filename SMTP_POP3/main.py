from datetime import datetime
from POP3.main import POP3Client
from SMTP.main import SMTPClient
import base64
from email_decoder import EmailDecoder


class EmailClient:
    def __init__(self):
        self.smtp_client = None
        self.pop3_client = None
        self.smtp_authenticated = False
        self.pop3_authenticated = False
        self.log_file = f"email_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def setup_smtp(self, server, port, username, password, use_tls=True):
        try:
            self.smtp_client = SMTPClient()
            if not self.smtp_client.connect(server, port):
                return False

            if use_tls:
                self.smtp_client.send_command("STARTTLS")

            # Выполняем аутентификацию SMTP
            auth_string = base64.b64encode(f"\0{username}\0{password}".encode()).decode()
            self.smtp_client.send_command("AUTH PLAIN " + auth_string)

            self.smtp_authenticated = True
            self.log_message("SMTP аутентификация успешна", "ИНФО:")
            return True

        except Exception as e:
            self.log_message(f"Ошибка настройки SMTP: {str(e)}", "ОШИБКА:")
            return False

    def check_smtp_auth(self):
        if not self.smtp_authenticated:
            self.log_message("Требуется аутентификация SMTP", "ОШИБКА:")
            return False
        return True

    def check_pop3_auth(self):
        """
        Проверяет статус аутентификации POP3 и соединение с сервером.
        Возвращает True, если соединение активно и аутентификация выполнена успешно.
        """
        if not self.pop3_authenticated or not self.pop3_client:
            self.log_message("POP3 клиент не аутентифицирован или не подключен", "ОШИБКА:")
            return False
        try:
            # Проверяем соединение с помощью NOOP команды
            response = self.pop3_client.send_command("NOOP")
            if not response or "+OK" not in response:
                self.pop3_authenticated = False
                self.log_message("POP3 соединение потеряно", "ОШИБКА:")
                return False
            return True
        except Exception as e:
            self.pop3_authenticated = False
            self.log_message(f"Ошибка при проверке POP3 соединения: {str(e)}", "ОШИБКА:")
            return False

    def setup_pop3(self, server, port, username, password, use_ssl=True):
        try:
            self.pop3_client = POP3Client(server, port, use_ssl)
            if not self.pop3_client.connect():
                return False

            # Выполняем аутентификацию POP3
            user_response = self.pop3_client.send_command(f"USER {username}")
            if not user_response or "+OK" not in user_response:
                self.log_message("Ошибка при отправке команды USER", "ОШИБКА:")
                return False

            pass_response = self.pop3_client.send_command(f"PASS {password}")
            if not pass_response or "+OK" not in pass_response:
                self.log_message("Ошибка при отправке команды PASS", "ОШИБКА:")
                return False

            self.pop3_authenticated = True
            self.log_message("POP3 аутентификация успешна", "ИНФО:")
            return True

        except Exception as e:
            self.log_message(f"Ошибка настройки POP3: {str(e)}", "ОШИБКА:")
            return False

    def list_messages(self):
        """
        Получает список сообщений с сервера POP3.
        Возвращает список кортежей (номер, размер, заголовки).
        """
        if not self.pop3_client or not self.check_pop3_auth():
            self.log_message("POP3 клиент не настроен или не авторизован", "ОШИБКА:")
            return None

        try:
            # Получаем список сообщений
            response = self.pop3_client.send_command("LIST")
            if not response or "+OK" not in response:
                self.log_message("Ошибка при получении списка сообщений", "ОШИБКА:")
                return None

            messages_data = self.pop3_client.receive_multiline()
            if not messages_data:
                return []

            # Парсим список сообщений
            messages = []
            for line in messages_data.split('\n'):
                if line.strip():
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        try:
                            msg_num = int(parts[0])
                            msg_size = int(parts[1])

                            # Получаем заголовки для каждого сообщения
                            headers = self.get_message_headers(msg_num)
                            messages.append((msg_num, msg_size, headers))
                        except ValueError:
                            continue

            self.log_message(f"Получено {len(messages)} сообщений", "ИНФО:")
            return messages

        except Exception as e:
            self.log_message(f"Ошибка при получении списка сообщений: {str(e)}", "ОШИБКА:")
            return None

    def log_message(self, message, level="ИНФО:"):
        """Записывает сообщение в лог-файл"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} {level} {message}\n"
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Ошибка записи в лог: {str(e)}")

    def get_message_headers(self, msg_number):
        if not self.pop3_client or not self.check_pop3_auth():
            return None

        try:
            response = self.pop3_client.send_command(f"TOP {msg_number} 0")
            if not response or "+OK" not in response:
                return None

            headers_data = self.pop3_client.receive_multiline()
            if not headers_data:
                return None

            # Парсим заголовки
            headers = {}
            current_header = None
            current_value = []

            for line in headers_data.split('\n'):
                line = line.strip()
                if not line:
                    continue

                if line[0] in [' ', '\t'] and current_header:
                    current_value.append(line.strip())
                else:
                    if current_header:
                        headers[current_header] = EmailDecoder.decode_header_value(' '.join(current_value))

                    if ':' in line:
                        current_header = line.split(':', 1)[0].strip()
                        current_value = [line.split(':', 1)[1].strip()]

            if current_header:
                headers[current_header] = EmailDecoder.decode_header_value(' '.join(current_value))

            return headers

        except Exception as e:
            self.log_message(f"Ошибка при получении заголовков сообщения {msg_number}: {str(e)}", "ОШИБКА:")
            return None

    def send_email(self, from_addr, to_addr, subject, message):
        if not self.smtp_client or not self.check_smtp_auth():
            print("SMTP клиент не настроен или не авторизован")
            return False

    def read_message(self, msg_number):
        if not self.pop3_client or not self.check_pop3_auth():
            return None

        try:
            response = self.pop3_client.send_command(f"RETR {msg_number}")
            if not response or "+OK" not in response:
                return None

            message_data = self.pop3_client.receive_multiline()
            if not message_data:
                return None

            # Декодируем и возвращаем содержимое сообщения
            return EmailDecoder.decode_message_content(message_data)

        except Exception as e:
            self.log_message(f"Ошибка при чтении сообщения {msg_number}: {str(e)}", "ОШИБКА:")
            return None

    def delete_message(self, msg_number):
        if not self.pop3_client or not self.check_pop3_auth():
            print("POP3 клиент не настроен или не авторизован")
            return

    def close(self):
        if self.smtp_client:
            if self.smtp_authenticated:
                self.smtp_client.send_command("QUIT")
            self.smtp_client.close()
        if self.pop3_client:
            if self.pop3_authenticated:
                self.pop3_client.send_command("QUIT")
            self.pop3_client.close()


def print_menu():
    print("\nПочтовый клиент - Главное меню")
    print("1. Настроить SMTP")
    print("2. Настроить POP3")
    print("3. Отправить письмо")
    print("4. Просмотреть список писем")
    print("5. Прочитать письмо")
    print("6. Удалить письмо")
    print("0. Выход")


def main():
    client = EmailClient()

    while True:
        print_menu()
        choice = input("\nВыберите действие (0-6): ")

        if choice == "0":
            client.close()
            print("Программа завершена")
            break

        elif choice == "1":
            server = input("Введите SMTP сервер: ")
            port = int(input("Введите порт SMTP: "))
            username = input("Введите имя пользователя: ")
            password = input("Введите пароль: ")
            if client.setup_smtp(server, port, username, password):
                print("SMTP успешно настроен и авторизован")
            else:
                print("Ошибка настройки или авторизации SMTP")

        elif choice == "2":
            server = input("Введите POP3 сервер: ")
            port = int(input("Введите порт POP3: "))
            username = input("Введите имя пользователя: ")
            password = input("Введите пароль: ")
            use_ssl = input("Использовать SSL? (д/н): ").lower() == 'д'
            if client.setup_pop3(server, port, username, password, use_ssl):
                print("POP3 успешно настроен и авторизован")
            else:
                print("Ошибка настройки или авторизации POP3")

        elif choice == "3":
            from_addr = input("От кого: ")
            to_addr = input("Кому: ")
            subject = input("Тема: ")
            print("Введите текст сообщения (для завершения введите пустую строку):")
            lines = []
            while True:
                line = input()
                if not line:
                    break
                lines.append(line)
            message = "\n".join(lines)
            client.send_email(from_addr, to_addr, subject, message)

        elif choice == "4":
            client.list_messages()

        elif choice == "5":
            msg_num = input("Введите номер сообщения: ")
            client.read_message(msg_num)

        elif choice == "6":
            msg_num = input("Введите номер сообщения для удаления: ")
            client.delete_message(msg_num)

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    main()
