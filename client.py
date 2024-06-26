from game import Card, set_dominant, tractor_sorted, valid_play

from PyQt5.QtWidgets import (QMainWindow, QApplication, QPushButton, QLineEdit, QMessageBox,
                             QLabel, QWidget, QFrame, QCheckBox, QFormLayout, QHBoxLayout, QVBoxLayout, QGridLayout)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer
from PyQt5 import QtGui
from PyQt5.QtNetwork import QTcpSocket

import sys
import os
from functools import partial



class UI(QMainWindow):
    client = None
    side = "defense"
    hand = []
    selected = []
    pot = []
    dom_suit = ""
    speed_deal = False
    auto_draw = 20
    deal_over = False
    starting_cards = []
    

    def __init__(self, name=""):
        super(UI, self).__init__()
        
        self.setWindowTitle("Tractor")

        # Font
        font = QtGui.QFont()
        font.setPointSize(12)
        self.setFont(font)

        # --- Connect Layout --- #
        self.connect_frame = QFrame()
        self.setCentralWidget(self.connect_frame)
        connect_layout = QVBoxLayout(self.connect_frame)

        self.form_frame = QFrame()
        form_layout = QFormLayout(self.form_frame)
        self.ip_entry = QLineEdit("127.0.0.1" if name else "")
        self.name_entry = QLineEdit(name)
        form_layout.addRow("IP:", self.ip_entry)
        form_layout.addRow("Name:", self.name_entry)

        self.host_connect = QPushButton("Connect")

        connect_layout.addWidget(self.form_frame)
        connect_layout.addWidget(self.host_connect)
        # --- Connect Layout --- #
        
        # --- Main Layout --- #
        self.main_frame = QFrame()
        self.setCentralWidget(self.main_frame)
        main_layout = QGridLayout(self.main_frame)
        
        # 0,0
        self.info_frame = QFrame()
        info_layout = QHBoxLayout(self.info_frame)
        self.dom_img = QLabel("DomImg")
        self.dom_img.setStyleSheet("border: 1px solid black")
        self.team_img = QLabel("TeamImg")
        self.team_img.setStyleSheet("border: 1px solid black")
        self.points_label = QLabel("120/120")
        info_layout.addWidget(self.dom_img)
        info_layout.addWidget(self.team_img)
        info_layout.addWidget(self.points_label)
        
        # 0,1
        self.p2_label = QLabel("?")
        self.p2_label.setAlignment(Qt.AlignCenter)
        
        # 0,2
        self.sort_checkbox = QCheckBox("AutoSort")
        self.sort_checkbox.setChecked(True)
        
        # 1,0 
        self.p1_label = QLabel("?")
        self.p1_label.setAlignment(Qt.AlignCenter)
        
        # 1,1
        self.center_widget = QFrame()
        
        self.draw_button = QPushButton("DRAW") 
        self.call_button = QPushButton("CALL")
        self.sort_button = QPushButton() # Delete
        self.done_button = QPushButton("DONE")
        self.play_button = QPushButton("PLAY")
        self.score_button = QPushButton("SCORE")
        self.burn_button = QPushButton("BURN")
 
        self.message_label = QLabel("")
        self.message_label.setStyleSheet("background-color: rgb(185, 252, 255); border: 1px solid black")
        self.message_label.setAlignment(Qt.AlignCenter)

        # 1,2
        self.p3_label = QLabel("?")
        self.p3_label.setAlignment(Qt.AlignCenter)
        
        # 2,0 - 2,2
        self.cards_frame = QFrame()
        
        # set up main layout
        main_layout.addWidget(self.info_frame, 0, 0)
        main_layout.setAlignment(self.info_frame, Qt.AlignLeft)
        main_layout.addWidget(self.p2_label, 0, 1)
        main_layout.addWidget(self.sort_checkbox, 0, 2)
        main_layout.setAlignment(self.sort_checkbox, Qt.AlignRight)
        main_layout.addWidget(self.p1_label, 1, 0)
        main_layout.addWidget(self.center_widget, 1, 1)
        main_layout.addWidget(self.p3_label, 1, 2)
        main_layout.addWidget(self.cards_frame, 2, 0, 1, 3)

        #--- PYQT5 CODE ---#

        self.opponents = {
            "p1": (120, 200),
            "p2": (350, 100),
            "p3": (550, 200)
        }
        self.timer = QTimer()

        question = QPixmap(resource_path("images/questionMark.png")).scaledToHeight(64)
        self.dom_img.setPixmap(question)
        self.dom_img.resize(question.width(), question.height())
        self.team_img.setPixmap(question)
        self.team_img.resize(question.width(), question.height())
        
        self.host_connect.clicked.connect(self.setup)
        self.draw_button.clicked.connect(self.draw)
        self.call_button.clicked.connect(self.call)
        self.sort_button.clicked.connect(self.sort_hand)
        self.done_button.clicked.connect(self.done)
        self.play_button.clicked.connect(self.play)
        self.score_button.clicked.connect(self.score)
        self.burn_button.clicked.connect(self.burn)

        # self.p1_label.setVisible(False)
        # self.p2_label.setVisible(False)
        # self.p3_label.setVisible(False)
        # self.message_label.setVisible(False)
        # self.points_label.setVisible(False)
        # self.call_button.setVisible(False)
        # self.draw_button.setVisible(False)
        # self.done_button.setVisible(False)
        # self.sort_button.setVisible(False)
        # self.play_button.setVisible(False)
        # self.score_button.setVisible(False)
        # self.burn_button.setVisible(False)
        # self.sort_checkbox.setVisible(False)
        # self.dom_img.setVisible(False)
        # self.team_img.setVisible(False)

        self.card_map = {} # maps the card label to the Card object 
        self.hand_labels = [] 
        self.p1_cards = [QLabel() for _ in range(4)]
        self.p2_cards = [QLabel() for _ in range(4)]
        self.p3_cards = [QLabel() for _ in range(4)]
        self.my_cards = [QLabel() for _ in range(4)]
        self.pot_cards = [QLabel() for _ in range(8)]
        for c in self.pot_cards:
            c.mousePressEvent = partial(self.click, c)

        self.show()

    def click(self, label, event):
        if not label.pixmap():
            return
            
        card = self.card_map[label]
        if label in self.hand_labels:
            if card in self.selected:
                label.move(label.x(), label.y() + 50)
                self.selected.remove(card)
            else:
                label.move(label.x(), label.y() - 50)
                self.selected.append(card)
        else: # clicked on pot card
            if len(self.selected) == 1:
                self.pot[self.pot.index(card)] = self.selected[0]
                self.hand[self.hand.index(self.selected[0])] = card
                self.selected = []
                if self.sort_checkbox.isChecked():
                    self.sort_hand()
                else:
                    self.update_hand()
                
                self.show_cards(self.pot, 96, (265, 300), 30)
    
    def sort_hand(self):
        self.hand = tractor_sorted(self.hand)
        self.update_hand()

    def update_hand(self):
        # do some math to measure a good placement for hand
        self.clear_hand()
        self.selected = []
        length = len(self.hand)
        spacing = 50 - length
        x = int((665 - spacing * (length-1)) // 2)
        self.show_cards(self.hand, 192, (x, 424), spacing)

    # draw cards of height height onto the UI from Card list cards,
    # starting at tuple start (x, y), spaced by spacing
    def show_cards(self, cards, height, start, spacing):
        my_source = self.hand_labels
        if start == (120, 200): my_source = self.p1_cards
        elif start == (350, 100): my_source = self.p2_cards
        elif start == (550, 200): my_source = self.p3_cards
        elif start == (350, 300): my_source = self.my_cards
        elif start == (265, 300): my_source = self.pot_cards

        for i, card in enumerate(cards):
            label = my_source[i]
            label.move(int(start[0] + i * spacing), start[1])
            pixmap = QPixmap(resource_path("images/cards/" + card.file_name())).scaledToHeight(height)
            label.setPixmap(pixmap)
            label.resize(pixmap.width(), pixmap.height())
            label.show()
            self.card_map[label] = card

    # clear any cards people placed down
    def clear_cards(self):
        for p_cards in [self.p1_cards, self.p2_cards, self.p3_cards, self.my_cards]:
            for card in p_cards:
                if card.pixmap():
                    card.setPixmap(QPixmap())

    def clear_pot(self):
        self.done_button.setVisible(False)
        for card in self.pot_cards:
            card.setVisible(False)
    
    def clear_hand(self):
        for card in self.hand_labels:
            if card.pixmap():
                card.setPixmap(QPixmap())
    
    def check_team(self):
        for card in self.hand:
            if card.rank == "TEN" and card.suit == self.dom_suit:
                self.side = "defense"
                team = QPixmap(resource_path("images/shield.png")).scaledToHeight(64)
                self.team_img.setPixmap(team)
                self.team_img.resize(team.width(), team.height())
                return
            
        if self.deal_over:
            self.side = "attack"
            team = QPixmap(resource_path("images/sword.png")).scaledToHeight(64)
            self.team_img.setPixmap(team)
            self.team_img.resize(team.width(), team.height())
    
    def set_dom(self):
        suit_map = QPixmap(resource_path("images/" + self.dom_suit.lower() + ".png")).scaledToHeight(64)
        set_dominant(self.dom_suit) # update dom values in game.py
        if self.sort_checkbox.isChecked(): # autosort if checked since dom was updated
            self.sort_hand()
        self.dom_img.setPixmap(suit_map)
        self.dom_img.resize(suit_map.width(), suit_map.height())
        
        if self.draw_button.isEnabled():
            self.draw_button.setText("Auto Draw")
            self.draw_button.move(350, 200)
        else:
            self.draw_button.setVisible(False)
        self.speed_deal = True
        self.check_team()
    
    def draw(self):
        if self.draw_button.text() == "Auto Draw":
            self.draw_button.setVisible(False)
        self.client.write("draw".encode('utf-8'))
    
    def call(self):
        # error checking (need two cards: one ten and one joker)
        if len(self.selected) == 2 and ((self.selected[0].rank == "JOKER" and self.selected[1].rank == "TEN") or
                                        (self.selected[1].rank == "JOKER" and self.selected[0].rank == "TEN")):
            self.client.write(("call-" + self.selected[0].rank + "-" + self.selected[0].suit +
                                   "-" + self.selected[1].rank + "-" + self.selected[1].suit).encode('utf-8'))
            self.call_button.setVisible(False)
            if self.selected[0].rank == "TEN": self.dom_suit = self.selected[0].suit
            else: self.dom_suit = self.selected[1].suit
            self.set_dom()
        else:
            bad_call = QMessageBox()
            bad_call.setIcon(QMessageBox.Critical)
            bad_call.setWindowTitle("Bad Call")
            bad_call.setText("You must call with exactly one ten and one joker!")
            bad_call.exec_()
    
    def done(self):
        self.clear_pot()
        self.client.write(("bury-" + str(len(self.pot)) + "-" + "-".join([card.rank + "-" + card.suit for card in self.pot])).encode('utf-8'))

    def play(self):
        if not self.selected:
            bad_play = QMessageBox()
            bad_play.setIcon(QMessageBox.Critical)
            bad_play.setWindowTitle("Invalid Play")
            bad_play.setText("Must select 1, 2, or 4 cards to play")
            bad_play.exec_()
            return     

        self.selected = tractor_sorted(self.selected)
        valid, response = valid_play(self.starting_cards, self.selected, self.hand)
        if valid:
            self.client.write(("play-" + "-".join([card.rank + "-" + card.suit for card in self.selected])).encode('utf-8'))

            # display cards and remove from hand
            self.show_cards(self.selected, 96, (350,300), 30)
            self.hand = [card for card in self.hand if card not in self.selected]
            for label in self.hand_labels:
                if self.card_map[label] in self.selected:
                    label.deleteLater()
            self.hand_labels = [label for label in self.hand_labels if self.card_map[label] not in self.selected]
            self.card_map = {label: card for label, card in self.card_map.items() if card not in self.selected}
            
            if self.sort_checkbox.isChecked(): # autosort if checked since dom was updated
                self.sort_hand()
            else:
                self.update_hand()
                
            self.play_button.setEnabled(False)
        else:
            bad_play = QMessageBox()
            bad_play.setIcon(QMessageBox.Critical)
            bad_play.setWindowTitle("Invalid Play")
            bad_play.setText(response)
            bad_play.exec_()
        
    def score(self):
        if self.side == "defense":
            confirm = QMessageBox()
            confirm.setIcon(QMessageBox.Question)
            response = QMessageBox.question(confirm, 'Confirm Action', "Are you sure you want to score? You are a defender.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if response == QMessageBox.Yes:
                self.client.write("score-True".encode('utf-8'))
        else:
            self.client.write("score-True".encode('utf-8'))

    def burn(self):
        if self.side == "attack":
            confirm = QMessageBox()
            confirm.setIcon(QMessageBox.Question)
            response = QMessageBox.question(confirm, 'Confirm Action', "Are you sure you want to burn? You are an attacker.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if response == QMessageBox.Yes:
                self.client.write("score-False".encode('utf-8'))
        else:
            self.client.write("score-False".encode('utf-8'))

    def setup(self):
        name = self.name_entry.text()
        if len(name) < 1 or len(name) > 11 or "-" in name or name.strip() == "You":
            bad_name = QMessageBox()
            bad_name.setIcon(QMessageBox.Critical)
            bad_name.setWindowTitle("Bad Name")
            if len(name) < 1:
                bad_name.setText("You need to set a name first!")
            elif "-" in name:
                bad_name.setText("Invalid character \"-\" in name")
            elif name.strip() == "You":
                bad_name.setText("That will unfortunately break my game. Please choose, like, any other name.")
            else:
                bad_name.setText("Name is too long!")
            bad_name.exec_()
        else:
            self.your_name = name
            self.connect()

    def connect(self):
        self.address = self.ip_entry.text()
        self.port = 5050
        self.client = QTcpSocket(self)
        self.client.connected.connect(self.on_connected)
        self.client.readyRead.connect(self.read_data)
        self.client.error.connect(self.on_error)
        self.client.connectToHost(self.address, self.port)
        
        self.setWindowTitle("Tractor - " + self.your_name)

    def on_connected(self):
        print("Connected to server!")
        self.client.write(f"name-{self.your_name}".encode('utf-8'))
    
    def on_error(self, socket_error):
        socket_err = QMessageBox()
        socket_err.setIcon(QMessageBox.Critical)
        socket_err.setWindowTitle("Socket Error")
        socket_err.setText(f"Connection error: {socket_error}")
        socket_err.exec_()
        
    def read_data(self):
        message = self.client.readAll().data().decode('-utf-8')
        
        print(f"message: {message}")
        
        if message.startswith("welcome"): # welcome-0 for first, or welcome-3-Andy-Dustin-Michael for 3 other ppl or welcome-1-Andy for one other, etc...
            parts = message.split("-")
            for i in range(int(parts[1])):
                self.opponents[parts[-1-i]] = self.opponents.pop("p"+str(3-i))
                getattr(self, "p"+str(3-i)+"_label").setText(parts[-1-i])
            
            self.p1_label.setVisible(True)
            self.p2_label.setVisible(True)
            self.p3_label.setVisible(True)
            self.message_label.setText("Waiting for players...")
            self.message_label.setVisible(True)
            self.host_frame.setVisible(False)
        
        elif message.startswith("joined"): # joined-[my_index]-[newplayer_index]-[name] 
            parts = message.split("-")
            index = int(parts[2]) - int(parts[1])
            self.opponents[parts[3]] = self.opponents.pop("p"+str(index))           
            getattr(self, "p"+str(index)+"_label").setText(parts[3])

        elif message.startswith("start"):
            self.message_label.setVisible(False)

            self.call_button.setVisible(True)
            self.draw_button.setVisible(True)
            self.sort_button.setVisible(True)
            self.sort_checkbox.setVisible(True)
            self.dom_img.setVisible(True)
            self.team_img.setVisible(True)
            self.points_label.setVisible(True)
            self.points_label.setText("0/80")
            
            self.call_button.setEnabled(True)
            self.draw_button.setEnabled(message == "start-play")
            
        elif message.startswith("yourturn"):
            self.draw_button.setEnabled(True)
            self.call_button.setEnabled(True)
            if self.speed_deal or self.auto_draw > 0:
                self.draw()
                
        elif message.startswith("draw"):
            self.auto_draw -= 1
            message = message.split("-")
            self.hand.append(Card(message[1], message[2]))

            label = QLabel(self.main_widget)
            label.mousePressEvent = partial(self.click, label)
            self.hand_labels.append(label)
            
            if self.sort_checkbox.isChecked():
                self.sort_hand()
            else:
                self.update_hand()
                
            self.draw_button.setEnabled(False)
            self.call_button.setEnabled(False)
            self.check_team()
        
        elif message.startswith("call"): # e.g., call-Andy-JOKER-RED-TEN-HEARTS
            message = message.split("-")
            self.call_button.setVisible(False)
            self.show_cards([Card(message[2], message[3]), Card(message[4], message[5])], 96, self.opponents[message[1]], 30)
            if message[2] == "TEN": self.dom_suit = message[3]
            else: self.dom_suit = message[5]
            self.set_dom()
        
        elif message.startswith("pot"): # e.g., pot-8-TEN-DIAMONDS-TEN-HEARTS-ACE-HEARTS-...
            self.speed_deal = False
            self.done_button.setVisible(True)
            message = message.split("-")
            self.pot = [Card(message[i], message[i+1]) for i in range(2, len(message), 2)]
            self.show_cards(self.pot, 96, (265, 300), 30)

        elif message.startswith("dealover"):
            self.deal_over = True
            self.speed_deal = False
            self.draw_button.setVisible(False)
            self.call_button.setEnabled(True)
            if self.dom_suit:
                self.check_team()

        elif message.startswith("play"):
            self.clear_cards()
            self.play_button.setVisible(True)
            self.play_button.setEnabled(message == "play-yourturn")
        
        elif message.startswith("put"): # e.g., put-Andy-TEN-HEARTS-TEN-HEARTS-STARTING-TEN-HEARTS-TEN-HEARTS-GO
            message = message.split("-")
            self.call_button.setVisible(False)
            if message[-1] == "GO":
                self.play_button.setEnabled(True)
                message = message[:-1]
            
            if "STARTING" in message:
                self.show_cards([Card(message[i], message[i+1]) for i in range(2, message.index("STARTING"), 2)], 96, self.opponents[message[1]], 30)
                self.starting_cards = [Card(message[i], message[i+1]) for i in range(message.index("STARTING") + 1, len(message), 2)]
            else:
                self.show_cards([Card(message[i], message[i+1]) for i in range(2, len(message), 2)], 96, self.opponents[message[1]], 30)
            
        elif message.startswith("winner"): # e.g., winner-Andy or winner-You or winner-You-POINTS
            self.starting_cards = []
            message = message.split("-")
            self.message_label.setVisible(True)
            self.play_button.setVisible(False)
            self.message_label.setText(message[1] + (" win!" if message[1] == "You" else " wins!"))
            
            if message[1] == "You" and len(message) == 3: # you won, there are points
                self.score_button.setVisible(True)
                self.burn_button.setVisible(True)
            elif message[1] == "You" and not self.hand: # you won, no points, out of cards
                self.timer.singleShot(3000, self.no_cards)
            elif len(message) != 3 and not self.hand: # anybody won, no points, out of cards
                self.timer.singleShot(3000, self.clean_screen)
            else: # next play
                self.timer.singleShot(3000, lambda: self.next_play(message[1] == "You"))

        elif message.startswith("score"): # e.g., score-True-60-GO or score-False-45
            message = message.split("-")
            self.points_label.setText(message[2] + "/80")
            self.score_button.setVisible(False)
            self.burn_button.setVisible(False)

            if len(message) == 4 and not self.hand:
                self.message_label.setText("SCORED" if message[1] == "True" else "BURNED")
                self.timer.singleShot(3000, self.no_cards)
            else:
                self.message_label.setText("SCORED" if message[1] == "True" else "BURNED")
                self.timer.singleShot(3000, lambda: self.next_play(len(message) == 4))
                
        elif message.startswith("gameover"): # e.g., gameover-attack-85 or gameover-defense-70
            message = message.split("-")
            self.points_label.setText(message[2] + "/80")
            self.score_button.setVisible(False)
            self.burn_button.setVisible(False)
            self.message_label.setText(message[1].upper() + " WINS!")
            self.message_label.setVisible(True)
        
        elif message.startswith("endpot"): # e.g., endpot-8-KING-HEARTS-FIVE-SPADES-...
            self.score_button.setVisible(True)
            self.burn_button.setVisible(True)
            message = message.split("-")
            self.pot = [Card(message[i], message[i+1]) for i in range(2, len(message), 2)]
            self.show_cards(self.pot, 96, (265, 300), 30)
            
    
    # --- TIMED FUNCTIONS --- #
    
    def next_play(self, next_player: bool):
        self.message_label.setVisible(False)
        self.play_button.setVisible(True)
        self.play_button.setEnabled(next_player)
        self.clear_cards()

    def no_cards(self):
        self.clear_cards()
        self.client.write("nocards".encode('utf-8'))
    
    def clean_screen(self):
        self.message_label.setVisible(False)
        self.clear_cards()



def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = UI(*sys.argv[1:2]) # 2nd arg could be default name
    sys.exit(app.exec_())





# TODO 
# ----------
# 1 - countercalling
# 1 - play again
# 2 - check if nobody can call
# 2 - ensure unique names
# 3 - prettier UI (either lock windows or make draggable, add colors and fonts, add more labels for explaining what happened, maybe add a help button, etc.)
# 3 - fix suit images
# 4 - f-string formatting