# Wildcatting — Architecture Overview

_Generated 2026-04-11 from a read-through of the `wildcatting-classic` source tree._

Wildcatting is a turn-based, minimally-multiplayer terminal game about oil
speculation in West Texas circa 1902. It is structured as a client/server
application: a long-running **server** holds authoritative game state, and one
or more **curses-based clients** connect to it over XML-RPC, survey the oil
field, drill wells, and sell them back to the market over a fixed number of
in-game weeks.

This document describes the system's components, data model, and the main
interaction flows. It is written from code, not from any external design
document — the source is the spec.

---

## 1. 10,000-foot view

```
            ┌─────────────────────────────────────┐
            │          go-wildcatting             │
            │      (dispatch / argv parsing)      │
            └──────┬──────────┬───────────┬───────┘
                   │          │           │
          ┌────────▼──┐  ┌────▼──────┐  ┌─▼────────────┐
          │  client   │  │  server   │  │  screensaver │
          │ (curses)  │  │ (XML-RPC) │  │ / theme-info │
          └────┬──────┘  └────┬──────┘  └──────────────┘
               │              │
               │   XML-RPC    │
               └─────────────►│
                              │
                        ┌─────▼──────────────┐
                        │ TieredXMLRPCServer │
                        │  ┌──────────────┐  │
                        │  │ BaseService  │  │  echo / ping / version
                        │  │ AdminService │  │  ping
                        │  │ GameService  │  │  new / join / survey / drill / …
                        │  │SettingService│  │  getSetting
                        │  └──────────────┘  │
                        └─────┬──────────────┘
                              │
                        ┌─────▼──────────┐
                        │    Game        │◄──────┐
                        │ (per gameId)   │       │
                        └─────┬──────────┘       │
                              │                  │
             ┌────────────────┼────────────────┐ │
             ▼                ▼                ▼ │
         ┌────────┐      ┌────────┐       ┌──────┴──┐
         │OilField│      │ Week   │       │ Theme    │
         │ (grid  │      │(turns, │       │(West     │
         │ of     │      │ price) │       │ Texas)   │
         │ Sites) │      └────────┘       └──────────┘
         └───┬────┘
             ▼
         ┌────────┐   ┌──────────┐
         │  Site  │◄──┤Reservoir │  (adjacency-merged)
         └───┬────┘   └──────────┘
             │
             ▼
          ┌──────┐
          │ Well │   (per-player, producing barrels/week)
          └──────┘
```

All game logic — site generation, reservoir simulation, well output, taxation,
price walks, turn ordering — lives server-side in `wildcatting.game` and its
helpers. The client is a relatively thin **presentation + input layer** over
curses that knows how to call the server and re-render on each update.

---

## 2. Processes and entry points

The single command is `go-wildcatting`, implemented in
[`wildcatting/cli.py`](../../wildcatting/cli.py) as a `main()` function and
registered via `[project.scripts]` in `pyproject.toml`. It uses
`wildcatting.cmdparse.CommandParser` to dispatch CVS-style subcommands:

| Command       | Class                | Module              | Purpose                                           |
|---------------|----------------------|---------------------|---------------------------------------------------|
| `server`      | `ServerCommand`      | `ServerCommand.py`  | Binds an XML-RPC listener on `:7777` by default.  |
| `client`      | `ClientCommand`      | `ClientCommand.py`  | Connects via `xmlrpc.client.ServerProxy`, runs curses UI. |
| `screensaver` | `ScreensaverCommand` | `ScreensaverCommand.py` | Standalone curses demo that fades oil fields.     |
| `ping`        | `PingCommand`        | `PingCommand.py`    | Smoke-tests a server via `admin.ping`.            |
| `theme-info`  | `ThemeInfoCommand`   | `ThemeInfoCommand.py` | Dumps theme constants (drill cost ranges, etc.). |

The client supports a **no-network mode** (`--no-network`) that substitutes a
`StandaloneServer` — a plain Python object whose attributes mimic the remote
proxy layout (`.game`, `.setting`, `.version`). This makes the XML-RPC surface
transparent to `Client.run()` and enables offline / hotseat play.

---

## 3. Server composition

The server is a subclass of `SimpleXMLRPCServer`:

