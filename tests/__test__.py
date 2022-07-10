import time
import requests
import socket


times = []


def __test_HTTPReceiver(rps: int = 100, total: int = 600):
    start = time.time()
    for i in range(total):
        end = time.time()
        requests.post('http://localhost:8001', str(i) * 1000000)
        time.sleep(1 / rps)
        if i % rps == 0:
            print(str(end - start) + "s")
            times.append(end-start)
            start = end


def __test_SocketReceiver(rps: int = 100, total: int = 600):
    s = socket.socket()
    s.bind(('', 8001))
    s.listen()

    c, addr = s.accept()
    start = time.time()
    for i in range(total):
        end = time.time()
        c.send(bytes(str(i) * 1000000, "utf-8") + b'\03')
        time.sleep(1 / rps)
        if i % rps == 0:
            print(str(end - start) + "s")
            times.append(end - start)
            start = end
    c.close()


if __name__ == '__main__':
    times = []
    __test_HTTPReceiver()
    print(sum(times)/len(times))

