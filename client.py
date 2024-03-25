from re import M
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLineEdit, QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import sys
import socket
import threading
from game import Card, set_dominant, tractor_sorted, valid_play
from time import sleep
from functools import partial


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        uic.loadUi("client.ui", self)

        question = QPixmap("images/questionMark.png").scaledToHeight(64)
        self.dom_img.setPixmap(question)
        self.dom_img.resize(question.width(), question.height())

        #sword = QPixmap("images/shield.png").scaledToHeight(64)
        self.team_img.setPixmap(question)
        self.team_img.resize(question.width(), question.height())
        
        self.name_submit.clicked.connect(setup)
        self.draw_button.clicked.connect(draw)
        self.call_button.clicked.connect(call)
        self.sort_button.clicked.connect(sort)
        self.done_button.clicked.connect(done)
        self.play_button.clicked.connect(play)
        self.score_button.clicked.connect(score)
        self.burn_button.clicked.connect(burn)

        self.p1_label.setVisible(False)
        self.p2_label.setVisible(False)
        self.p3_label.setVisible(False)
        self.message_label.setVisible(False)
        self.points_label.setVisible(False)
        self.call_button.setVisible(False)
        self.draw_button.setVisible(False)
        self.done_button.setVisible(False)
        self.sort_button.setVisible(False)
        self.play_button.setVisible(False)
        self.score_button.setVisible(False)
        self.burn_button.setVisible(False)
        self.sort_checkbox.setVisible(False)
        self.dom_img.setVisible(False)
        self.team_img.setVisible(False)

        self.card_map = {} # maps the card label to the Card object 

        self.hand = [QLabel(self) for _ in range(25)]
        for c in self.hand:
            c.mousePressEvent = partial(self.click, c)

        self.p1_cards = [QLabel(self) for _ in range(4)]
        self.p2_cards = [QLabel(self) for _ in range(4)]
        self.p3_cards = [QLabel(self) for _ in range(4)]
        self.my_cards = [QLabel(self) for _ in range(4)]
        self.pot_cards = [QLabel(self) for _ in range(8)]
        for c in self.pot_cards:
            c.mousePressEvent = partial(self.click, c)

        self.show()

    def click(self, label, event):
        if not label.pixmap():
            return
            
        global selected, pot, hand
        card = self.card_map[label]
        if label in self.hand:
            if card in selected:
                label.move(label.x(), label.y() + 50)
                selected.remove(card)
            else:
                label.move(label.x(), label.y() - 50)
                selected.append(card)
        else: # clicked on pot card
            if len(selected) == 1:
                pot[pot.index(card)] = selected[0]
                hand[hand.index(selected[0])] = card
                selected = []
                if self.sort_checkbox.isChecked():
                    sort()
                else:
                    self.update_hand(hand)
                self.show_cards(pot, 96, (265, 300), 30)



    # draw cards of height height onto the UI from Card list cards,
    # starting at tuple start (x, y), spaced by spacing
    def show_cards(self, cards, height, start, spacing):
        my_source = self.hand
        if start == (120, 200): my_source = self.p1_cards
        elif start == (350, 100): my_source = self.p2_cards
        elif start == (550, 200): my_source = self.p3_cards
        elif start == (350, 300): my_source = self.my_cards
        elif start == (265, 300): my_source = self.pot_cards

        for i, card in enumerate(cards):
            label = my_source[i]
            label.move(int(start[0] + i * spacing), start[1])
            pixmap = QPixmap("images/cards/" + card.file_name()).scaledToHeight(height)
            label.setPixmap(pixmap)
            label.resize(pixmap.width(), pixmap.height())
            label.show()
            self.card_map[label] = card
    
    # do some math to measure a good placement for hand
    def update_hand(self, cards):
        global selected
        self.clear_hand()
        selected = []
        length = len(cards)
        spacing = 50 - length
        x = (665 - spacing * (length-1)) / 2
        self.show_cards(cards, 192, (x, 424), spacing)

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
        for card in self.hand:
            if card.pixmap():
                card.setPixmap(QPixmap())



