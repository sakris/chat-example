from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

chatLog = []  # для хранения истории чата


class Client(LineOnlyReceiver):
    ip: str = None
    login: str = None
    factory: 'Chat'

    def __init__(self, factory):
        """
        Инициализация фабрики клиента
        :param factory:
        """
        self.factory = factory

    def connectionMade(self):
        """
        Обработчик подключения нового клиента
        """
        self.ip = self.transport.getHost().host
        self.factory.clients.append(self)

        print(f"Client connected: {self.ip}")

        self.transport.write(f"{self.getTime()} Welcome to the chat v0.1\n".encode())

    def dataReceived(self, data: bytes):
        """
        Обработчик нового сообщения от клиента
        :param data:
        """
        message = data.decode().replace('\n', '')

        if self.login is not None:
            server_message = f"{self.login}: {message}"
            self.factory.notify_all_users(server_message)
            chatLog.append(server_message)
            print(server_message)
        else:
            if message.startswith("login:"):
                _login = message.replace("login:", "")  # заносим в переменную введенный логин

                if not self.factory.check_login(_login):  # проверяем входит ли логин в множество логинов
                    self.factory.logins.add(_login)
                    self.login = _login
                    # new user connected
                    notification = f"New user connected: {self.login}"
                    print(notification)
                    self.factory.notify_all_users(notification)
                                        
                    # отправляем историю сообщений
                    self.sendLine("History chat:".encode())
                    for msg in chatLog:
                        self.sendLine(msg.encode())
                    self.sendLine("*****".encode())
                else:
                    print("login taken")
                    self.sendLine("login taken".encode())
                    self.transport.abortConnection()  # обрываем сессию                             
                
            else:
                print("Error: Invalid client login")

    def connectionLost(self, reason=None):
        """
        Обработчик отключения клиента
        :param reason:
        """
        self.factory.clients.remove(self)

        if self.login in self.factory.logins:
            self.factory.logins.remove(self.login)
        print(f"Client disconnected: {self.ip}")
    # Time format    
    def getTime(self):
        return '({:%Y/%m/%d %H:%M:%S})'.format(datetime.datetime.now())
     


class Chat(Factory):
    clients: list

    def __init__(self):
        """
        Инициализация сервера
        """
        self.clients = []
        self.logins = set()  # для хранения списка логинов
        print("*" * 10, "\nStart server \nCompleted [OK]")

    def startFactory(self):
        """
        Запуск процесса ожидания новых клиентов
        :return:
        """
        print("\n\nStart listening for the clients...")

    def buildProtocol(self, addr):
        """
        Инициализация нового клиента
        :param addr:
        :return:
        """
        return Client(self)

    def notify_all_users(self, data: str):
        """
        Отправка сообщений всем текущим пользователям
        :param data:
        :return:
        """
        for user in self.clients:
            user.transport.write(f"{data}\n".encode())

    def check_login(self, login: str):
        """
        Проверка на существование логина
        :param login:
        :return:
        """
        return login in self.logins


if __name__ == '__main__':
    reactor.listenTCP(7410, Chat())
    reactor.run()
