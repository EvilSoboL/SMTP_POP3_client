import socket
import ssl
import datetime


class SMTPClient:
    def __init__(self):
        self.socket = None
        self.log_file = f"smtp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log_message(self, message, direction=''):
        """Записывает сообщение в лог-файл"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} {direction} {message}\n")
        print(f"{direction} {message}")

    def receive_response(self):
        """Получает ответ от сервера"""
        try:
            response = self.socket.recv(1024).decode()
            self.log_message(response, '<--')
            return response
        except Exception as e:
            self.log_message(f"Ошибка при получении ответа: {str(e)}")
            return None

    def send_command(self, command):
        """Отправляет команду серверу"""
        try:
            self.log_message(command, '-->')
            self.socket.send(f"{command}\r\n".encode())
            return self.receive_response()
        except Exception as e:
            self.log_message(f"Ошибка при отправке команды: {str(e)}")
            return None

    def connect(self, server, port):
        """Устанавливает соединение с SMTP-сервером"""
        try:
            # Создаем обычный сокет
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)  # Устанавливаем таймаут
            self.socket.connect((server, port))

            # Получаем приветственное сообщение
            initial_response = self.receive_response()

            if port == 587:  # Для STARTTLS
                # Отправляем EHLO
                self.send_command(f"EHLO {socket.gethostname()}")

                # Отправляем STARTTLS
                response = self.send_command("STARTTLS")
                if response and response.startswith('220'):
                    # Создаем SSL контекст
                    context = ssl.create_default_context()
                    # Оборачиваем существующий сокет в SSL
                    self.socket = context.wrap_socket(self.socket, server_hostname=server)
                    # После STARTTLS нужно снова отправить EHLO
                    self.send_command(f"EHLO {socket.gethostname()}")
                else:
                    raise Exception("STARTTLS не поддерживается сервером")

            print("\nСоединение установлено. Теперь вы можете вводить SMTP команды.")
            print("Для завершения работы введите 'QUIT'\n")
            return True
        except Exception as e:
            self.log_message(f"Ошибка подключения: {str(e)}")
            return False

    def close(self):
        """Закрывает соединение"""
        if self.socket:
            self.socket.close()


def main():
    print("Добро пожаловать в SMTP клиент!")
    print("\nПримеры SMTP команд:")
    print("AUTH LOGIN")  # Добавлена команда аутентификации
    print("MAIL FROM:<sender@example.com>")
    print("RCPT TO:<recipient@example.com>")
    print("DATA")
    print("QUIT\n")

    # Запрашиваем параметры подключения
    server = input("Введите адрес SMTP-сервера: ")
    port = int(input("Введите порт: "))

    client = SMTPClient()

    if not client.connect(server, port):
        print("Не удалось подключиться к серверу")
        return

    # Основной цикл работы с командами
    while True:
        command = input("\nВведите SMTP команду: ")

        if not command:
            continue

        if command.upper() == 'DATA':
            # Особая обработка команды DATA
            client.send_command(command)
            print("\nВведите текст сообщения.")
            print("Для завершения введите точку (.) в отдельной строке.\n")

            message_lines = []
            while True:
                line = input()
                message_lines.append(line)
                if line == '.':
                    break

            message = '\r\n'.join(message_lines)
            client.send_command(message)

        elif command.upper() == 'QUIT':
            client.send_command(command)
            break
        else:
            client.send_command(command)

    client.close()
    print("\nСоединение закрыто. Сессия сохранена в файле", client.log_file)


if __name__ == "__main__":
    main()
