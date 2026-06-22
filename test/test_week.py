import unittest

from wildcatting.model import Player
from wildcatting.week import Week


class TestWeek(unittest.TestCase):
    def testGetOilPrice(self) -> None:
        week = Week(1, [Player("alice", "A")], 5.00)
        self.assertAlmostEqual(5.00, week.price)

    def testFirstSurveyTurn(self) -> None:
        players = []
        players.append(Player("alice", "A"))
        players.append(Player("bob", "B"))

        week = Week(1, players, 5.00)

        self.assertEqual(players[0], week.survey_player)

    def testTurnProgression(self) -> None:
        players = []
        players.append(Player("alice", "A"))
        players.append(Player("bob", "B"))

        week = Week(1, players, 5.00)
        self.assertEqual(players[0], week.survey_player)
        self.assertTrue(week.is_survey_turn(players[0]))
        self.assertFalse(week.is_survey_turn(players[1]))

        for player in players:
            self.assertFalse(week.is_turn_finished(player))

        week.end_survey(players[0])
        self.assertEqual(players[1], week.survey_player)
        self.assertTrue(week.is_survey_turn(players[1]))
        self.assertFalse(week.is_survey_turn(players[0]))

        week.end_survey(players[1])
        self.assertEqual(None, week.survey_player)

        for player in players:
            self.assertFalse(week.is_turn_finished(player))

        self.assertTrue(players[0] in week.pending_players)
        week.end_turn(players[0])
        self.assertTrue(players[0] not in week.pending_players)

        self.assertTrue(players[1] in week.pending_players)
        week.end_turn(players[1])
        self.assertTrue(players[1] not in week.pending_players)

        for player in players:
            self.assertTrue(week.is_turn_finished(player))

        self.assertTrue(week.finished)


if __name__ == "__main__":
    unittest.main()
