#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

from itertools import islice, combinations
from random import shuffle

import psycopg2
import bleach


class DatabaseContext():
    def __init__(self, connect):
        self.db = connect()

    def __enter__(self):
        return self.db

    def __exit__(self, *_):
        self.db.commit()
        self.db.close()

    def __call__(self):
        return self.db


@DatabaseContext
def connect():
    """Connect to the PostgreSQL database.  Returns a database connection."""
    return psycopg2.connect("dbname=tournament")


def deleteMatches():
    """Remove all the match records from the database."""
    with connect() as db:
        c = db.cursor()
        c.execute("UPDATE standings SET wins = 0, matches = 0;")


def deletePlayers():
    """Remove all the player records from the database."""
    with connect() as db:
        c = db.cursor()
        c.execute("DELETE FROM standings;")


def countPlayers():
    """Returns the number of players currently registered."""
    with connect() as db:
        c = db.cursor()
        c.execute("SELECT count(*) FROM standings;")
        (count,) = c.fetchone()
        return count


def registerPlayer(name):
    """Adds a player to the tournament database.

    The database assigns a unique serial id number for the player.  (This
    should be handled by your SQL database schema, not in your Python code.)

    Args:
      name: the player's full name (need not be unique).
    """
    with connect() as db:
        c = db.cursor()
        c.execute("INSERT INTO standings (name) VALUES(%s);",
                  [bleach.clean(name)])


def playerStandings():
    """Returns a list of the players and their win records, sorted by wins.

    The first entry in the list should be the player in first place, or a
    player tied for first place if there is currently a tie.

    Returns:
      A list of tuples, each of which contains (id, name, wins, matches):
        id: the player's unique id (assigned by the database)
        name: the player's full name (as registered)
        wins: the number of matches the player has won
        matches: the number of matches the player has played
    """
    with connect() as db:
        c = db.cursor()
        c.execute("SELECT * FROM standings ORDER BY wins DESC;")
        return c.fetchall()


def reportMatch(winner, loser):
    """Records the outcome of a single match between two players.

    Args:
      winner:  the id number of the player who won
      loser:  the id number of the player who lost
    """
    with connect() as db:
        c = db.cursor()
        c.execute(
            "UPDATE standings SET wins = wins + 1, matches = matches + 1"
            "WHERE id = {};".format(winner))
        c.execute(
            "UPDATE standings SET matches = matches + 1"
            "WHERE id = {};".format(loser))


def swissPairings():
    """Returns a list of pairs of players for the next round of a match.

    Assuming that there are an even number of players registered, each player
    appears exactly once in the pairings.  Each player is paired with another
    player with an equal or nearly-equal win record, that is, a player adjacent
    to him or her in the standings.

    Returns:
      A list of tuples, each of which contains (id1, name1, id2, name2)
        id1: the first player's unique id
        name1: the first player's name
        id2: the second player's unique id
        name2: the second player's name
    """
    with connect() as db:
        c = db.cursor()
        c.execute("SELECT id, name FROM standings ORDER BY wins DESC;")
        players = c.fetchall()

        # match up item in players with the item after it
        pairs = ((id1, name1, id2, name2)
                 for ((id1, name1), (id2, name2))
                 in zip(players, players[1:]))

        # skip every second item in the list to avoid duplicate pairs.
        return list(islice(pairs, 0, None, 2))

def round_robin(players):
    deletePlayers()

    for name in players:
        registerPlayer(name)

    with connect() as db:
        c = db.cursor()
        c.execute("SELECT id FROM standings;")
        ids = [x[0] for x in c.fetchall()]

    for pair in map(list, combinations(ids, 2)):
        shuffle(pair)
        reportMatch(*pair)


def custom_tournament(players, num_rounds):
    """Theorem: If there are P players, where P is odd, and N rounds, where N
    is odd, then it is impossible to pair up players such that they all play N
    rounds against each other.

    Proof: Assume for sake of contradiction that such a pairing existed. Then
    since each player played N rounds, N * P is double the number of total
    rounds played. (Since if player i plays x rounds with player j rounds, that
    is counted to the total, but player j's x rounds with player i is also
    counted to the total. However N * P is odd since N and P where initially
    odd. So N * P is not divisible by two. A contradiction. QED
    """
    deletePlayers()

    for name in players:
        registerPlayer(name)

    with connect() as db:
        c = db.cursor()
        c.execute("SELECT id FROM standings;")
        ids = [x[0] for x in c.fetchall()]

    if len(ids) % 2 == 0:
        even_players(ids, num_rounds)
    elif num_rounds % 2 == 0:
        even_rounds(ids, num_rounds)
    else:
        print("impossible to arrange such a tournament")


def even_players(ids, num_rounds):
    mid = len(ids) // 2
    for _ in range(num_rounds):
        shuffle(ids)
        for pair in zip(ids[:mid], ids[mid:]):
            reportMatch(*pair)


def even_rounds(ids, num_rounds):
    for _ in range(num_rounds // 2):
        shuffle(ids)
        for pair in map(list, zip(ids, ids[1:] + ids[:1])):
            shuffle(pair)
            reportMatch(*pair)

print("EVEN PLAYERS")
custom_tournament("ABCDEFGHIJ", 3)
print(playerStandings())
print("EVEN ROUNDS")
custom_tournament("ABCDEFGHI", 4)
print(playerStandings())
print("ODD")
custom_tournament("ABC", 3)
print("ROUND ROBIN")
round_robin("ABCDE")
print(playerStandings())