- **`TieredXMLRPCServer`** (`wildcatting/server.py:18`) — registers methods on
  sub-instances under a dotted namespace (`game.new`, `setting.getSetting`,
  `admin.ping`). It always passes `allow_none=True`. Introspection functions
  are registered via `register_introspection_functions()` in
  `ServerCommand.run()`.

- **`BaseService`** — `echo`, `ping`, `version`. Used for the client/server
  version handshake in `ClientCommand.run()`.

- **`AdminService`** — single-method `ping`. Not currently used beyond
  `PingCommand`.

- **`GameService`** — the meat of the server. Holds a dict of `gameId → Game`,
  mints game / client handles, and routes all player actions through
  authoritative turn and ownership checks.

- **`SettingService`** — serializes the theme's "setting" (location, era,
  price format, drill cost bounds, flavor facts) once at construction and
  hands it to any client that asks.

### 3.1 Handle scheme

`GameService` exposes two kinds of opaque handles, both base64-encoded
strings using `::` as an internal separator:

- **Client handle** — `base64("<gameId>::<clientId>")`. `clientId` is a random
  16-hex-char token minted by `Game._newClientId()` on first contact. Used for
  everything that is not player-specific (`listPlayers`, `getPlayerField`,
  `getUpdate`, `getWeeklySummary`).

- **Game handle** — `base64("<gameId>::<username>::<secret>")`. Minted on
  `join` and returned to the client; `secret` is another 16-hex-char random
  token stored on the `Player`. Used for anything that mutates player state
  (`survey`, `erect`, `drill`, `sell`, `endTurn`, `start`).

There is no cryptographic signing — the handles act as bearer tokens whose
secrecy depends on the 64-bit entropy of the secret + the fact that clients
don't leak them. See [`review.md`](./review.md) for the security commentary.

---

## 4. Domain model

```
┌────────────┐      ┌──────────┐      ┌─────────┐
│  Game      │──*──►│  Player  │──*──►│  Well   │
│            │      └──────────┘      │         │
│ OilField   │                        │ drill/  │
│ Week       │      ┌──────────┐      │ week    │
│ clients    │◄─────┤  Client  │      └──┬──────┘
│ clientUpd. │      │  (hex id)│         │ placed on
└─────┬──────┘      └──────────┘         ▼
      │                                ┌──────┐
      │ fills                          │ Site │
      ▼                                └───┬──┘
┌────────────┐                             │
│ OilField   │──*──────────────────────────┘
│ (w × h)    │
│            │       ┌──────────────┐
│  Site grid │──*───►│  Reservoir   │  shared by adjacent oil sites
└────────────┘       └──────────────┘
```

### 4.1 `Site` (`wildcatting/model/oilfield.py:46`)

Represents one cell on the map. Generated server-side by a pipeline of
"fillers":

1. `OilFiller` — `PeakedFiller` that places 1..N random peaks, computes a
   log-dropoff probability surface (10..100), and rolls a per-cell d100 to
   set an **oil flag**.
2. `PotentialOilDepthFiller` — same peak algorithm, but writes a 1..10 depth
   to cells that have the oil flag.
3. `ReservoirFiller` — walks adjacent (right/down) oil cells and merges them
   into shared `Reservoir` objects when their depth brackets match; otherwise
   gives each site its own one-cell reservoir.
4. `DrillCostFiller` — places another peak field for drill cost, inverted so
   cheap areas cluster.
5. `TaxFiller` — uniform random tax per site from the theme's range.

The result is a mildly realistic landscape with clusters of high-probability,
low-drill-cost sweet spots and shared reservoirs that deplete when pumped.

Two attribute groups live on each `Site`:
- Public, serialized-to-client fields (`_prob`, `_drillCost`, `_tax`,
  `_surveyed`, `_oilDepth`, `_well`).
- **Private** double-underscore fields (`__reservoir`, `__oilFlag`,
  `__potentialOilDepth`) that are deliberately **excluded by the
  `Serializable` custom encoder** and therefore never leave the server. This
  is how the game prevents the client from peeking at hidden reservoir data.

### 4.2 `Well` (`wildcatting/model/oilfield.py:139`)

Owned by a `Player`, tracks drilling progress, initial cost, running P&L,
capacity, and output. `drill()` consumes one drill increment, charges the
player, and checks whether depth reached the reservoir's oil depth. `week()`
is driven by `OilField.week()` every new week and re-runs the `WellTheory`
to produce new output, then debits tax and credits income.

