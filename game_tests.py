import unittest
from game import set_dominant, type_of, Card

class TestTypeOfFunction(unittest.TestCase):
    def test_single(self):
        self.assertEqual(type_of([Card("THREE", "CLUBS")]), 1)
    
    def test_pair(self):
        self.assertEqual(type_of([Card("THREE", "CLUBS"),
                                  Card("THREE", "CLUBS")]), 2)

    def test_bad_pair(self):
        self.assertEqual(type_of([Card("THREE", "CLUBS"),
                                  Card("THREE", "HEARTS")]), -1)

    def test_dom_pair(self):
        self.assertEqual(type_of([Card("TWO", "CLUBS"),
                                  Card("TWO", "CLUBS")]), 2)

    def test_bad_dom_pair(self):
        self.assertEqual(type_of([Card("TEN", "HEARTS"),
                                  Card("TWO", "HEARTS")]), -1)

    def test_tractor(self):
        self.assertEqual(type_of([Card("NINE", "CLUBS"),
                                  Card("NINE", "CLUBS"),
                                  Card("JACK", "CLUBS"),
                                  Card("JACK", "CLUBS")]), 3)

    def test_dom_tractor_01(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("ACE", "HEARTS"),
                                  Card("ACE", "HEARTS"),
                                  Card("KING", "HEARTS"),
                                  Card("KING", "HEARTS")]), 3)

    def test_dom_tractor_02(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("ACE", "HEARTS"),
                                  Card("ACE", "HEARTS"),
                                  Card("TWO", "CLUBS"),
                                  Card("TWO", "CLUBS")]), 3)
                                  
    def test_dom_tractor_03(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("ACE", "HEARTS"),
                                  Card("ACE", "HEARTS"),
                                  Card("TWO", "HEARTS"),
                                  Card("TWO", "HEARTS")]), -1)


    def test_dom_tractor_04(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TWO", "CLUBS"),
                                  Card("TWO", "CLUBS"),
                                  Card("TWO", "HEARTS"),
                                  Card("TWO", "HEARTS")]), 3)

    def test_dom_tractor_05(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TWO", "CLUBS"),
                                  Card("TWO", "CLUBS"),
                                  Card("TWO", "DIAMONDS"),
                                  Card("TWO", "DIAMONDS")]), -1)

    def test_dom_tractor_06(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TWO", "HEARTS"),
                                  Card("TWO", "HEARTS"),
                                  Card("TEN", "DIAMONDS"),
                                  Card("TEN", "DIAMONDS")]), 3)

    def test_dom_tractor_07(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TWO", "HEARTS"),
                                  Card("TWO", "HEARTS"),
                                  Card("TEN", "HEARTS"),
                                  Card("TEN", "HEARTS")]), -1)

    def test_dom_tractor_08(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TEN", "CLUBS"),
                                  Card("TEN", "CLUBS"),
                                  Card("TEN", "DIAMONDS"),
                                  Card("TEN", "DIAMONDS")]), -1)

    def test_dom_tractor_09(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TEN", "DIAMONDS"),
                                  Card("TEN", "DIAMONDS"),
                                  Card("TEN", "HEARTS"),
                                  Card("TEN", "HEARTS")]), 3)

    def test_dom_tractor_10(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TEN", "DIAMONDS"),
                                  Card("TEN", "DIAMONDS"),
                                  Card("JOKER", "BLACK"),
                                  Card("JOKER", "BLACK")]), -1)

    def test_dom_tractor_11(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TEN", "HEARTS"),
                                  Card("TEN", "HEARTS"),
                                  Card("JOKER", "BLACK"),
                                  Card("JOKER", "BLACK")]), 3)

    def test_dom_tractor_12(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("TEN", "HEARTS"),
                                  Card("TEN", "HEARTS"),
                                  Card("JOKER", "RED"),
                                  Card("JOKER", "RED")]), -1)

    def test_dom_tractor_13(self):
        set_dominant("HEARTS")
        self.assertEqual(type_of([Card("JOKER", "BLACK"),
                                  Card("JOKER", "BLACK"),
                                  Card("JOKER", "RED"),
                                  Card("JOKER", "RED")]), 3)
 

if __name__ == "__main__":
    unittest.main()