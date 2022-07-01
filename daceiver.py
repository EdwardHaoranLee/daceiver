from flask import Flask, request
import socket
from collections import deque
from typing import Any, List
from abc import ABC, abstractmethod
from multiprocessing import Process


class DataQueue(deque):
    def __init__(self, maxlen: int = None):
        super().__init__(maxlen=maxlen)


class IDataReceiver(ABC):
    port: int
    maxlen: int
    queue: DataQueue

    def __init__(self, maxlen: int = None, port: int = 8001):
        self.port = port

        self.maxlen = maxlen
        self.queue = DataQueue(self.maxlen)

    @abstractmethod
    def start(self) -> None: pass

    @abstractmethod
    def end(self) -> None: pass

    def add(self, data: Any) -> Any:
        self.queue.append(data)
        return data

    def peak_all(self) -> List[Any]:
        return list(self.queue)

    def peak_right(self) -> Any:
        return self.queue[-1] if len(self.queue) > 0 else None

    def peak_left(self) -> Any:
        return self.queue[0] if len(self.queue) > 0 else None

    def clear(self) -> bool:
        self.queue.clear()
        return len(self.queue) == 0

    def pop_right(self) -> Any:
        return self.queue.pop() if len(self.queue) > 0 else None

    def pop_left(self) -> Any:
        return self.queue.popleft() if len(self.queue) > 0 else None

    def len(self) -> int:
        return len(self.queue)


class HTTPReceiver(IDataReceiver, ABC):
    app: Flask
    server: Process
    successful_msg: str = 'Successfully Added!'

    def __init__(self, maxlen: int = None, port: int = 8001, successful_msg: str = None, method: str = 'POST'):
        super().__init__(maxlen, port)
        self.app = Flask(__name__)
        self.app.add_url_rule('/', view_func=self.__httpcall, methods=[method])

        self.successful_msg = successful_msg if successful_msg is not None else self.successful_msg

    def __httpcall(self) -> Any:
        self.add(request.data)
        return self.successful_msg

    def start(self) -> None:
        self.server = Process(target=self.app.run, args=('0.0.0.0', self.port))
        self.server.start()

    def end(self) -> None:
        self.server.terminate()
        self.server.join()


class SocketReceiver(IDataReceiver, ABC):
    socket: socket.socket
    end_character: str
    block_size: int

    def __init__(self, maxlen: int = None, port: int = 8001, protocol: str = 'UDP', end_character: str = '\03',
                 block_size: int = 1024):
        super().__init__(maxlen, port)
        self.end_character = end_character
        self.block_size = block_size
        if protocol == 'UDP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif protocol == 'TCP':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self) -> None:
        self.socket.bind(('', self.port))
        self.socket.listen()

        msg = b''

        while True:
            data, _ = self.socket.recvfrom(self.block_size)



if __name__ == '__main__':
    extractor = DataExtractor(maxlen=2)
    extractor.run()
