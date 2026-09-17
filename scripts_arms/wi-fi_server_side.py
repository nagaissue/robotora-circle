import socket

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("接続待ち...")

conn, addr = server.accept()
print("接続:", addr)

cnt = 0
send_data = (b"Hello PLC\n", b"data1\n", b"data2\n", b"data3\n")
while True:
    data = conn.recv(1024)

    if not data:
        break

    print("PLC:", data.decode().strip())

    conn.sendall(send_data[cnt % len(send_data)])
    cnt += 1

conn.close()
server.close()