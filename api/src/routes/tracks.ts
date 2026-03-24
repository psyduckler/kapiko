import { Hono } from 'hono';
import type { Env, TrackQueryParams } from '../types';

const tracks = new Hono<{ Bindings: Env }>();

// GET /api/v1/tracks — search/browse all tracks
tracks.get('/', async (c) => {
  const params = c.req.query() as TrackQueryParams;
  const limit = Math.min(parseInt(params.limit ?? '20'), 100);
  const offset = parseInt(params.offset ?? '0');

  const allowedSorts: Record<string, string> = {
    popularity: 'popularity DESC',
    energy: 'energy DESC',
    energy_asc: 'energy ASC',
    tempo: 'tempo DESC',
    tempo_asc: 'tempo ASC',
    valence: 'valence DESC',
    name: 'name ASC',
    billboard_rank: 'billboard_rank ASC',
  };
  const orderBy = allowedSorts[params.sort ?? ''] ?? 'popularity DESC';

  const conditions: string[] = [];
  const bindings: (string | number)[] = [];

  if (params.genre) {
    conditions.push('genre_id = ?');
    bindings.push(params.genre.toLowerCase());
  }
  if (params.artist) {
    conditions.push('LOWER(artists) LIKE ?');
    bindings.push(`%${params.artist.toLowerCase()}%`);
  }
  if (params.min_energy !== undefined) {
    conditions.push('energy >= ?');
    bindings.push(parseFloat(params.min_energy));
  }
  if (params.max_energy !== undefined) {
    conditions.push('energy <= ?');
    bindings.push(parseFloat(params.max_energy));
  }
  if (params.min_tempo !== undefined) {
    conditions.push('tempo >= ?');
    bindings.push(parseFloat(params.min_tempo));
  }
  if (params.max_tempo !== undefined) {
    conditions.push('tempo <= ?');
    bindings.push(parseFloat(params.max_tempo));
  }
  if (params.key !== undefined) {
    const keyNum = parseInt(params.key);
    if (!isNaN(keyNum) && keyNum >= 0 && keyNum <= 11) {
      conditions.push('key = ?');
      bindings.push(keyNum);
    }
  }
  if (params.mode !== undefined) {
    const modeNum = parseInt(params.mode);
    if (modeNum === 0 || modeNum === 1) {
      conditions.push('mode = ?');
      bindings.push(modeNum);
    }
  }
  if (params.billboard_year !== undefined) {
    const yearNum = parseInt(params.billboard_year);
    if (!isNaN(yearNum) && yearNum >= 2000 && yearNum <= 2020) {
      conditions.push('billboard_year = ?');
      bindings.push(yearNum);
    }
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';

  const [rows, countRow] = await Promise.all([
    c.env.DB.prepare(
      `SELECT * FROM tracks ${where} ORDER BY ${orderBy} LIMIT ? OFFSET ?`
    ).bind(...bindings, limit, offset).all(),
    c.env.DB.prepare(
      `SELECT COUNT(*) as total FROM tracks ${where}`
    ).bind(...bindings).first<{ total: number }>(),
  ]);

  return c.json({
    data: rows.results,
    meta: {
      total: countRow?.total ?? 0,
      limit,
      offset,
    },
  });
});

// GET /api/v1/tracks/:id — single track with all analytics
tracks.get('/:id', async (c) => {
  const id = c.req.param('id');

  const track = await c.env.DB.prepare(
    `SELECT t.*, g.name as genre_name FROM tracks t
     LEFT JOIN genres g ON t.genre_id = g.id
     WHERE t.id = ?`
  ).bind(id).first();

  if (!track) {
    return c.json({ error: 'Track not found', status: 404 }, 404);
  }

  return c.json({ data: track });
});

export default tracks;