### 4.3 `Reservoir` (`wildcatting/reservoir.py`)

A shared pool of barrels with a total "size" (number of merged sites), total
depth, and a running reserves counter. `ratioPumped()` is used by
`SimpleWellTheory` to gradually reduce well output as the pool drains.

### 4.4 `SimpleWellTheory` (`wildcatting/welltheory.py`)

Turns (site, week) into a new `output` value. Ramps up capacity for the
first three weeks, then decays via `(1 - ratioPumped) * maxOutput`. Replacing
this class is how a theme could introduce different extraction curves.

### 4.5 `Week` / `Turn`

- `Week` holds the price for that week, a copied player order, a
  `_surveyPlayerIndex` (the seat currently holding the mandatory survey
  turn), and a `_pending` list of players who still have to end their turn.
- `Turn` is a per-player record of what they've already done this week
  (`surveyedSite`, `drilledSite`). It's what lets `GameService._ensureTurn`
  reject "already surveyed" / "already drilled elsewhere" attempts.

### 4.6 Prices

`oilprices.py` defines three price walks: `HistoricalPrices` (samples a
random window from an embedded ~275 KB WTI historical dataset baked into the
source), `GaussianPrices`, and `TrendingGaussianPrices` (the default, built
by `WestTexas.__init__`). Each is an iterator; `Game._nextWeek` calls
`next(self._prices)` to advance.

### 4.7 Themes

`Theme` is an abstract configuration object. `WestTexas` (aliased to
`DefaultTheme`) provides all the numerical constants — dropoffs, peak counts,
drill cost bounds, tax range, mean reserves, output bounds — and the
`WellTheory` and `OilPrices` instances. The theme also carries a text corpus
of flavor "facts" that the client draws at random in the bottom border.

---

## 5. Serialization

`Serializable` (`wildcatting/model/serialize.py`) is a hand-rolled
self-describing serializer:

```
{
  "wildcatting.model.Serializable.class": "OilField",
  "wildcatting.model.Serializable.state": {
      "_width": 80,
      "_height": 24,
      "_rows": [[{"wildcatting.model.Serializable.class": "Site", ...}, ...], ...]
  }
}
```

Rules:
- Keys containing `"__"` are **skipped** on serialize — this is how `Site`'s
  private reservoir data stays on the server.
- `deserialize()` re-hydrates by looking up class names via
  `getattr(wildcatting.model, clsname)`, bypassing `__init__` with
  `cls.__new__(cls)` and restoring `__dict__` directly.
- The whole thing rides on top of XML-RPC's built-in primitive/dict/list
  marshalling.

This approach is clever but has consequences — see the Security and
Maintainability sections in [`review.md`](./review.md).

---

## 6. Client

The client is two layers:

- **`wildcatting.client.Wildcatting`** — a plain data holder for the client's
  view of the world (`playerField`, `week`, `oilPrice`, `playersTurn`,
  `pendingPlayers`, `gameFinished`).

- **`wildcatting.client.Client`** — orchestrates the session lifecycle:
  connect / create-or-join game → pregame lobby → main loop (survey, erect,
  drill, weekly report, end turn) → weekly summary → end-game animation.

It pulls updates in two ways:

1. Push — responses from mutating calls (`survey`, `erect`, `drill`) include
   the fresh `Site` or `Well` and are merged into the local player field.
2. Poll — when it's not the player's turn, the main loop calls `getUpdate`
   via a curses `halfdelay` tick. An exponential backoff doubles the
   poll interval if a round-trip takes longer than the current delay.

Rendering is split across view classes in `wildcatting/view/`:

| View class                | Role                                                              |
|---------------------------|-------------------------------------------------------------------|
| `WildcattingView`         | The main framed oil-field screen with probability/cost/depth tabs |
| `OilFieldProbabilityView` | Colored heat-map of survey probability                            |
| `OilFieldDrillCostView`   | Heat-map of drill cost                                            |
| `OilFieldDepthView`       | Heat-map of known oil depth                                       |
| `DrillView`               | The drill-or-stop animation screen                                |
| `SurveyorsReportView`     | Post-survey modal with site stats and "drill?" prompt             |
| `WeeklyReportView`        | End-of-turn review of owned wells, sell action                    |
| `WeeklySummaryView`       | Week rollup / final game scoreboard                               |
| `PregameReportView`       | Lobby display before the master starts the game                   |
| `PlayerCountView` / `PlayerNamesView` | Hotseat player entry                                   |

