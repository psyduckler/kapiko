import { Hono } from 'hono';
import type { Env } from '../types';

const genres = new Hono<{ Bindings: Env }>();

// GET /api/v1/genres — list all genres with summary stats
genres.get('/', async (c) => {
  const results = await c.env.DB.prepare(
    `SELECT * FROM genres ORDER BY track_count DESC`
  ).all();

  return c.json({
    data: results.results,
    meta: { total: results.results.length },
  });
});

// GET /api/v1/genres/:genre — detailed genre analytics
genres.get('/:genre', async (c) => {
  const genreId = c.req.param('genre').toLowerCase();

  const genre = await c.env.DB.prepare(
    `SELECT * FROM genres WHERE id = ?`
  ).bind(genreId).first();

  if (!genre) {
    return c.json({ error: 'Genre not found', status: 404 }, 404);
  }

  // Fetch distribution data for charts
  const energyBuckets = await c.env.DB.prepare(`
    SELECT
      CAST(ROUND(energy * 10) AS INTEGER) * 10 AS bucket,
      COUNT(*) AS count
    FROM tracks
    WHERE genre_id = ? AND energy IS NOT NULL
    GROUP BY bucket
    ORDER BY bucket
  `).bind(genreId).all();

  const tempoBuckets = await c.env.DB.prepare(`
    SELECT
      CAST(ROUND(tempo / 20) * 20 AS INTEGER) AS bucket,
      COUNT(*) AS count
    FROM tracks
    WHERE genre_id = ? AND tempo IS NOT NULL AND tempo > 0
    GROUP BY bucket
    ORDER BY bucket
  `).bind(genreId).all();

  const valenceBuckets = await c.env.DB.prepare(`
    SELECT
      CAST(ROUND(valence * 10) AS INTEGER) * 10 AS bucket,
      COUNT(*) AS count
    FROM tracks
    WHERE genre_id = ? AND valence IS NOT NULL
    GROUP BY bucket
    ORDER BY bucket
  `).bind(genreId).all();

  const topArtists = await c.env.DB.prepare(`
    SELECT artists, COUNT(*) as track_count
    FROM tracks
    WHERE genre_id = ?
    GROUP BY artists
    ORDER BY track_count DESC
    LIMIT 10
  `).bind(genreId).all();

  return c.json({
    data: {
      genre,
      distributions: {
        energy: energyBuckets.results,
        tempo: tempoBuckets.results,
        valence: valenceBuckets.results,
      },
      top_artists: topArtists.results,
    },
  });
});

// GET /api/v1/genres/:genre/tracks — paginated tracks in genre
genres.get('/:genre/tracks', async (c) => {
  const genreId = c.req.param('genre').toLowerCase();
  const limit = Math.min(parseInt(c.req.query('limit') ?? '20'), 100);
  const offset = parseInt(c.req.query('offset') ?? '0');
  const sort = c.req.query('sort') ?? 'popularity';

  const genre = await c.env.DB.prepare(
    `SELECT id FROM genres WHERE id = ?`
  ).bind(genreId).first();

  if (!genre) {
    return c.json({ error: 'Genre not found', status: 404 }, 404);
  }

  const allowedSorts: Record<string, string> = {
    popularity: 'popularity DESC',
    energy: 'energy DESC',
    tempo: 'tempo DESC',
    valence: 'valence DESC',
    name: 'name ASC',
  };
  const orderBy = allowedSorts[sort] ?? 'popularity DESC';

  const [tracks, countRow] = await Promise.all([
    c.env.DB.prepare(
      `SELECT * FROM tracks WHERE genre_id = ? ORDER BY ${orderBy} LIMIT ? OFFSET ?`
    ).bind(genreId, limit, offset).all(),
    c.env.DB.prepare(
      `SELECT COUNT(*) as total FROM tracks WHERE genre_id = ?`
    ).bind(genreId).first<{ total: number }>(),
  ]);

  return c.json({
    data: tracks.results,
    meta: {
      total: countRow?.total ?? 0,
      limit,
      offset,
      genre: genreId,
    },
  });
});

export default genres;
