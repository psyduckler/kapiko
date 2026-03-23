import { Hono } from 'hono';
import type { Env, FeatureComparison } from '../types';

const compare = new Hono<{ Bindings: Env }>();

function percentileLabel(delta: number | null, feature: string): string {
  if (delta === null) return 'unknown';
  const isLoudness = feature === 'loudness';
  // loudness is negative — smaller delta means louder
  const normalizedDelta = isLoudness ? -delta : delta;
  if (normalizedDelta > 0.15) return 'above average';
  if (normalizedDelta < -0.15) return 'below average';
  return 'near average';
}

function compareFeature(
  trackVal: number | null,
  genreAvg: number | null,
  feature: string
): FeatureComparison {
  const delta = trackVal !== null && genreAvg !== null ? trackVal - genreAvg : null;
  return {
    track_value: trackVal,
    genre_avg: genreAvg,
    delta,
    percentile_label: percentileLabel(delta, feature),
  };
}

// GET /api/v1/compare?track_id=...&genre=...
compare.get('/', async (c) => {
  const trackId = c.req.query('track_id');
  const genreId = c.req.query('genre');

  if (!trackId) {
    return c.json({ error: 'Missing required query param: track_id', status: 400 }, 400);
  }
  if (!genreId) {
    return c.json({ error: 'Missing required query param: genre', status: 400 }, 400);
  }

  const [track, genre] = await Promise.all([
    c.env.DB.prepare(`SELECT * FROM tracks WHERE id = ?`).bind(trackId).first(),
    c.env.DB.prepare(`SELECT * FROM genres WHERE id = ?`).bind(genreId.toLowerCase()).first(),
  ]);

  if (!track) {
    return c.json({ error: 'Track not found', status: 404 }, 404);
  }
  if (!genre) {
    return c.json({ error: 'Genre not found', status: 404 }, 404);
  }

  const t = track as Record<string, number | null | string>;
  const g = genre as Record<string, number | null | string>;

  const result = {
    track,
    genre,
    comparison: {
      tempo: compareFeature(t.tempo as number | null, g.avg_tempo as number | null, 'tempo'),
      energy: compareFeature(t.energy as number | null, g.avg_energy as number | null, 'energy'),
      valence: compareFeature(t.valence as number | null, g.avg_valence as number | null, 'valence'),
      loudness: compareFeature(t.loudness as number | null, g.avg_loudness as number | null, 'loudness'),
      acousticness: compareFeature(t.acousticness as number | null, g.avg_acousticness as number | null, 'acousticness'),
      danceability: compareFeature(t.danceability as number | null, g.avg_danceability as number | null, 'danceability'),
      instrumentalness: compareFeature(t.instrumentalness as number | null, g.avg_instrumentalness as number | null, 'instrumentalness'),
      speechiness: compareFeature(t.speechiness as number | null, g.avg_speechiness as number | null, 'speechiness'),
    },
  };

  return c.json({ data: result });
});

export default compare;
