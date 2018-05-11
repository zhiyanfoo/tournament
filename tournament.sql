-- Table definitions for the tournament project.
--
-- Put your SQL 'create table' statements in this file; also 'create view'
-- statements if you choose to use it.
--
-- You can write comments in this file by starting them with two dashes, like
-- these lines here.

DROP DATABASE IF EXISTS tournament;

CREATE DATABASE tournament;

\c tournament;

CREATE TABLE standings (
    id SMALLSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    wins SMALLINT DEFAULT 0,
    matches SMALLINT DEFAULT 0);
