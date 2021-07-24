from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QLineEdit, QMessageBox, QLabel, QSizePolicy
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
import sys
import socket
import threading
import pickle
from game import Card
from time import sleep


class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()

        uic.loadUi("client.ui", self)

        question = QPixmap("images/questionMark.png").scaledToHeight(64)
        self.domImg.setPixmap(question)
        self.domImg.resize(question.width(), question.height())

        #sword = QPixmap("images/shield.png").scaledToHeight(64)
        self.teamImg.setPixmap(question)
        self.teamImg.resize(question.width(), question.height())
        
        self.nameSubmit.clicked.connect(setup)
        self.drawButton.clicked.connect(draw)

        self.callButton.setVisible(False)
        self.drawButton.setVisible(False)
        self.sortButton.setVisible(False)
        self.domImg.setVisible(False)
        self.teamImg.setVisible(False)

        self.show()

    # draw cards of height height onto the UI from Card list cards,
    # starting at tuple start (x, y), spaced by spacing
    def showCards(self, cards, height, start, spacing):
        print("heya")
        for i, card in enumerate(cards):
            label = QLabel(self)
            print("nope")
            label.move(int(start[0] + i * spacing), start[1])
            pixmap = QPixmap("images/cards/" + card.fileName()).scaledToHeight(height)
            label.setPixmap(pixmap)
            label.resize(pixmap.width(), pixmap.height())
            label.show()
    
    def updateHand(self, hand):
        print('hiya')
        length = len(hand)
        spacing = 50 - length
        x = (665 - spacing * (length-1)) / 2
        self.showCards(hand, 192, (x, 424), spacing)


def setup():
    global yourName
    if len(MainWindow.nameEntry.text()) < 1:
        needName = QMessageBox()
        needName.setIcon(QMessageBox.Critical)
        needName.setText("You need to set a name first!")
        needName.setWindowTitle("Need Name")
        needName.exec_()
    else:
        yourName = MainWindow.nameEntry.text()
        connect(yourName)


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
    global yourName, oppNames, MainWindow
    while True:
        message = sock.recv(4096).decode('utf-8')

        if not message:
            break
    
        if message.startswith("welcome"):
            MainWindow.title.setText("Waiting for players...")
        
        elif message.startswith("start"):
            MainWindow.callButton.setVisible(True)
            MainWindow.drawButton.setVisible(True)
            MainWindow.domImg.setVisible(True)
            MainWindow.teamImg.setVisible(True)

            MainWindow.callButton.setEnabled(False)
            MainWindow.drawButton.setEnabled(message == "start-play")
        
        elif message.startswith("yourturn"):
            MainWindow.drawButton.setEnabled(True)
            print("HI")

        elif message.startswith("draw"):
            message = message.split("-")
            hand.append(Card(message[1], message[2]))
            print("yo")
            MainWindow.updateHand(hand)
            MainWindow.drawButton.setEnabled(False)



    sock.close()


def draw():
    client.send("draw".encode('utf-8'))





app = QApplication(sys.argv)
MainWindow = UI()
MainWindow.setWindowTitle("Tractor Client")

client = None
HOST_ADDR = socket.gethostbyname(socket.gethostname())
HOST_PORT = 5050

yourName = ""
oppNames = []
hand = []

sys.exit(app.exec_())
