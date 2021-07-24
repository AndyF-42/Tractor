from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt5 import uic
import sys
import socket
import threading
import pickle
from time import sleep
from game import Deck


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        uic.loadUi("server.ui", self)



        self.startButton = self.findChild(QPushButton, "startButton")
        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.startButton.clicked.connect(startServer)
        self.stopButton.clicked.connect(stopServer)

        self.show()


# Start server function
def startServer():
    global server

    MainWindow.startButton.setEnabled(False)
    MainWindow.stopButton.setEnabled(True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST_ADDR, HOST_PORT))
    server.listen()  # server is listening for client connection

    thread = threading.Thread(target=acceptClients, args=(server,))
    thread.start()

    MainWindow.addressLabel.setText("Address: " + HOST_ADDR)
    MainWindow.portLabel.setText("Port: " + str(HOST_PORT))


# Stop server function
def stopServer():
    global server, clients, clientsNames, player_data
    
    for i, client_connection in enumerate(clients):
        del clientsNames[i]
        del clients[i]
        client_connection.close()

    # server.shutdown(socket.SHUT_RDWR)
    server.close()
    updateClients(clientsNames)

    # clients = []
    # clientsNames = []
    player_data = []
    MainWindow.address_label.setText("Address: X.X.X.X")
    MainWindow.port_label.setText("Port: XXXX")

    MainWindow.startButton.setEnabled(True)
    MainWindow.stopButton.setEnabled(False)


# Accept clients to server
def acceptClients(the_server):
    while True:
        if len(clients) < num_players:
            client, addr = the_server.accept()
            clients.append(client)

            # start message thread to not clog the gui thread
            thread = threading.Thread(target=communicate, args=(client,))
            thread.start()


# Receive and send messages with current client
def communicate(client):
    global server, clients

    # send welcome message to client
    name = client.recv(4096).decode('utf-8')

    client.send(("welcome" + str(len(clients))).encode('utf-8'))
    
    clientsNames.append(name)
    updateClients(clientsNames)  # update client names display

    if len(clients) == num_players:
        sleep(1)

        for c in clients[:-1]:
            c.send("start-wait".encode('utf-8'))
        client.send("start-play".encode('utf-8'))

    while True:
        message = client.recv(4096).decode('utf-8')
        print(message)
        if not message:
            break

        if message == "draw":
            card = deck.draw()
            client.send(("draw-" + card.getRank() + "-" + card.getSuit()).encode('utf-8')) # e.g., "add-THREE-CLUBS"
            #client.send(pickle.dumps(card))
            print(clientsNames[(clients.index(client) + 1) % len(clients)])
            clients[(clients.index(client) + 1) % len(clients)].send("yourturn".encode('utf-8'))

            

    clientsNames.remove(client)
    clients.remove(client)
    client.close()
    updateClients(clientsNames)


# Update the client list display
def updateClients(names):
    MainWindow.clientsList.setText("\n".join(names))



app = QApplication(sys.argv)
MainWindow = UI()
MainWindow.setWindowTitle("Tractor Server")

server = None
HOST_ADDR = socket.gethostbyname(socket.gethostname())
HOST_PORT = 5050
clients = []
clientsNames = []
player_data = []
num_players = 2

deck = Deck(2)
deck.shuffle()

pot = []

for _ in range(2 * num_players):
    pot.append(deck.draw())

sys.exit(app.exec())