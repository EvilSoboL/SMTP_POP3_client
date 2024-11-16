import socket
import ssl
import sys
from datetime import datetime
import re
import base64
import quopri
import email
from email.header import decode_header
from email.parser import Parser


class POP3Client:
    def __init__(self, server, port, use_ssl=True):
        self.server = server
        self.port = port
        self.socket = None
        self.connected = False
        self.use_ssl = use_ssl
        self.log_file = f"pop3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log_message(self, message, direction=""):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {direction} {message}\n")
        print(f"{direction} {message}")

    def connect(self):
        try:
            plain_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.use_ssl:
                context = ssl.create_default_context()
                self.socket = context.wrap_socket(plain_socket, server_hostname=self.server)
            else:
                self.socket = plain_socket

            self.socket.connect((self.server, self.port))
            response = self.socket.recv(1024).decode('utf-8')
            self.log_message(response, "SERVER:")
            self.connected = True
            return True
        except Exception as e:
            self.log_message(f"Connection error: {str(e)}", "ERROR:")
            return False

    def send_command(self, command):
        if not self.connected:
            self.log_message("Not connected to server", "ERROR:")
            return None

        try:
            self.log_message(command, "CLIENT:")
            self.socket.send(f"{command}\r\n".encode('utf-8'))
            response = self.socket.recv(1024).decode('utf-8')
            self.log_message(response, "SERVER:")
            return response
        except Exception as e:
            self.log_message(f"Error sending command: {str(e)}", "ERROR:")
            return None

    def receive_multiline(self):
        try:
            response = ""
            while True:
                line = self.socket.recv(1024).decode('utf-8', errors='replace')
                response += line
                if line.endswith('\r\n.\r\n'):
                    break
            self.log_message("Получено многострочное сообщение", "SERVER:")
            return response
        except Exception as e:
            self.log_message(f"Error receiving response: {str(e)}", "ERROR:")
            return None

    def decode_message(self, message_data):
        try:
            # Парсим email сообщение
            email_message = email.message_from_string(message_data)

            print("\n=== Заголовки сообщения ===")
            # Декодируем и выводим основные заголовки
            for header in ['From', 'To', 'Subject', 'Date']:
                if header in email_message:
                    value = email_message[header]
                    decoded_header = decode_header(value)
                    decoded_value = ''
                    for part, charset in decoded_header:
                        if isinstance(part, bytes):
                            decoded_value += part.decode(charset or 'utf-8', errors='replace')
                        else:
                            decoded_value += part
                    print(f"{header}: {decoded_value}")

            print("\n=== Содержимое сообщения ===")
            # Обрабатываем тело сообщения
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.get_payload()
                        encoding = part.get('Content-Transfer-Encoding', '')

                        if encoding.lower() == 'base64':
                            content = base64.b64decode(content).decode('utf-8', errors='replace')
                        elif encoding.lower() == 'quoted-printable':
                            content = quopri.decodestring(content).decode('utf-8', errors='replace')

                        print(content)
                        break
            else:
                content = email_message.get_payload()
                encoding = email_message.get('Content-Transfer-Encoding', '')

                if encoding.lower() == 'base64':
                    content = base64.b64decode(content).decode('utf-8', errors='replace')
                elif encoding.lower() == 'quoted-printable':
                    content = quopri.decodestring(content).decode('utf-8', errors='replace')

                print(content)

        except Exception as e:
            print(f"Ошибка при декодировании сообщения: {str(e)}")

    def close(self):
        if self.socket:
            self.send_command("QUIT")
            self.socket.close()
            self.connected = False


def print_available_commands():
    print("\nДоступные команды:")
    print("USER username - ввести имя пользователя")
    print("PASS password - ввести пароль")
    print("STAT - получить статистику почтового ящика")
    print("LIST - получить список сообщений")
    print("RETR n - получить сообщение номер n")
    print("DELE n - пометить сообщение n на удаление")
    print("RSET - отменить все помеченные на удаление")
    print("NOOP - проверка соединения")
    print("QUIT - завершить сессию")
    print("HELP - показать эту справку")


def main():
    server = input("Введите адрес POP3 сервера: ")
    use_ssl = input("Использовать SSL/TLS? (y/n): ").lower() == 'y'

    if use_ssl:
        default_port = 995
    else:
        default_port = 110

    port = int(input(f"Введите порт (по умолчанию {default_port}): ") or str(default_port))

    client = POP3Client(server, port, use_ssl)

    if not client.connect():
        print("Не удалось подключиться к серверу")
        return

    print_available_commands()

    while True:
        command = input("\nВведите команду (HELP для справки): ").strip()

        if command.upper() == "HELP":
            print_available_commands()
            continue

        if command.upper() == "QUIT":
            client.close()
            break

        if command.upper().startswith(("RETR")):
            response = client.send_command(command)
            if response and "+OK" in response:
                message_data = client.receive_multiline()
                if message_data:
                    client.decode_message(message_data)
        elif command.upper().startswith("LIST"):
            response = client.send_command(command)
            if response and "+OK" in response:
                list_data = client.receive_multiline()
                print(list_data)
        else:
            client.send_command(command)


if __name__ == "__main__":
    main()
