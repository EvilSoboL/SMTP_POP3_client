from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from SMTP.main import SMTPClient
from POP3.main import POP3Client
import base64


class EmailClient:
    def __init__(self):
        self.smtp_client = None
        self.pop3_client = None
        self.smtp_authenticated = False
        self.pop3_authenticated = False
        self.log_file = f"email_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log_message(self, message, direction=""):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {direction} {message}\n")
        print(f"{direction} {message}")

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

    def setup_pop3(self, server, port, username, password, use_ssl=True):
        try:
            self.pop3_client = POP3Client(server, port, use_ssl)
            if not self.pop3_client.connect():
                return False

            # Выполняем аутентификацию POP3
            self.pop3_client.send_command(f"USER {username}")
            response = self.pop3_client.send_command(f"PASS {password}")

            if response and "+OK" in response:
                self.pop3_authenticated = True
                self.log_message("POP3 аутентификация успешна", "ИНФО:")
                return True
            return False

        except Exception as e:
            self.log_message(f"Ошибка настройки POP3: {str(e)}", "ОШИБКА:")
            return False

    def check_smtp_auth(self):
        if not self.smtp_authenticated:
            self.log_message("Требуется аутентификация SMTP", "ОШИБКА:")
            return False
        return True

    def check_pop3_auth(self):
        if not self.pop3_authenticated:
            self.log_message("Требуется аутентификация POP3", "ОШИБКА:")
            return False
        return True

    def send_email(self, from_addr, to_addr, subject, message):
        if not self.smtp_client or not self.check_smtp_auth():
            print("SMTP клиент не настроен или не авторизован")
            return False

        try:
            msg = MIMEText(message, 'plain', 'utf-8')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = from_addr
            msg['To'] = to_addr

            self.smtp_client.send_command(f"MAIL FROM:<{from_addr}>")
            self.smtp_client.send_command(f"RCPT TO:<{to_addr}>")
            self.smtp_client.send_command("DATA")
            self.smtp_client.send_command(msg.as_string() + "\r\n.")

            self.log_message("Сообщение успешно отправлено", "ИНФО:")
            return True

        except Exception as e:
            self.log_message(f"Ошибка при отправке сообщения: {str(e)}", "ОШИБКА:")
            return False

    def list_messages(self):
        if not self.pop3_client or not self.check_pop3_auth():
            print("POP3 клиент не настроен или не авторизован")
            return

        response = self.pop3_client.send_command("LIST")
        if response and "+OK" in response:
            messages = self.pop3_client.receive_multiline()
            if messages:
                print("\nСписок сообщений:")
                print(messages)

    def read_message(self, msg_number):
        if not self.pop3_client or not self.check_pop3_auth():
            print("POP3 клиент не настроен или не авторизован")
            return

        response = self.pop3_client.send_command(f"RETR {msg_number}")
        if response and "+OK" in response:
            message_data = self.pop3_client.receive_multiline()
            if message_data:
                self.pop3_client.decode_message(message_data)

    def delete_message(self, msg_number):
        if not self.pop3_client or not self.check_pop3_auth():
            print("POP3 клиент не настроен или не авторизован")
            return

        response = self.pop3_client.send_command(f"DELE {msg_number}")
        if response and "+OK" in response:
            self.log_message(f"Сообщение {msg_number} помечено на удаление", "ИНФО:")

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
