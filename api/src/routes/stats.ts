import { Hono } from 'hono';
import type { Env } from '../types';

const stats = new Hono<{ Bindings: Env }>();

// GET /api/v1/stats — global stats
stats.get('/', async (c) => {
  const [trackCount, genreCount, featureAvgs, topGenres] = await Promise.all([
    c.env.DB.prepare(`SELECT COUNT(*) as total FROM tracks`).first<{ total: number }>(),
    c.env.DB.prepare(`SELECT COUNT(*) as total FROM genres`).first<{ total: number }>(),
    c.env.DB.prepare(`
      SELECT
        ROUND(AVG(tempo), 2) as avg_tempo,
        ROUND(AVG(energy), 3) as avg_energy,
        ROUND(AVG(valence), 3) as avg_valence,
        ROUND(AVG(loudness), 2) as avg_loudness,
        ROUND(AVG(acousticness), 3) as avg_acousticness,
        ROUND(AVG(danceability), 3) as avg_danceability,
        ROUND(AVG(instrumentalness), 3) as avg_instrumentalness,
        ROUND(AVG(speechiness), 3) as avg_speechiness,
        ROUND(AVG(liveness), 3) as avg_liveness
      FROM tracks
    `).first(),
    c.env.DB.prepare(`
      SELECT id, name, track_count
      FROM genres
      ORDER BY track_count DESC
    `).all(),
  ]);

  return c.json({
    data: {
      totals: {
        tracks: trackCount?.total ?? 0,
        genres: genreCount?.total ?? 0,
      },
      global_averages: featureAvgs,
      genres: topGenres.results,
    },
  });
});

export default stats;
