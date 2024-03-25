import sys
import socket
import threading
from time import sleep
from game import Deck, Card, is_better
import json



class TractorServer():
    caller = None
    player_data = []
    first_player = None
    current_winner = None
    starting_cards = []
    winning_cards = []
    potential_points = 0
    points_scored = 0

    def __init__(self, num_players):
        self.num_players = num_players
        self.deck = Deck(num_players // 2)
        self.deck.shuffle()
        self.pot = [self.deck.draw() for _ in range(2 * num_players)]
        
        with open("secrets.json", "r") as secrets:
            self.address, self.port = json.load(secrets).values()
    
    # run the server
    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.address, self.port))
        self.server.listen()

        print(f"Server listening on address {self.address} and port {self.port}")
        
        self.clients = []
        self.clients_names = []
        while True:
            if len(self.clients) < self.num_players:
                client, addr = self.server.accept()
                self.clients.append(client)

                thread = threading.Thread(target=self.communicate, args=(client,))
                thread.start() 

    # receive and send messages with a single client
    def communicate(self, client):
        name = client.recv(4096).decode('utf-8') # start with client's name
        
        client.send(("welcome-" + str(len(self.clients)-1) + "-" + "-".join(self.clients_names)).encode('utf-8')) # e.g., welcome-2-Andy-Michael

        for i, c in enumerate(self.clients):
            if c != client:
                c.send(("joined-" + str(i) + "-" + str(len(self.clients)-1) + "-" + name).encode('utf-8')) # e.g., joined-[my_index]-[newplayer_index]-[name] 
        
        self.clients_names.append(name)
        print(f"{name} joined!")

        if len(self.clients) == self.num_players:
            sleep(1)

            for c in self.clients[:-1]:
                c.send("start-wait".encode('utf-8'))
            client.send("start-play".encode('utf-8'))

        while True:
            message = client.recv(4096).decode('utf-8')
            if not message:
                break

            if message == "draw":
                card = self.deck.draw()
                client.send(("draw-" + card.get_rank() + "-" + card.get_suit()).encode('utf-8')) # e.g., "draw-THREE-CLUBS"
                
                if self.deck.isempty():
                    for c in self.clients:
                        if c == self.caller:
                            c.send(("pot-" + str(len(self.pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in self.pot])).encode('utf-8'))
                        else:
                            c.send("dealover".encode('utf-8'))
                else:
                    self.clients[(self.clients.index(client) + 1) % len(self.clients)].send("yourturn".encode('utf-8'))
            
            elif message.startswith("call"): # e.g., call-JOKER-RED-TEN-HEARTS
                self.caller = client
                for c in self.clients:
                    if c != client: # send non-callers the info
                        c.send(("call-" + name + "-" + "-".join(message.split("-")[1:])).encode('utf-8'))
                    elif self.deck.isempty(): # if deck empty, send the pot to the caller
                        c.send(("pot-" + str(len(self.pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in self.pot])).encode('utf-8'))
            
            elif message.startswith("bury"):
                message = message.split("-")
                self.pot = [Card(message[i], message[i+1]) for i in range(2, len(message), 2)]
                for c in self.clients:
                    if c == client:
                        c.send("play-yourturn".encode('utf-8'))
                    else:
                        c.send("play".encode('utf-8'))
            
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
                        c.send(("put-" + name + "-" + "-".join(message[1:]) +
                            ("-STARTING-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in self.starting_cards])) + 
                            ("-GO" if c == self.clients[(self.clients.index(client) + 1) % len(self.clients)] else "")).encode('utf-8'))
                
                if self.first_player == self.clients[(self.clients.index(client) + 1) % len(self.clients)]: # made it all around
                    for c in self.clients:
                        if c == self.current_winner:
                            c.send(("winner-You" + ("-POINTS" if self.potential_points > 0 else "")).encode('utf-8'))
                        else:
                            c.send(("winner-" + self.clients_names[(self.clients.index(self.current_winner))] + ("-POINTS" if self.potential_points > 0 else "")).encode('utf-8'))
                    self.first_player = None
                    self.starting_cards = []
                    self.winning_cards = []
            
            elif message.startswith("score"): # e.g, score-True or score-False
                if message.split("-")[1] == "True":
                    self.points_scored += self.potential_points

                if self.points_scored >= 80:
                    for c in self.clients:
                        c.send("gameover-attack".encode('utf-8'))
                else:
                    for c in self.clients:
                        if c == self.current_winner:
                            c.send((message + "-" + str(self.points_scored) + "-GO").encode('utf-8'))
                        else:
                            c.send((message + "-" + str(self.points_scored)).encode('utf-8'))

                self.current_winner = None
                self.potential_points = 0

        self.clients_names.remove(client)
        self.clients.remove(client)
        client.close()


if __name__ == "__main__":
    server = TractorServer(4)
    server.run()