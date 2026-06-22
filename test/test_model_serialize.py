from wildcatting.model import OilField, Player, Setting, Site, WeeklySummary, Well


class TestSerializer:
    def testSite(self) -> None:
        site1 = Site(1, 1)
        obj1 = site1.serialize()
        site2 = Site.deserialize(obj1)
        obj2 = site2.serialize()

        assert obj1 == obj2

    def testOilField(self) -> None:
        field1 = OilField(2, 2)
        obj1 = field1.serialize()
        field2 = OilField.deserialize(obj1)
        obj2 = field2.serialize()

        assert obj1 == obj2

    def testSetting(self) -> None:
        setting1 = Setting()
        obj1 = setting1.serialize()
        setting2 = Setting.deserialize(obj1)
        obj2 = setting2.serialize()

        assert obj1 == obj2


class TestSerializationRoundTrips:
    def test_well_round_trip(self) -> None:
        player = Player("alice", "A")
        well1 = Well(week=3, player=player)
        well1.drill_depth = 4
        well1.output = 20.0
        well1.capacity = 2

        obj1 = well1.serialize()
        well2 = Well.deserialize(obj1)
        obj2 = well2.serialize()

        assert obj1 == obj2

    def test_player_round_trip(self) -> None:
        player1 = Player("bob", "B")
        player1.secret = "DEADBEEF12345678"
        player1.income(500)
        player1.expense(200)

        obj1 = player1.serialize()
        player2 = Player.deserialize(obj1)
        obj2 = player2.serialize()

        assert obj1 == obj2

    def test_weekly_summary_round_trip(self) -> None:
        players = [Player("alice", "A"), Player("bob", "B")]
        players[0].income(1000)
        players[1].expense(200)

        summary1 = WeeklySummary(players, 5)
        obj1 = summary1.serialize()
        summary2 = WeeklySummary.deserialize(obj1)
        obj2 = summary2.serialize()

        assert obj1 == obj2


class TestWeeklySummaryLeader:
    def test_highest_pnl_player_is_leader(self) -> None:
        alice = Player("alice", "A")
        bob = Player("bob", "B")
        alice.income(500)
        bob.income(200)

        summary = WeeklySummary([alice, bob], week=3)
        rows = {r["username"]: r for r in summary.report_rows}

        assert rows["alice"]["leader"] is True
        assert rows["bob"]["leader"] is False

    def test_tied_leaders_both_flagged(self) -> None:
        alice = Player("alice", "A")
        bob = Player("bob", "B")
        alice.income(300)
        bob.income(300)

        summary = WeeklySummary([alice, bob], week=3)
        rows = {r["username"]: r for r in summary.report_rows}

        assert rows["alice"]["leader"] is True
        assert rows["bob"]["leader"] is True

    def test_single_player_is_leader(self) -> None:
        alice = Player("alice", "A")
        summary = WeeklySummary([alice], week=1)
        assert summary.report_rows[0]["leader"] is True
