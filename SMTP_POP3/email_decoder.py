import email
from email.header import decode_header
from email.parser import Parser
import quopri
import base64
import chardet


class EmailDecoder:
    @staticmethod
    def decode_header_value(header_value):
        """Декодирует значение заголовка письма из MIME-encoded words формата"""
        if not header_value:
            return ""

        try:
            # Декодируем MIME-encoded words
            decoded_parts = []
            for part, charset in decode_header(header_value):
                if isinstance(part, bytes):
                    if charset:
                        try:
                            decoded_parts.append(part.decode(charset))
                        except (UnicodeDecodeError, LookupError):
                            # Если указанная кодировка не работает, пытаемся определить автоматически
                            detected = chardet.detect(part)
                            if detected['encoding']:
                                try:
                                    decoded_parts.append(part.decode(detected['encoding']))
                                except UnicodeDecodeError:
                                    decoded_parts.append(part.decode('utf-8', errors='replace'))
                            else:
                                decoded_parts.append(part.decode('utf-8', errors='replace'))
                    else:
                        # Если кодировка не указана, пытаемся определить автоматически
                        detected = chardet.detect(part)
                        if detected['encoding']:
                            try:
                                decoded_parts.append(part.decode(detected['encoding']))
                            except UnicodeDecodeError:
                                decoded_parts.append(part.decode('utf-8', errors='replace'))
                        else:
                            decoded_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    decoded_parts.append(str(part))

            return ' '.join(decoded_parts)
        except Exception as e:
            print(f"Ошибка при декодировании заголовка: {str(e)}")
            return header_value

    @staticmethod
    def decode_message_content(message_data):
        """Декодирует содержимое письма"""
        try:
            # Парсим сообщение
            parser = Parser()
            email_message = parser.parsestr(message_data)

            # Получаем тело письма
            if email_message.is_multipart():
                # Для многочастных сообщений берем первую текстовую часть
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        content = part.get_payload(decode=True)
                        charset = part.get_content_charset()
                        if charset:
                            try:
                                return content.decode(charset)
                            except UnicodeDecodeError:
                                detected = chardet.detect(content)
                                if detected['encoding']:
                                    return content.decode(detected['encoding'], errors='replace')
                                return content.decode('utf-8', errors='replace')
                        else:
                            detected = chardet.detect(content)
                            if detected['encoding']:
                                return content.decode(detected['encoding'], errors='replace')
                            return content.decode('utf-8', errors='replace')
            else:
                # Для простых сообщений
                content = email_message.get_payload(decode=True)
                charset = email_message.get_content_charset()
                if charset:
                    try:
                        return content.decode(charset)
                    except UnicodeDecodeError:
                        detected = chardet.detect(content)
                        if detected['encoding']:
                            return content.decode(detected['encoding'], errors='replace')
                        return content.decode('utf-8', errors='replace')
                else:
                    detected = chardet.detect(content)
                    if detected['encoding']:
                        return content.decode(detected['encoding'], errors='replace')
                    return content.decode('utf-8', errors='replace')

        except Exception as e:
            print(f"Ошибка при декодировании содержимого: {str(e)}")
            return "Ошибка при декодировании содержимого письма"
