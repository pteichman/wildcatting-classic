import unittest

from wildcatting.model import Player
from wildcatting.week import Week

class TestWeek(unittest.TestCase):
    def testGetOilPrice(self):
        week = Week(1, [Player("alice", "A")], 5.00)
        self.assertAlmostEqual(5.00, week.getPrice())
    
    def testFirstSurveyTurn(self):
        players = []
        players.append(Player("alice", "A"))
        players.append(Player("bob", "B"))

        week = Week(1, players, 5.00)

        self.assertEqual(players[0], week.getSurveyPlayer())

    def testTurnProgression(self):
        players = []
        players.append(Player("alice", "A"))
        players.append(Player("bob", "B"))

        week = Week(1, players, 5.00)
        self.assertEqual(players[0], week.getSurveyPlayer())
        self.assertTrue(week.isSurveyTurn(players[0]))
        self.assertFalse(week.isSurveyTurn(players[1]))

        for player in players:
            self.assertFalse(week.isTurnFinished(player))

        week.endSurvey(players[0])
        self.assertEqual(players[1], week.getSurveyPlayer())
        self.assertTrue(week.isSurveyTurn(players[1]))
        self.assertFalse(week.isSurveyTurn(players[0]))

        week.endSurvey(players[1])
        self.assertEqual(None, week.getSurveyPlayer())

        for player in players:
            self.assertFalse(week.isTurnFinished(player))

        self.assertTrue(players[0] in week.getPendingPlayers())
        week.endTurn(players[0])
        self.assertTrue(players[0] not in week.getPendingPlayers())

        self.assertTrue(players[1] in week.getPendingPlayers())
        week.endTurn(players[1])
        self.assertTrue(players[1] not in week.getPendingPlayers())

        for player in players:
            self.assertTrue(week.isTurnFinished(player))

        self.assertTrue(week.isFinished())

if __name__ == "__main__":
    unittest.main()
