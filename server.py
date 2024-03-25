from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton
from PyQt5 import uic
import sys
import socket
import threading
from time import sleep
from game import Deck, Card, is_better
import requests
import json


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        uic.loadUi("server.ui", self)

        self.start_button.clicked.connect(start_server)
        self.stop_button.clicked.connect(stop_server)

        self.show()


# Start server function
def start_server():
    global server

    MainWindow.start_button.setEnabled(False)
    MainWindow.stop_button.setEnabled(True)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", HOST_PORT))
    server.listen()  # server is listening for client connection

    thread = threading.Thread(target=accept_clients, args=(server,))
    thread.start()

    MainWindow.address_label.setText("Address: " + HOST_ADDR)
    MainWindow.port_label.setText("Port: " + str(HOST_PORT))


# Stop server function
def stop_server():
    global server, clients, clients_names, player_data
    
    for connection in clients:
        connection.close()
    clients = []
    clients_names = []

    server.close()
    update_clients(clients_names)

    player_data = []
    MainWindow.address_label.setText("Address: X.X.X.X")
    MainWindow.port_label.setText("Port: XXXX")

    MainWindow.start_button.setEnabled(True)
    MainWindow.stop_button.setEnabled(False)


# Accept clients to server
def accept_clients(the_server):
    while True:
        if len(clients) < num_players:
            client, addr = the_server.accept()
            clients.append(client)

            # start message thread to not clog the gui thread
            thread = threading.Thread(target=communicate, args=(client,))
            thread.start()


# Receive and send messages with current client
def communicate(client):
    global server, clients, pot, caller, current_winner, winning_cards, first_player, starting_cards, potential_points, points_scored

    # send welcome message to client
    name = client.recv(4096).decode('utf-8')
    
    client.send(("welcome-" + str(len(clients)-1) + "-" + "-".join(clients_names)).encode('utf-8')) # e.g., welcome-2-Andy-Michael

    for i, c in enumerate(clients):
        if c != client:
            c.send(("joined-" + str(i) + "-" + str(len(clients)-1) + "-" + name).encode('utf-8')) # e.g., joined-[my_index]-[newplayer_index]-[name] 
    
    clients_names.append(name)
    update_clients(clients_names)  # update client names display

    if len(clients) == num_players:
        sleep(1)

        for c in clients[:-1]:
            c.send("start-wait".encode('utf-8'))
        client.send("start-play".encode('utf-8'))

    while True:
        message = client.recv(4096).decode('utf-8')
        if not message:
            break

        if message == "draw":
            card = deck.draw()
            client.send(("draw-" + card.get_rank() + "-" + card.get_suit()).encode('utf-8')) # e.g., "draw-THREE-CLUBS"
            #client.send(pickle.dumps(card))
            
            if deck.isempty():
                for c in clients:
                    if c == caller:
                        c.send(("pot-" + str(len(pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in pot])).encode('utf-8'))
                    else:
                        c.send("dealover".encode('utf-8'))
            else:
                clients[(clients.index(client) + 1) % len(clients)].send("yourturn".encode('utf-8'))
        
        elif message.startswith("call"): # e.g., call-JOKER-RED-TEN-HEARTS
            caller = client
            for c in clients:
                if c != client: # send non-callers the info
                    c.send(("call-" + name + "-" + "-".join(message.split("-")[1:])).encode('utf-8'))
                elif deck.isempty(): # if deck empty, send the pot to the caller
                    c.send(("pot-" + str(len(pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in pot])).encode('utf-8'))
        
        elif message.startswith("bury"):
            message = message.split("-")
            pot = [Card(message[i], message[i+1]) for i in range(2, len(message), 2)]
            for c in clients:
                if c == client:
                    c.send("play-yourturn".encode('utf-8'))
                else:
                    c.send("play".encode('utf-8'))
        
        elif message.startswith("play"): # e.g., play-TEN-HEARTS-TEN-HEARTS
            message = message.split("-")
            cards = [Card(message[i], message[i+1]) for i in range(1, len(message), 2)]

            for card in cards:
                potential_points += card.get_points()

            if not starting_cards:
                first_player = client
                starting_cards = [card for card in cards]

            if is_better(winning_cards, cards):
                current_winner = client
                winning_cards = [card for card in cards]

            for c in clients:
                if c != client:
                    c.send(("put-" + name + "-" + "-".join(message[1:]) +
                           ("-STARTING-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in starting_cards])) + 
                           ("-GO" if c == clients[(clients.index(client) + 1) % len(clients)] else "")).encode('utf-8'))
            
            if first_player == clients[(clients.index(client) + 1) % len(clients)]: # made it all around
                for c in clients:
                    if c == current_winner:
                        c.send(("winner-You" + ("-POINTS" if potential_points > 0 else "")).encode('utf-8'))
                    else:
                        c.send(("winner-" + clients_names[(clients.index(current_winner))] + ("-POINTS" if potential_points > 0 else "")).encode('utf-8'))
                first_player = None
                starting_cards = []
                winning_cards = []
        
        elif message.startswith("score"): # e.g, score-True or score-False
            if message.split("-")[1] == "True":
                points_scored += potential_points

            if points_scored >= 80:
                for c in clients:
                    c.send("gameover-attack".encode('utf-8'))
            else:
                for c in clients:
                    if c == current_winner:
                        c.send((message + "-" + str(points_scored) + "-GO").encode('utf-8'))
                    else:
                        c.send((message + "-" + str(points_scored)).encode('utf-8'))

            current_winner = None
            potential_points = 0

            

    clients_names.remove(client)
    clients.remove(client)
    client.close()
    update_clients(clients_names)


# Update the client list display
def update_clients(names):
    MainWindow.clients_list.setText("\n".join(names))



app = QApplication(sys.argv)
MainWindow = UI()
MainWindow.setWindowTitle("Tractor Server")

server = None
with open("secrets.json", "r") as secrets:
    HOST_ADDR, HOST_PORT = json.load(secrets).values()
clients = []
caller = None
clients_names = []
player_data = []
num_players = 4
deck = Deck(num_players // 2)
deck.shuffle()
pot = []
for _ in range(2 * num_players):
    pot.append(deck.draw())
first_player = None
current_winner = None
starting_cards = []
winning_cards = []
potential_points = 0
points_scored = 0

sys.exit(app.exec())