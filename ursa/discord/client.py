from PyQt5.QtCore import QObject, pyqtSignal
from discord import Client, Message, Intents


class ClientEventProxy(QObject):
    on_connect = pyqtSignal()
    on_ready = pyqtSignal()
    on_message = pyqtSignal(Message)
    on_disconnect = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)


class UrsaClient(Client):
    event_proxy: ClientEventProxy

    def __init__(self, **options):
        super().__init__(**options, intents=Intents.default() | Intents(message_content=True))
        self.event_proxy = ClientEventProxy()

    async def on_connect(self):
        print("DEBUG -> on_connect")
        self.event_proxy.on_connect.emit()

    async def on_ready(self):
        print("DEBUG -> on_ready")
        self.event_proxy.on_ready.emit()

    async def on_message(self, message: Message):
        print(f"DEBUG -> on_message: {message.content}")
        self.event_proxy.on_message.emit(message)

    async def on_disconnect(self):
        print("DEBUG -> on_disconnect")
        self.event_proxy.on_disconnect.emit()
