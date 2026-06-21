# Wildcatting — Persona-Based Engineering Review

_Companion to [`overview.md`](./overview.md). Generated 2026-04-11 from a
read-through of the source._

This review walks the codebase through six different professional lenses and
collects what each would say. Severity in each finding is tagged:

- **(S)** — structural / worth a real fix
- **(M)** — minor / clean-up opportunity
- **(N)** — note / subjective or stylistic

Nothing in here is meant as a dunk. Wildcatting is a small, self-contained,
dependency-free Python 3 game that compiles cleanly to 2026 interpreters
despite carrying Python 2-era bones, and that is itself impressive. The
goal of the review is to say what a team taking ownership of it today
would want to know.

> **Session update — 2026-04-11.** Several findings from this review were
> addressed in a subsequent session. Resolved items are marked **(RESOLVED)**
> inline. A summary is at the bottom of this document.
>
> **Session update — 2026-06-21.** Second pass of fixes. Resolved items
> updated below; summary extended at the bottom.

---

## Persona 1 — Staff Software Engineer

### Architecture observations

- **(N) Clean separation of concerns.** The split between `GameService`
  (policy / RPC authority) and `Game` (state container) is sensible. The
  client is genuinely thin — game rules live server-side, and the client
  only asks authoritative questions and re-renders.
- **(N) Feature toggles via themes.** Everything tunable about the game
  comes out of `Theme` abstract methods. Adding a second location is
  mostly a matter of subclassing `Theme` and supplying constants. The
  existing code reinforces this: `WestTexas` is aliased to `DefaultTheme`
  in `wildcatting/theme/__init__.py`, so there's a real extension seam.
- **(N) No third-party runtime dependencies.** For a hobby/retro game,
  this is a durability superpower. `setup.py` declares only `python_requires>=3.6`
  and nothing else; the Python 3.6..3.12 classifier list lines up with
  what actually runs.

### Structural concerns

- **(S) `Serializable` is cute but fragile.** `wildcatting/model/serialize.py`
  hand-rolls an encoder that (a) excludes any attribute containing `"__"`
  and (b) re-hydrates by calling `getattr(wildcatting.model, clsname)`.
  The `"__"` substring test is load-bearing — it is literally what keeps
  reservoir data from leaking to clients — but it's invisible from the
  callsites and has no tests that assert "this field must not reach the
  client". A rename like `_potential_oil_depth` → `__potential_oil_depth`
  is currently how we enforce privacy, which is the wrong shape for a
  security boundary.
  - **Suggestion:** replace with an explicit `_serialize_fields` allow-list
    per class, and assert the exclusion in `test_model_serialize.py`.
- **(S) ~~Stringly-typed RPC vocabulary.~~** **(RESOLVED)** All `assert
  isinstance`/`assert re.match` calls in `server.py` and `game.getPlayer`
  replaced with `if not ... raise WildcattingException(...)`.  Base64
  decode errors also caught and raised as `WildcattingException` rather
  than leaking a raw `binascii.Error`.
- **(M) God-object in `game.py`.** `game.py` owns five different `Filler`
  classes, the `Game` aggregate, and the random-ID generation. The filler
  hierarchy could live in its own module (`wildcatting/generation.py`) and
  be testable without instantiating a whole `Game`. `Game._generateSecret`
  is duplicated logic with the 16-hex-char client id generator — both
  should live in one place. **(PARTIALLY RESOLVED)** `_generateSecret` now
  uses `secrets.token_hex(8)` — the alphabet-list `random.choice` loop is gone.
- **(M) Coupling between client and server packages.** `ClientCommand`
  imports `wildcatting.server.StandaloneServer`, which itself pulls in
  `wildcatting.theme`. In practice, shipping a "client-only" wheel is
  impossible: any client install drags the whole server in. That's fine
  for today's single-package setup but worth knowing if someone wants to
  ship a slim client later.