def setup():
    global your_name
    name = MainWindow.name_entry.text()
    if len(name) < 1 or len(name) > 11 or "-" in name or name.strip() == "You":
        bad_name = QMessageBox()
        bad_name.setIcon(QMessageBox.Critical)
        bad_name.setWindowTitle("Bad Name")
        if len(name) < 1:
            bad_name.setText("You need to set a name first!")
        elif "-" in name:
            bad_name.setText("Invalid character \"-\" in name")
        elif name.strip() == "You":
            bad_name.setText("Fuck off. You're not cute.")
        else:
            bad_name.setText("Name is too long!")
        bad_name.exec_()
    else:
        your_name = name
        connect(your_name)


def connect(name):
    global client, HOST_PORT, HOST_ADDR
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST_ADDR, HOST_PORT))
        client.send(name.encode('utf-8'))
        # start a thread to keep receiving message from server
        thread = threading.Thread(target=receive, args=(client,))
        thread.start()

        MainWindow.setWindowTitle("Tractor Client - " + name)
    except socket.error:
        error = QMessageBox()
        error.setIcon(QMessageBox.Critical)
        error.setText("Error: Could not connect to server")
        error.setWindowTitle("Connection Issue")
        error.exec_()


def receive(sock):
    global your_name, opponents, MainWindow, SPEED_DEAL, dom_suit, pot, auto_draw, deal_over, starting_cards, hand
    while True:
        message = sock.recv(4096).decode('utf-8')

        if not message:
            break
    
        if message.startswith("welcome"): # welcome-0 for first, or welcome-3-Andy-Dustin-Michael for 3 other ppl or welcome-1-Andy for one other, etc...
            MainWindow.p1_label.setVisible(True)
            MainWindow.p2_label.setVisible(True)
            MainWindow.p3_label.setVisible(True)

            parts = message.split("-")

            for i in range(int(parts[1])):
                MainWindow.findChild(QLabel, "p"+str(3-i)+"_label").setText(parts[-1-i])
                opponents[parts[-1-i]] = opponents.pop("p"+str(3-i))

            MainWindow.title.setText("Waiting for players...")
            MainWindow.name_frame.setVisible(False)

        elif message.startswith("joined"):  # joined-[my_index]-[newplayer_index]-[name] 
            parts = message.split("-")
            index = int(parts[2]) - int(parts[1])
            MainWindow.findChild(QLabel, "p"+str(index)+"_label").setText(parts[3])
            opponents[parts[3]] = opponents.pop("p"+str(index))
        
        elif message.startswith("start"):
            MainWindow.title.setText("Tractor - " + your_name)

            MainWindow.call_button.setVisible(True)
            MainWindow.draw_button.setVisible(True)
            MainWindow.sort_button.setVisible(True)
            MainWindow.sort_checkbox.setVisible(True)
            MainWindow.dom_img.setVisible(True)
            MainWindow.team_img.setVisible(True)
            MainWindow.points_label.setVisible(True)
            MainWindow.points_label.setText("0/80")

            MainWindow.call_button.setEnabled(True)
            MainWindow.draw_button.setEnabled(message == "start-play")
        
        elif message.startswith("yourturn"):
            MainWindow.draw_button.setEnabled(True)
            if SPEED_DEAL or auto_draw > 0:
                sleep(0.1)
                draw()

        elif message.startswith("draw"):
            auto_draw -= 1
            message = message.split("-")
            hand.append(Card(message[1], message[2]))
            if MainWindow.sort_checkbox.isChecked():
                sort()
            else:
                MainWindow.update_hand(hand)
            MainWindow.draw_button.setEnabled(False)
            check_team()
        
        elif message.startswith("call"): # e.g., call-Andy-JOKER-RED-TEN-HEARTS
            message = message.split("-")
            MainWindow.call_button.setVisible(False)
            MainWindow.show_cards([Card(message[2], message[3]), Card(message[4], message[5])], 96, opponents[message[1]], 30)
            if message[2] == "TEN": dom_suit = message[3]
            else: dom_suit = message[5]
            set_dom()
            check_team()
        
        elif message.startswith("pot"): # e.g., pot-8-TEN-DIAMONDS-TEN-HEARTS-ACE-HEARTS-...
            SPEED_DEAL = False
            MainWindow.done_button.setVisible(True)
            message = message.split("-")
            pot = [Card(message[i], message[i+1]) for i in range(2, len(message), 2)]
            MainWindow.show_cards(pot, 96, (265, 300), 30)

        elif message.startswith("dealover"):
            deal_over = True
            SPEED_DEAL = False
            MainWindow.draw_button.setVisible(False)
            if dom_suit:
                check_team()
        
        elif message.startswith("play"):
            MainWindow.clear_cards()
            MainWindow.play_button.setVisible(True)
            MainWindow.play_button.setEnabled(message == "play-yourturn")

        elif message.startswith("put"): # e.g., put-Andy-TEN-HEARTS-TEN-HEARTS-STARTING-TEN-HEARTS-TEN-HEARTS-GO
            message = message.split("-")
            MainWindow.call_button.setVisible(False)
            if message[-1] == "GO":
                MainWindow.play_button.setEnabled(True)
                message = message[:-1]
            
            if "STARTING" in message:
                MainWindow.show_cards([Card(message[i], message[i+1]) for i in range(2, message.index("STARTING"), 2)], 96, opponents[message[1]], 30)
                starting_cards = [Card(message[i], message[i+1]) for i in range(message.index("STARTING") + 1, len(message), 2)]
            else:
                MainWindow.show_cards([Card(message[i], message[i+1]) for i in range(2, len(message), 2)], 96, opponents[message[1]], 30)
        
        elif message.startswith("winner"): # e.g., winner-Andy or winner-You or winner-You-POINTS
            starting_cards = []
            message = message.split("-")
            MainWindow.message_label.setVisible(True)
            MainWindow.play_button.setVisible(False)
            MainWindow.message_label.setText(message[1] + (" win!" if message[1] == "You" else " wins!"))
            
            if message[1] == "You" and len(message) == 3:
                MainWindow.score_button.setVisible(True)
                MainWindow.burn_button.setVisible(True)
            elif message[1] == "You" and not hand: # NO CARDS LEFT ADD MORE HERE
                client.send("nocards".encode('utf-8'))
            elif len(message) != 3:
                sleep(3)
                MainWindow.message_label.setVisible(False)
                MainWindow.play_button.setEnabled(message[1] == "You")
                MainWindow.clear_cards()

        elif message.startswith("score"): # e.g., score-True-60-GO or score-False-45
            message = message.split("-")
            MainWindow.points_label.setText(message[2] + "/80")
            MainWindow.score_button.setVisible(False)
            MainWindow.burn_button.setVisible(False)

            if len(message) == 4 and not hand: # NO CARDS LEFT ADD MORE HERE
                pass
            else:
                MainWindow.message_label.setText("SCORED" if message[1] == "True" else "BURNED")
                sleep(3)
                MainWindow.message_label.setVisible(False)
                MainWindow.play_button.setVisible(True)
                MainWindow.play_button.setEnabled(len(message) == 4)
                MainWindow.clear_cards()
        
        elif message.startswith("gameover"): # e.g., gameover-attack or gameover-defense
            message = message.split("-")
            MainWindow.score_button.setVisible(False)
            MainWindow.burn_button.setVisible(False)
            MainWindow.message_label.setText(message[1].upper() + " WINS!")
            MainWindow.message_label.setVisible(True)


    sock.close()


