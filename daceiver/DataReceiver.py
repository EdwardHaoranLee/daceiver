import socket
import threading
from abc import ABC, abstractmethod
from collections import deque
from threading import Thread
from typing import Any, List

from flask import Flask, request


class DataQueue(deque):
    def __init__(self, maxlen: int = None):
        super().__init__(maxlen=maxlen)

    def __str__(self):
        return super(DataQueue, self).__str__()


class IDataReceiver(ABC):
    port: int
    maxlen: int
    queue: DataQueue

    lock: threading.Lock

    def __init__(self, maxlen: int = None, port: int = 8001):
        self.port = port

        self.maxlen = maxlen
        self.queue = DataQueue(self.maxlen)

        self.lock = threading.Lock()

    @abstractmethod
    def start(self) -> None: pass

    @abstractmethod
    def stop(self) -> None: pass

    def add(self, data: Any) -> Any:
        self.lock.acquire()
        self.queue.append(data)
        self.lock.release()
        return data

    def peak_all(self) -> List[Any]:
        self.lock.acquire()
        result = list(self.queue)
        self.lock.release()
        return result

    def peak_right(self) -> Any:
        self.lock.acquire()
        result = self.queue[-1] if len(self.queue) > 0 else None
        self.lock.release()
        return result

    def peak_left(self) -> Any:
        self.lock.acquire()
        result = self.queue[0] if len(self.queue) > 0 else None
        self.lock.release()
        return result

    def clear(self) -> bool:
        self.lock.acquire()
        self.queue.clear()
        is_success = len(self.queue) == 0
        self.lock.release()
        return is_success

    def pop_right(self) -> Any:
        self.lock.acquire()
        result = self.queue.pop() if len(self.queue) > 0 else None
        self.lock.release()
        return result

    def pop_left(self) -> Any:
        self.lock.acquire()
        result = self.queue.popleft() if len(self.queue) > 0 else None
        self.lock.release()
        return result

    def __len__(self) -> int:
        self.lock.acquire()
        length = len(self.queue)
        self.lock.release()
        return length


class HTTPReceiver(IDataReceiver, ABC):
    app: Flask
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
        self.app.run('0.0.0.0', self.port)


class SocketReceiver(IDataReceiver, ABC):
    socket: socket.socket
    end_character: bytes
    block_size: int

    is_running: bool
    is_send_confirmation: bool
    confirmation_msg: bytes
    socket_thread: Thread

    def __init__(self, maxlen: int = None, port: int = 8001, end_character: bytes = b'\03', block_size: int = 4096,
                 is_send_confirmation: bool = False, confirmation_msg: bytes = b''):
        super().__init__(maxlen, port)
        self.end_character = end_character
        self.block_size = block_size
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.is_running = False
        self.is_send_confirmation = is_send_confirmation
        self.confirmation_msg = confirmation_msg

    def start(self) -> None:
        self.is_running = True
        self.socket.bind(('127.0.0.1', self.port))
        self.socket.listen(5)

        print('Waiting for socket client to connect...')
        conn, addr = self.socket.accept()

        print('Socket client from ' + str(addr) + ' is connected on port: ' + str(self.port))
        self.socket_thread = Thread(target=self.__start_socket_thread, args=(conn,))
        self.socket_thread.start()

    def stop(self) -> None:
        self.is_running = False
        self.socket_thread.join()

    def __start_socket_thread(self, conn: socket) -> None:
        msg = b''

        while self.is_running:
            data = conn.recv(self.block_size)
            end_index = data.find(self.end_character)
            if end_index != -1:
                msg += data[:end_index]
                self.add(msg)
                msg = data[end_index + len(self.end_character):]
                if self.is_send_confirmation:
                    conn.send(self.confirmation_msg)
            else:
                msg += data

        conn.close()


if __name__ == '__main__':
    receiver = SocketReceiver()
