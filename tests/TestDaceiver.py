import random
import socket
import time
import unittest
import warnings
from threading import Thread

from daceiver import SocketReceiver


class TestSocketReceiverCommunication(unittest.TestCase):
    receiver = None
    sender = None
    receiver_thread = None

    host = '127.0.0.1'
    port_poll = set()

    end_char = b'\03'
    confirmation_msg = b'Received'

    def setUp(self) -> None:
        warnings.simplefilter("ignore", ResourceWarning)

        port = random.randint(8000, 9000)
        while port in self.port_poll:
            port = random.randint(8000, 9000)
        self.receiver = SocketReceiver(port=port, end_character=self.end_char, is_send_confirmation=True,
                                       confirmation_msg=self.confirmation_msg)
        self.receiver_thread = Thread(target=self.receiver.start)
        self.receiver_thread.start()

        self.sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sender.connect((self.host, port))
        self.assertEqual(len(self.receiver), 0)
        self.port_poll.add(port)

    def tearDown(self) -> None:
        self.sender.close()
        self.receiver.stop()

    def receive_confirmation(self, conn: socket.socket) -> bool:
        data = conn.recv(1024)
        return data == self.confirmation_msg

    def test_add_small_data_one_time(self) -> None:
        msg = b'hello world' + self.end_char
        self.sender.send(msg)
        if self.receive_confirmation(self.sender):
            self.assertEqual(self.receiver.peak_all()[0], msg[:-1])
        else:
            raise IOError()

        self.sender.close()
        self.receiver.stop()

    def test_add_small_data_two_time(self) -> None:
        msg = b'hello' + self.end_char
        self.sender.send(msg)
        if self.receive_confirmation(self.sender):
            self.assertEqual(self.receiver.peak_all()[0], msg[:-1])
        else:
            raise IOError()

        msg = b'hello there' + self.end_char
        self.sender.send(msg)
        if self.receive_confirmation(self.sender):
            self.assertEqual(self.receiver.peak_all()[1], msg[:-1])
        else:
            raise IOError()

    def test_performance_60rps_for_10secs(self) -> None:
        time.sleep(1)
        pass

    def test_performance_100rps_for_10secs(self) -> None:
        time.sleep(1)
        pass

    def test_performance_144rps_for_10secs(self) -> None:
        time.sleep(1)
        pass
