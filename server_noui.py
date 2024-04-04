from game import Deck, Card, is_better

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QTcpServer, QHostAddress

import sys
import json



class TractorServer(QTcpServer):
    caller = None
    player_data = []
    first_player = None
    current_winner = None
    starting_cards = []
    winning_cards = []
    potential_points = 0
    points_scored = 0
    clients = {}
    
    def __init__(self, num_players: int):
        super().__init__()

        self.num_players = num_players
        self.deck = Deck(num_players // 2)
        self.deck.shuffle()
        self.pot = [self.deck.draw() for _ in range(2 * num_players)]
        self.timer = QTimer()
        
        with open("secrets.json", "r") as secrets:
            self.address, self.port = json.load(secrets).values()

        self.newConnection.connect(self.client_connected)
        self.listen(QHostAddress(self.address), self.port)
        print(f"Server listening on address {self.address} and port {self.port}")

    def client_connected(self):
        if len(self.clients) < self.num_players:
            client = self.nextPendingConnection()
            self.clients[client] = ""
            client.readyRead.connect(self.read_data)
            print("Client connected")

    def read_data(self):
        client = self.sender()
        message = client.readAll().data().decode('utf-8')
        print(f"message: {message}")

        if message.startswith("name"):
            name = message.split("-")[1]

            welcome_msg = "welcome-" + str(len(self.clients)-1)
            for n in self.clients.values():
                if n: welcome_msg += ("-" + n)
            client.write(welcome_msg.encode('utf-8')) # e.g., welcome-2-Andy-Michael

            for i, c in enumerate(self.clients):
                if c != client:
                    c.write(("joined-" + str(i) + "-" + str(len(self.clients)-1) + "-" + name).encode('utf-8')) # e.g., joined-[my_index]-[newplayer_index]-[name] 
            
            self.clients[client] = name
            print(f"{name} joined!")

            if len(self.clients) == self.num_players:
                self.timer.singleShot(500, self.start_play)
                
        elif message == "draw":
            card = self.deck.draw()
            client.write(("draw-" + card.get_rank() + "-" + card.get_suit()).encode('utf-8')) # e.g., "draw-THREE-CLUBS"
            
            self.timer.singleShot(500, lambda: self.next_turn(client))
        
        elif message.startswith("call"): # e.g., call-JOKER-RED-TEN-HEARTS
            self.caller = client
            for c in self.clients:
                if c != client: # send non-callers the info
                    c.write(("call-" + self.clients[client] + "-" + "-".join(message.split("-")[1:])).encode('utf-8'))
                elif self.deck.isempty(): # if deck empty, send the pot to the caller
                    c.write(("pot-" + str(len(self.pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in self.pot])).encode('utf-8'))
            
        elif message.startswith("bury"):
            message = message.split("-")
            self.pot = [Card(message[i], message[i+1]) for i in range(2, len(message), 2)]
            for c in self.clients:
                if c == client:
                    c.write("play-yourturn".encode('utf-8'))
                else:
                    c.write("play".encode('utf-8'))
        
        elif message.startswith("play"): # e.g., play-TEN-HEARTS-TEN-HEARTS
            message = message.split("-")
            cards = [Card(message[i], message[i+1]) for i in range(1, len(message), 2)]

            for card in cards:
                self.potential_points += card.get_points()

            if not self.starting_cards:
                self.first_player = client
                self.starting_cards = [card for card in cards]

            if is_better(self.winning_cards, cards):
                self.current_winner = client
                self.winning_cards = [card for card in cards]

            for c in self.clients:
                if c != client:
                    c.write(("put-" + name + "-" + "-".join(message[1:]) +
                        ("-STARTING-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in self.starting_cards])) + 
                        ("-GO" if c == list(self.clients)[(list(self.clients).index(client) + 1) % len(self.clients)] else "")).encode('utf-8'))
            
            if self.first_player == list(self.clients)[(list(self.clients).index(client) + 1) % len(self.clients)]: # made it all around
                for c in self.clients:
                    if c == self.current_winner:
                        c.write(("winner-You" + ("-POINTS" if self.potential_points > 0 else "")).encode('utf-8'))
                    else:
                        c.write(("winner-" + self.clients[self.current_winner] + ("-POINTS" if self.potential_points > 0 else "")).encode('utf-8'))
                self.first_player = None
                self.starting_cards = []
                self.winning_cards = []
            
        elif message.startswith("score"): # e.g, score-True or score-False
            if message.split("-")[1] == "True":
                self.points_scored += self.potential_points

            if self.points_scored >= 80:
                for c in self.clients:
                    c.write("gameover-attack".encode('utf-8'))
            else:
                for c in self.clients:
                    if c == self.current_winner:
                        c.write((message + "-" + str(self.points_scored) + "-GO").encode('utf-8'))
                    else:
                        c.write((message + "-" + str(self.points_scored)).encode('utf-8'))

            self.current_winner = None
            self.potential_points = 0
         
    # --- TIMED FUNCTIONS --- #   
    def start_play(self):
        print("start_play!")
        for c in list(self.clients)[:-1]:
            c.write("start-wait".encode('utf-8'))
        list(self.clients)[-1].write("start-play".encode('utf-8'))
        
    def next_turn(self, client):
        if self.deck.isempty():
            for c in self.clients:
                if c == self.caller:
                    c.write(("pot-" + str(len(self.pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in self.pot])).encode('utf-8'))
                else:
                    c.write("dealover".encode('utf-8'))
        else:
            list(self.clients)[(list(self.clients).index(client) + 1) % len(self.clients)].write("yourturn".encode('utf-8'))

def start_play():
    print("wtf")

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    server = TractorServer(4)
    sys.exit(app.exec_())