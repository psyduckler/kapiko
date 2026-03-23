-- kapiko Music Intelligence API — D1 Schema

CREATE TABLE IF NOT EXISTS genres (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  track_count INTEGER DEFAULT 0,
  avg_tempo REAL,
  avg_energy REAL,
  avg_valence REAL,
  avg_loudness REAL,
  avg_acousticness REAL,
  avg_danceability REAL,
  avg_instrumentalness REAL,
  avg_speechiness REAL,
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tracks (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  artists TEXT,
  album TEXT,
  genre_id TEXT REFERENCES genres(id),
  popularity INTEGER,
  duration_ms INTEGER,
  tempo REAL,
  energy REAL,
  valence REAL,
  loudness REAL,
  acousticness REAL,
  danceability REAL,
  instrumentalness REAL,
  speechiness REAL,
  liveness REAL,
  key INTEGER,
  mode INTEGER,
  time_signature INTEGER,
  source TEXT DEFAULT 'spotify',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre_id);
CREATE INDEX IF NOT EXISTS idx_tracks_energy ON tracks(energy);
CREATE INDEX IF NOT EXISTS idx_tracks_tempo ON tracks(tempo);
CREATE INDEX IF NOT EXISTS idx_tracks_popularity ON tracks(popularity DESC);