def draw():
    if MainWindow.draw_button.text() == "Auto Draw":
        MainWindow.draw_button.setVisible(False)
    client.send("draw".encode('utf-8'))


def call():
    global dom_suit
    # error checking (need two cards: one ten and one joker)
    if len(selected) == 2 and ((selected[0].get_rank() == "JOKER" and selected[1].get_rank() == "TEN") or
                               (selected[1].get_rank() == "JOKER" and selected[0].get_rank() == "TEN")):
        client.send(("call-" + selected[0].get_rank() + "-" + selected[0].get_suit() +
                         "-" + selected[1].get_rank() + "-" + selected[1].get_suit()).encode('utf-8'))
        MainWindow.call_button.setVisible(False)
        if selected[0].get_rank() == "TEN": dom_suit = selected[0].get_suit()
        else: dom_suit = selected[1].get_suit()
        set_dom()
    else:
        bad_call = QMessageBox()
        bad_call.setIcon(QMessageBox.Critical)
        bad_call.setWindowTitle("Bad Call")
        bad_call.setText("You must call with exactly one ten and one joker!")
        bad_call.exec_()
        

def set_dom():
    global SPEED_DEAL, dom_suit
    suit_map = QPixmap("images/" + dom_suit.lower() + ".png").scaledToHeight(64)
    set_dominant(dom_suit) # update dom values in game.py
    if MainWindow.sort_checkbox.isChecked(): # autosort if checked since dom was updated
        sort()
    MainWindow.dom_img.setPixmap(suit_map)
    MainWindow.dom_img.resize(suit_map.width(), suit_map.height())
    if MainWindow.draw_button.isEnabled():
        MainWindow.draw_button.setText("Auto Draw")
        MainWindow.draw_button.move(350, 200)
    else:
        MainWindow.draw_button.setVisible(False)
    SPEED_DEAL = True
    check_team()