- **(M) Java-style getters/setters everywhere.** This is a stylistic
  choice that has a real cost: every model class has a dozen
  `getX`/`setX` pairs and no `@property`/dataclass usage. It makes the
  code look much larger than it is. `Site`, `Well`, `Player`, `Week`,
  `Turn`, `Update`, etc., are all candidates for `@dataclass` conversion
  (they'd keep the same serialized shape if you use underscored names).
- **(N) `OilField.week` mutates state deep in a for-loop** rather than
  returning a diff. That's fine as an authoritative mutation, but the
  update-tracking side (`Game.markSiteUpdated`) is a parallel mechanism
  that has to be remembered any time a site mutates. A central "site
  mutator" would reduce the chance of future drift.
- **(N) `WildcattingException` is the only exception type.** Anything
  that can go wrong — bad handle, wrong turn, duplicate name, already
  sold — is a bare string in a single exception class, which the client
  then pretty-much treats as "something happened on the server". Typed
  subclasses would help clients react better (e.g., highlight the field
  rather than show a generic error).

### Things that age well

- The move away from Python 2 (`ef61e1f`, `d1532df`) landed without a
  rewrite, which tells me the abstractions were already reasonable.
- `Week`, `Turn`, and `Player` are small, focused, and easy to read.
- The `xmlrpc.server` / `xmlrpc.client` pair is still in the Python
  standard library and remains a legitimate choice for a
  low-throughput LAN game. No need to chase HTTP/JSON for its own sake.

---

## Persona 2 — Security Engineer

The threat model here is: LAN party, semi-trusted peers, no internet
exposure. Almost everything below is fine under that assumption and
dangerous outside it. I'm calling out what changes if this ever gets
exposed to a WAN.

### Transport and handshake

- **(S) No transport security.** `TieredXMLRPCServer` binds plain HTTP
  (`SimpleXMLRPCServer`). Handles traverse the wire unencrypted. Anyone
  on the same segment can sniff `join` and replay `survey`/`drill`/`sell`
  on behalf of another player. Acceptable for a LAN game; **do not
  expose this server to the internet as-is**.
- **(S) `server.py` does not set `bind_and_activate` or a host allowlist**.
  Default `ServerCommand` binds `""` which is `0.0.0.0` on both IPv4 and
  IPv6. Combined with the above, any reachable client can `new` a game
  or `ping` your server. No resource limits.
- **(M) Version mismatch is treated as fatal at the client** but the
  server doesn't care — a malicious client can still lie about its
  version. `BaseService.version()` is unauthenticated (correctly).

### Authentication / authorization

- **(S) ~~Bearer-token handles with no revocation.~~** **(RESOLVED)**
  `Game._generateSecret` now uses `secrets.token_hex(8)` — Mersenne
  Twister is gone from the auth path.
- **(S) ~~`assert`-based auth.~~** **(RESOLVED)** All `assert`-based
  validation in the RPC path replaced with `WildcattingException`.
  See Staff eng finding above.
- **(M) No rate limiting.** `GameService.new` will gladly allocate a new
  80×24 oil field with five probability fields worth of floating-point
  work for every caller; a tight loop of `new` calls would exhaust
  server memory.
- **(M) Username uniqueness check is case-sensitive and by string
  equality.** `alice` and `Alice` are different players — might surprise
  a user who expected to reconnect with a slightly different case.
- **(N) Game master is whoever joined first.** That is an elegant
  solution — no additional authentication for the "start the game"
  action. It falls out of player order. Worth preserving in any
  auth rewrite.

### Data at rest / in flight

- **(S) Pickle-ish custom serializer + dynamic `getattr` on classes.**
  `Serializable.deserialize` resolves `clsname` by
  `getattr(wildcatting.model, clsname)` and then calls `cls.__new__(cls)`
  with attacker-controlled dict state. The search scope is narrow
  (`wildcatting.model`) so this isn't "pickle RCE" — but a crafted
  payload could instantiate a `Well` or `Player` with bogus private
  state, and any code downstream that trusts `isinstance` but not
  invariants is vulnerable. The `deserialize()` path is called on both
  the server and the client for all RPC responses, so both sides can
  be poisoned.
  - **Fix:** validate the class name against an allow-list and call a
    real `__init__`-equivalent that enforces invariants.
- **(M) `xmlrpc.client` with `allow_none=True` is fine** but combined
  with introspection functions (`register_introspection_functions()`)
  it exposes `system.methodHelp`, `system.listMethods`, etc., to any
  caller. On a closed LAN this is convenient; on an open network it's a
  mapping tool for attackers.
- **(N) The historical price dataset** in `oilprices.py` is ~275 KB of
  inlined Python data — not a security issue, but worth auditing as part
  of any supply-chain review (you wouldn't want a future contribution to
  sneak a surprise in there).

### Client side

- **(N) `os.path.exists("/mach_kernel")` as a Mac detector.** Cute, but
  dead since OS X 10.10. It always returns `False` on modern macOS; no
  security impact, it's just a mis-detection that makes the Mac-specific
  workaround branch unreachable.
- **(N) `os.environ.get("COLUMNS", 80) - 5`** in `ClientCommand` —
  `COLUMNS` is a string if set, which would throw `TypeError`. In
  practice the env var is rarely set, so the crash never fires. Noted.

### Recommendations (ranked)

1. Replace all `assert isinstance`/`assert re.match` in `server.py`
   with real validation. This is load-bearing security code.
2. Move random IDs from `random` to `secrets`.
3. Allow-list class names in `Serializable.deserialize`.
4. Disable `register_introspection_functions()` unless you genuinely
   want it.
5. Document the LAN-only assumption in the README explicitly.

---

## Persona 3 — Site Reliability Engineer

### Server runtime

- **(S) Single-threaded, synchronous RPC.** `SimpleXMLRPCServer.serve_forever()`
  handles one request at a time. Fine for 2–4 players; a `new` call that
  allocates a big field can pause every other client. `ThreadingMixIn`
  would help, but then `Game` state needs a lock — it's currently
  touched with zero synchronization. Right now, a single slow `getUpdate`
  will stall surveying for everyone.
- **(S) No graceful shutdown / state persistence.** The process holds all
  game state in memory; a `SIGTERM` or crash loses every in-flight game.
  `Client.run()` at least catches `KeyboardInterrupt` and prints a
  reconnect hint, but the server it's connecting to has no way to
  honor it after a restart. Consider a "pickle to disk on interval"
  or just write the current `Game` dict via the existing `Serializable`
  machinery on `endTurn`.
- **(M) No health endpoints beyond `admin.ping`.** `/healthz` and a
  per-game-count metric would be cheap. For small numbers of games,
  `GameService._games` is the answer to "how many active games?" — but
  there is no RPC exposing it.
- **(M) No request logging.** The server logs via `XMLRPCServer` only
  when `_dispatch` throws. Successful calls are invisible in the log
  file. A line per call (method, elapsed, caller) would pay for itself
  the first time a bug report shows up.

### Client polling behavior

- **(N) Exponential backoff is implemented but never backs off
  downward.** `Client.wildcatting()` doubles `refresh` when a poll
  exceeds the current interval, then resets it to `origRefresh` on the
  next local action. This is correct for the "my turn, force a fast
  tick" path, but between turns it monotonically widens — on a flaky
  network two clients can end up minutes out of sync. A simple AIMD
  (additive-increase multiplicative-decrease) would even it out.
- **(M) Halfdelay value `50` is in deciseconds** — that's 5 seconds.
  Turn handoff latency is therefore up to ~5s even on a LAN. This is
  the pragmatic floor for "non-active clients waiting for a turn" but
  it's invisible from the main loop. A comment explaining the unit
  exists (`# Measured in deciseconds. Thanks, curses.`) which is the
  right level of documentation for this sort of trap.

### Observability

- **(S) ~~Logging is file-based with no rotation.~~** **(RESOLVED)**
  `startLogger` now uses `RotatingFileHandler` (10 MB, 3 backups).
- **(M) Log level is flipped between the root logger and handlers** —
  root is `DEBUG`, file is `DEBUG`, console is `ERROR`. Adding `--debug`
  at the CLI flips root from `ERROR` to `DEBUG`, which then overrides
  the handler levels. Works, but non-obvious. A standard `logging.config`
  dict would be clearer.
- **(M) No metrics at all.** For a game server this is fine, but a
  single Prometheus counter on turn/survey/drill would be informative
  enough to justify adding a `prometheus_client` dep if anyone ever
  decides to host it.

### Capacity

- Field generation is `O(width × height × peaks)` times several fillers.
  At the default 80×24 with maxPeaks=5, that's ~10k cell visits per
  filler × 5 fillers ≈ 50k — well under a millisecond in CPython.
  No concern. The ReservoirFiller's adjacency pass is O(n) with small
  constants.
- `getWellUpdates` is O(width × height) every `endTurn`. Fine at tabletop
  scale.

### Deployment

- **(M) ~~`setup.py` doesn't declare console-script entry points.~~**
  **(RESOLVED)** Replaced `setup.py` with `pyproject.toml` (hatchling).
  `go-wildcatting` is now registered via `[project.scripts]` pointing to
  `wildcatting.cli:main`.
- **(M) ~~`test/suite` being a script in `setup.py`~~** **(RESOLVED)**
  `test/suite` has been deleted. Tests run via
  `uv run python -m unittest discover test/`.

### Recommendations

1. Add a JSON `dump` / `load` of `GameService._games` on a timer, keyed
   by gameId — survival across restarts.
2. Wrap handlers with a `time.monotonic()` log of method + elapsed.
3. Add rotating log handlers.
4. Switch to `entry_points` in `setup.py`.

---

## Persona 4 — QA / Test Engineer

### Coverage gaps

- **(S) Zero curses coverage.** None of the view classes has a test.
  This is normal for curses code but not inevitable — a test harness
  that feeds stub key codes into `wildcattingView.input()` and asserts
  on the resulting action dict would catch regressions in the turn
  state machine.
- **(S) ~~No serializer exclusion test.~~** **(RESOLVED)** `test_information_hiding.py`
  asserts that `oilFlag` and reservoir internals never appear in any
  serialized output, including after game end when all sites are revealed.
- **(M) ~~No price-walk test.~~** **(RESOLVED)** `test_reservoir.py`
  verifies `GaussianPrices` never drops below the `$0.01` floor under
  extreme downward pressure. `test_stochastic.py` verifies prices are
  always positive over 100 ticks of the default `TrendingGaussianPrices`.
- **(M) ~~No "game end" test.~~** **(RESOLVED)** `test_stochastic.py`
  runs a complete multi-week game to `isFinished()` and verifies the
  lifecycle terminates correctly.
- **(M) `test_gameservice.py` relies on real RNG** through
  `DefaultTheme()`. Tests like `testDrilling` iterate "while
  output is None and depth < 10" — if an adversarial seed ever caused
  an infinite loop it would wedge the suite rather than fail. Seeding
  `random` at the top of each test would both speed it up and make
  failures deterministic.

### Tooling

- **(S) ~~No `pyproject.toml`, no lockfile.~~** **(PARTIALLY RESOLVED)**
  `pyproject.toml` (hatchling) and `uv.lock` are now in place; tests
  run via `uv run python -m unittest discover test/`. CI and a linter
  are still missing.
- **(S) No linter / type checker.** `ruff`, `mypy --strict`, or even
  `pyflakes` would fire on things like `Well.__eq__` referencing
  `self._turn` (which is never set anywhere in `Well.__init__`). That
  method is dead but is also a time bomb if someone puts a `Well`
  in a set.
- **(M) Tests and code live in different import roots.** `test/` is a
  sibling of `wildcatting/` and tests are discovered by a custom
  `test/suite`. Moving to `pytest` with `tests/` would be a small,
  standard change.

### Specific bugs / smells worth writing tests for

- **(S) ~~`Well.__eq__` / `__lt__` reference `self._turn`~~**
  **(RESOLVED)** Both methods now reference `self._week`. `__hash__`
  was also added so Wells remain usable in sets and dicts.
- **(S) ~~`GameService.drill` calls `game.markSiteUpdated(player, drilledSite)`~~**
  **(RESOLVED)** `drill` now looks up the site from the oil field after
  drilling and passes that to `markSiteUpdated`, so `None` can no longer
  be queued into client update lists. A related bug in `Game.markSiteUpdated`
  — comparing `player.getUsername()` against a list of `Player` objects —
  was already resolved previously.
- **(M) `Reservoir.pump` asserts `0 <= barrels < self._reserves`.**
  With a strict `<`, pumping exactly the remaining reserves (which
  `SimpleWellTheory` caps at `reserves / 2` — unreachable in practice
  but assertable) would throw `AssertionError`. Asserts for invariants
  are fine, but a proper test would pin the boundary behavior.
- **(M) `ReservoirFiller._fillSite` has a branch that re-creates a
  single-cell reservoir** in the "else" path, but overwrites any
  previous reservoir the site already had. Small players will
  occasionally get this visible as wildly mismatched reserves on
  adjacent hits.
- **(N) `OilField.getSite` asserts row/col bounds.** With `-O` stripped
  off, an out-of-range query becomes an `IndexError` instead of an
  `AssertionError`. Either is ugly for a network-reachable method.

### Recommended test additions

1. Round-trip serialization test with explicit deny-list:
   ```python
   raw = site.serialize()
   assert "_Site__reservoir" not in json.dumps(raw)
   ```
2. Deterministic seed fixture for all `GameService` tests.
3. Snapshot test of `SettingService.getSetting()` for the default theme.
4. `test_week.py` expansion: survey order with a player who joins late
   doesn't actually exist, since joins lock at `Game.start()` — worth
   an explicit test so that behavior is documented.

---

## Persona 5 — Game Designer / Product

### What the game gets right

- **(N) Readable feedback loops.** Survey → drill → sell is a clean
  three-step decision with visible cost. The week rollup and the
  price ticker above the field are enough context for a player to
  feel in control without being overwhelmed.
- **(N) Hidden information done well.** The reservoir layer, tax per
  site, and the eventual oil depth are authentically hidden from the
  player and revealed only through committed action. That's the
  right shape for a speculation game.
- **(N) Flavor density.** The `_rawFacts` corpus and the Spindletop
  README intro are a huge part of the game's charm — this is a theme
  that rewards reading, and the architecture (`Theme.getFacts()`,
  drawn in the border) makes it trivial to swap.

### What I'd push on

- **(S) The win condition is implicit.** `_finish` sorts by
  `getProfitAndLoss()` and logs scores, and the client runs a final
  animation — but players never see an explicit "game over, Alice
  wins with $12,430" screen that compares them. The weekly summary
  view is available, but scoring is not clearly communicated.
- **(S) Player agency on well **management** is thin.** After drilling,
  the only lever is when to sell. There is no "expand capacity",
  "cap the well", "maintenance", or "recondition" action, even though
  `Well.capacity` exists and `SimpleWellTheory` already simulates
  ramp-up. A "pay to increase capacity" action would reuse existing
  math.
- **(M) Drill depth is hard-capped at 10** in `Well.drill` with a raw
  constant, and the "dry hole" sleep is 3 seconds (`time.sleep(3)`) —
  both should be theme-configurable for difficulty tuning.
- **(M) No visible risk curve before drilling.** Players see probability
  and drill cost but not a projected breakeven. A simple
  "at $X/barrel you need N barrels to break even" number in
  `DrillView` would make the drilling decision more strategic and
  less vibes-based.
- **(M) Turn-based multiplayer means a slow player blocks the table.**
  `Week.isSurveyTurn` enforces strict ordering during the survey
  phase. A timeout ("if you don't act in 60s we end your turn")
  would rescue dropped-connection games. Currently the only recovery
  is "kill the server".
- **(N) Taxation is flat and random per site.** That's a fine
  simplification, but taxes never change, so players who happen to
  drill cheap-tax sites snowball. Making tax drift with oil price
  (higher prices → higher rates) is free thematic tension.
- **(N) Screensaver mode is a great marketing asset** and almost
  nothing else in the repo markets itself. A README screenshot would
  be worth more than all the refactoring in this doc.

---

## Persona 6 — Python Modernization Reviewer

The repo was ported from Python 2 (`e5a26b9`) and then fixed for float
division (`ef61e1f`). That porting was mechanical — it did not modernize.
Here's what a cleanup pass could adopt without changing behavior.

### Language features the code could adopt

- **(S) `dataclasses`** for `Site`, `Well`, `Player`, `Update`,
  `Reservoir`, `Setting`, `ClientInfo`, `WeeklySummary`. Currently
  every one of these is hand-rolled getters/setters. A `@dataclass`
  (or `@dataclass(kw_only=True, slots=True)`) would shrink each class
  to its state shape plus any real behavior.
- **(S) `typing`.** No type hints anywhere. Even a partial pass would
  catch the `Well.__eq__ → self._turn` bug at import time (via `mypy`).
- **(S) `secrets.token_hex`** instead of `random.choice` over a literal
  hex alphabet.
- **(S) `enum.Enum` or `StrEnum`** for client actions like `"survey"`,
  `"drill"`, `"stop"`, `"sell"`, `"nextPlayer"`, `"checkForUpdates"`.
  Right now these are bare strings in dicts passed between view and
  client, with no single source of truth.
- **(M) `pathlib`** for file paths; `startLogger` uses plain strings
  which is fine, but `ScreensaverCommand` and friends resolve paths
  manually.
- **(M) `argparse`** in place of `optparse` + `cmdparse.py`. The
  `optparse` module is deprecated since Python 3.2 and `cmdparse.py`
  is ~170 lines of custom subparser code. `argparse` subparsers solve
  the same problem natively. `shlex`/`importlib.metadata` can replace
  the `dir(module)`-based command discovery.
- **(M) ~~`functools.cmp_to_key`~~** **(RESOLVED)** `Game._finish` now uses
  `sorted(players, key=lambda p: -p.getProfitAndLoss())`.
- **(N) f-strings** everywhere the code uses `%` formatting. Cosmetic,
  but the current state mixes `%` and `"{}".format` inconsistently.
- **(N) `dict.setdefault`** uses are fine but `collections.defaultdict`
  would read more naturally for `_clientUpdates`.

### Packaging

- **(S) ~~`setup.py` only~~** **(RESOLVED)** — replaced with
  `pyproject.toml` using the hatchling build backend. `uv.lock` committed
  for reproducible installs.
- **(M) ~~`scripts=["go-wildcatting", "test/suite"]`~~** **(RESOLVED)**
  — `go-wildcatting` is now `wildcatting.cli:main` registered via
  `[project.scripts]`. `test/suite` deleted.
- **(M) ~~`python_requires=">=3.6"`~~** **(RESOLVED)** — floor raised to
  `>=3.11`.

### Small corrections

- **`optparse` import** (`cmdparse.py:4`) will start emitting
  `DeprecationWarning: The optparse module is deprecated` in 3.12 and
  is slated for removal in a future version. Plan the migration now.
- **`xmlrpc.server.SimpleXMLRPCServer`** is fine but the `allow_none`
  constructor argument is passed via `kwargs["allow_none"] = True`,
  which stomps any caller-supplied value; prefer a default arg.
- **`os.environ.get("USER")`** (`ClientCommand.py:20`) returns `None`
  on Windows where `USERNAME` is the right variable. Not a
  correctness bug because of the fallback to `"none"`, but a Windows
  user will have their well symbol be `N`, not their initial.
- **`"".join([random.choice((...)) for i in range(0, 16)])`**
  (`game.py:269`) is a classic port-from-Py2 generator-expression
  miss — the inner list is unnecessary.

### Unused / dead

- **~~`Well.__eq__` / `__lt__`~~** referencing `self._turn` — **(RESOLVED)** corrected to `self._week`; `__hash__` added.
- **~~`SimpleWellTheory.__str__`~~** **(RESOLVED)** now returns a real string.
- **~~`os.path.exists("/mach_kernel")`~~** **(RESOLVED)** Dead branch
  removed from `View`, `setFGBG`, and `ColorChooser`; also fixed a
  latent bug in `setFGBG` where the non-Mac path called `self._win.clear()`
  instead of `win.clear()`.
- **`wildcatting.colors.Colors`** is imported into
  `wildcatting.client` but not used in that module (only in view
  modules). Minor cleanup.

---

## Summary table

| Finding                                                 | Persona             | Severity | Status    |
|---------------------------------------------------------|---------------------|----------|-----------|
| Assert-based input validation stripped by `-O`          | Staff eng, Security | S        | **fixed** |
| `random.choice` for auth secrets                        | Security            | S        | **fixed** |
| `Serializable.deserialize` dynamic class lookup         | Security, Staff eng | S        | open      |
| Hidden-field exclusion by `"__"` substring              | Staff eng           | S        | open      |
| `Well.__eq__` references non-existent `self._turn`      | QA, Modernization   | S        | **fixed** |
| `Game.markSiteUpdated` username vs Player comparison    | QA                  | S        | **fixed** |
| `Game.sell()` dead code with defects                    | QA                  | S        | **fixed** |
| `GameService.drill` passes `None` to `markSiteUpdated`  | QA                  | S        | **fixed** |
| Single-threaded server, no persistence                  | SRE                 | S        | open      |
| Log files unrotated                                     | SRE                 | S        | **fixed** |
| No CI / lint / type checking                            | QA                  | S        | open      |
| `Serializable` exclusion has no test                    | QA                  | S        | **fixed** |
| Dataclasses / type hints                                | Modernization       | S        | open      |
| Turn-based multiplayer has no timeout                   | Game design         | S        | open      |
| Win condition / scoreboard not shown to player          | Game design         | S        | open      |
| Player agency on well management is thin                | Game design         | S        | open      |
| `setup.py` only, no `pyproject.toml` or lockfile        | SRE, Modernization  | M        | **fixed** |
| `scripts=` uses legacy keyword; `test/suite` in bin/    | SRE, Modernization  | M        | **fixed** |
| `python_requires` too low                               | Modernization       | M        | **fixed** |
| `argparse` replaces `optparse` + `cmdparse.py`          | Modernization       | M        | open      |
| `Game._finish` uses `cmp_to_key`                        | Modernization       | M        | **fixed** |
| `optparse` is deprecated in 3.12                        | Modernization       | M        | open      |
| Drill depth / dry-hole sleep hardcoded                  | Game design         | M        | open      |
| No health endpoint / request logs                       | SRE                 | M        | open      |
| Dead Mac detection                                      | Modernization       | N        | **fixed** |
| `SimpleWellTheory.__str__` returns None                 | Modernization       | N        | **fixed** |

---

## A suggested rework ordering

If someone wanted to modernize this in a week without rewriting game
logic, the defensible order is:

1. **Day 1** — *(partially complete)* `pyproject.toml` with hatchling,
   `[project.scripts]` entry point, `uv.lock`, Python floor to 3.11,
   and a 31-test safety-net suite covering financial invariants, reservoir
   bounds, information hiding, and end-to-end game flow. Still missing:
   GitHub Actions CI, linter, type checker.
2. **Day 2** — Replace asserts with real exceptions in `server.py`;
   swap `random` for `secrets`; add allow-list to
   `Serializable.deserialize`; add a negative test for reservoir
   leakage.
3. **Day 3** — Type hints on the model package; convert `Site`, `Well`,
   `Player`, `Update`, `Setting` to dataclasses; `mypy` clean.
4. **Day 4** — SRE: rotating log handler, request-timing log wrapper,
   persist `GameService._games` on `endTurn`, reconnect path proven.
5. **Day 5** — Game design: explicit final scoreboard view, turn
   timeout, theme-configurable drill cap. Leave the rest as tickets.

Everything else in this document is worth doing but is not load-bearing.
