#!/usr/bin/env python
#
# tournament.py -- implementation of a Swiss-system tournament
#

from itertools import islice

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