def check_team():
    global deal_over, side
    team = QPixmap("images/questionMark.png").scaledToHeight(64)
    for card in hand:
        if card.get_rank() == "TEN" and card.get_suit() == dom_suit:
            team = QPixmap("images/shield.png").scaledToHeight(64)
            side = "defense"
            deal_over = False
            break
    if deal_over:
        team = QPixmap("images/sword.png").scaledToHeight(64)
        side = "attack"
    MainWindow.team_img.setPixmap(team)
    MainWindow.team_img.resize(team.width(), team.height())


def sort():
    global hand
    hand = tractor_sorted(hand)
    MainWindow.update_hand(hand)


def done():
    MainWindow.clear_pot()
    client.send(("bury-" + str(len(pot)) + "-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in pot])).encode('utf-8'))


def play():
    global hand, selected, starting_cards
    if not selected:
        bad_play = QMessageBox()
        bad_play.setIcon(QMessageBox.Critical)
        bad_play.setWindowTitle("Invalid Play")
        bad_play.setText("Must select 1, 2, or 4 cards to play")
        bad_play.exec_()
        return     

    if valid_play(starting_cards, selected, hand):
        client.send(("play-" + "-".join([card.get_rank() + "-" + card.get_suit() for card in selected])).encode('utf-8'))
        #display cards and remove from hand
        MainWindow.show_cards(selected, 96, (350,300), 30)
        hand = [card for card in hand if card not in selected]
        MainWindow.update_hand(hand)
        MainWindow.play_button.setEnabled(False)
    else:
        bad_play = QMessageBox()
        bad_play.setIcon(QMessageBox.Critical)
        bad_play.setWindowTitle("Invalid Play")
        bad_play.setText("Invalid play!")
        bad_play.exec_()


def score():
    global side
    if side == "defense":
        confirm = QMessageBox()
        confirm.setIcon(QMessageBox.Question)
        response = QMessageBox.question(confirm, 'Confirm Action', "Are you sure you want to score? You are a defender.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:
            client.send("score-True".encode('utf-8'))
    else:
        client.send("score-True".encode('utf-8'))


def burn():
    global side
    if side == "attack":
        confirm = QMessageBox()
        confirm.setIcon(QMessageBox.Question)
        response = QMessageBox.question(confirm, 'Confirm Action', "Are you sure you want to burn? You are an attacker.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if response == QMessageBox.Yes:
            client.send("score-False".encode('utf-8'))
    else:
        client.send("score-False".encode('utf-8'))



app = QApplication(sys.argv)
MainWindow = UI()
MainWindow.setWindowTitle("Tractor Client")

client = None
HOST_ADDR = socket.gethostbyname(socket.gethostname())
HOST_PORT = 5050

your_name = ""
opponents = {
    "p1": (120, 200),
    "p2": (350, 100),
    "p3": (550, 200)
}
side = "defense"
hand = []
selected = []
pot = []
dom_suit = ""
SPEED_DEAL = False
auto_draw = 0
deal_over = False
starting_cards = []

sys.exit(app.exec_())




# NEXT STEPS
# ----------
# 1. DONE Fix game breaking if nobody calls until all cards dealt
# 2. DONE Start game (make play button visible)
# 3. DONE Send message for cards someone played and then when its your turn
# 4. DONE Figure out when a round is over (keep track of starter?) and see who won
# 5. DONE Let winner be able to add to pot (maybe just a button for "score" and "dont score", and add warning if doing something for wrong team)
        # DONE need thing for wrong team
        # cards on right side are buggy
        # DONE reposition score and burn buttons
        # DONE dont ask if no points
# 6. DONE Clear cards and let winner go first
# 7. Winning the game (check points, check no cards left, if no cards check buried, etc.)
# 8. Make prettier (either lock windows or make draggable, add colors and fonts, add more labels for explaining what happened, maybe add a help button, etc)
# 9. Make work across networks (haha i'm gonna kill myself)
# 10. Fix random crashes
# 11. Enter IP for client