---

## 7. Core interaction flows

### 7.1 Bootstrap and join

```
Client                                   Server (GameService)
──────                                   ────────────────────

ClientCommand.run()
  ServerProxy("http://host:7777/")
  s.version()                 ──────►    BaseService.version
                                         (returns VERSION_STRING)
  (version handshake)         ◄──────

Client.run(server)
  s.setting.getSetting()      ──────►    SettingService.getSetting
                                         (pre-serialized theme setting)
Client.wildcatting(stdscr)
  _inputUserNames()
  _connectToGame()
     if new game:
       s.game.new(w,h,turns)  ──────►    GameService.new
                                           gameId = str(next)
                                           Game(w,h,turns,theme)
                                             OilFiller ─► ReservoirFiller ─►
                                             DrillCostFiller ─► TaxFiller
                                           return newClientHandle(gameId)
                                         ◄──────
     for each local player:
       s.game.join(ch, user, sym)  ────► GameService.join
                                           game.addPlayer(clientId,player)
                                           secret = hex16
                                           player.setSecret(secret)
                                           return gameHandle
                                         ◄──────
     s.game.getClientInfo(ch) ────────►  maps each joined player → handle
  _runPreGame()
     loop:
       s.game.isStarted(ch)  ────────►   game.isStarted()
       s.game.listPlayers(ch) ───────►   (pending lobby)
       if master & "start":
         s.game.start(masterHandle) ──►  Game.start()
                                           _nextWeek()
                                             Week(1, players, price)
                                             OilField.week(...)
```

### 7.2 A single player turn

```
Client                                   Server
──────                                   ──────

(It is my turn.)
user navigates, hits space
  s.game.survey(h, r, c)      ──────►    GameService.survey
                                           _ensureSurveyTurn
                                           site.setSurveyed(True)
                                           turn.setSurveyedSite(site)
                                           game.markSiteUpdated(player,site)
                                           week.endSurvey(player)
                                         ◄── serialized Site
SurveyorsReportView → "drill?"
  s.game.erect(h, r, c)       ──────►    GameService.erect
                                           well = Well(); site.setWell(well)
                                           game.drill(r,c)  # first increment
                                         ◄── serialized Site (masked to player)
DrillView loop:
  while not output and depth<10:
    user hits space
    s.game.drill(h, r, c)     ──────►    GameService.drill
                                           _ensureTurn
                                           game.drill(r,c)
                                             well.drill(site, inc)
                                             if foundOil: theory.start(site)
                                         ◄── serialized Well

WeeklyReportView (built locally from player field)
  optionally s.game.sell(h,r,c) ────►    GameService.sell
                                           well.sell()
                                         ◄── price (int)
  user picks NEXT PLAYER
  s.game.endTurn(h)           ──────►    GameService.endTurn
                                           week.endTurn(player)
                                           if week.isFinished(): _nextWeek()
                                             OilField.week(price, theory, n)
                                               for each site with a well:
                                                 theory.week → new output
                                                 reservoir.pump
                                                 well.week → debit tax/credit
                                         ◄── (None, wellUpdates[])
  merge wellUpdates into local player field
```

### 7.3 Passive updates for non-active clients

While another player is taking their turn, a client drops into a curses
`halfdelay` loop. Each tick:

```
while not finished:
    input(c, refresh)    # returns {"checkForUpdates": True} on timeout
    s.game.getUpdate(clientHandle)
        returns Update { week, oilPrice, playersTurn, pendingPlayers,
                         gameFinished, sites: [Site, ...] }
    merge sites, refresh view
    if round-trip > refresh: exponential backoff
```

`Game.markSiteUpdated` bookkeeps a **per-client queue** of sites that have
changed since that client last polled, filtered so a client does not receive
echoes of updates it caused itself (the check is "site touched by a player
this client does not own"). `getUpdatedSites(clientId)` drains the queue.

### 7.4 Lifecycle summary

```
                       ┌─────────┐
                       │  new    │  (clientHandle minted)
                       └────┬────┘
                            │ join(s)
                       ┌────▼────┐
                       │ pregame │  (players queue up, master visible)
                       └────┬────┘
                            │ start (master only)
                       ┌────▼──────────┐
                       │ week 1..N     │
                       │               │
                       │  for each p:  │
                       │    survey     │
                       │    [erect]    │
                       │    [drill*]   │
                       │    [sell*]    │
                       │    endTurn    │
                       │               │
                       │  advance week │
                       │   price walk  │
                       │   pump wells  │
                       └────┬──────────┘
                            │ week > turnCount
                       ┌────▼────┐
                       │ finish  │  (scores logged, oil revealed)
                       └─────────┘
```

---

## 8. Module dependency graph

```
wildcatting.cli (go-wildcatting)
    │
    └── wildcatting.cmdparse
           │
           ├── ClientCommand ──► client ──► view ──► model
           │                      │
           │                      └─► (xmlrpc proxy or StandaloneServer)
           │
           ├── ServerCommand ──► server ──► game ──► model
           │                       │          ├─► theme ──► oilprices
           │                       │          ├─► welltheory
           │                       │          ├─► reservoir
           │                       │          ├─► week / turn
           │                       │          └─► model (OilField, Player…)
           │                       └─► theme (SettingService)
           │
           ├── ScreensaverCommand ─► view + game (standalone field gen)
           ├── PingCommand         ─► xmlrpc proxy
           └── ThemeInfoCommand    ─► theme
```

Notable:
- The `client` package imports `game.Game` — but only for the `--no-network`
  path via `StandaloneServer` in `ClientCommand`. Client-only code does not
  touch authoritative game state.
- `model.serialize` reaches back into `wildcatting.model` at runtime to
  resolve class names, so the model package is effectively a mutually
  recursive unit.
- There is **no third-party runtime dependency** — everything is standard
  library (curses, xmlrpc, optparse, random, math, base64). This is a
  significant maintainability asset (see review).

---

## 9. Testing

Tests live in `test/` and are run with:

    uv run python -m unittest discover test/

| File                         | Scope                                                                                         |
|------------------------------|-----------------------------------------------------------------------------------------------|
| `test_gameservice.py`        | Integration-style tests of `GameService` (start, end-turn ordering, sneaky erect/drill, multi-player). |
| `test_game.py`               | Lower-level `Game` behavior, field filler contracts.                                          |
| `test_week.py`               | Turn ordering within a `Week`.                                                                |
| `test_model_oilfield.py`     | Sanity on `OilField` grid access.                                                             |
| `test_model_serialize.py`    | Round-tripping `Site`, `OilField`, and `Setting` through `Serializable`.                     |
| `test_financial.py`          | Financial invariants: drill cost accounting, P&L identity, sell-for-half, weekly income formula. |
| `test_reservoir.py`          | Reservoir pump bounds, `ratioPumped` monotonicity, well output cap, Gaussian price floor.     |
| `test_information_hiding.py` | What clients can and cannot see: `oilFlag`/reservoir never serialized, `oilDepth` hidden until discovered, post-game field reveal. Round-trips `Well`, `Player`, `WeeklySummary`. |
| `test_stochastic.py`         | Seeded determinism, theme range constraints, complete game lifecycle, oil discovery depth, idle P&L, multiplayer turn ordering. |

There is no network test — `GameService` is exercised by calling methods
directly rather than through XML-RPC. Curses views are not covered.

---

## 10. Where to look for what

| I want to change…                               | Start here                                                 |
|-------------------------------------------------|------------------------------------------------------------|
| Map generation shape / difficulty               | `wildcatting/game.py` (Filler classes) + theme constants   |
| Oil price behavior                              | `wildcatting/oilprices.py`, `theme/westtexas.py`           |
| Well output curve / depletion                   | `wildcatting/welltheory.py`, `wildcatting/reservoir.py`    |
| RPC surface / handle format                     | `wildcatting/server.py` (`GameService`)                    |
| What a client sees about a site                 | `GameService._makePlayerSite`, `Serializable.__serialize_dict` |
| Key bindings and screen layout                  | `wildcatting/view/wildcattingview.py`                      |
| Lobby flow                                      | `Client._runPreGame`, `PregameReportView`                  |
| Flavor text / facts                             | `wildcatting/theme/westtexas.py`                           |

For a persona-driven critique — staff engineer, security, SRE, QA, game
designer, and Python modernization — see
[`review.md`](./review.md).
