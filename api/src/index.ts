import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import type { Env } from './types';
import genresRouter from './routes/genres';
import tracksRouter from './routes/tracks';
import compareRouter from './routes/compare';
import statsRouter from './routes/stats';

const app = new Hono<{ Bindings: Env }>();

// Middleware
app.use('*', logger());
app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'OPTIONS'],
  allowHeaders: ['Content-Type'],
  maxAge: 86400,
}));

// Health check
app.get('/', (c) => c.json({
  name: 'kapiko Music Intelligence API',
  version: '1.0.0',
  docs: '/api/v1',
  status: 'ok',
}));

// API v1 root
app.get('/api/v1', (c) => c.json({
  version: '1.0.0',
  endpoints: [
    'GET /api/v1/stats',
    'GET /api/v1/genres',
    'GET /api/v1/genres/:genre',
    'GET /api/v1/genres/:genre/tracks',
    'GET /api/v1/tracks',
    'GET /api/v1/tracks/:id',
    'GET /api/v1/compare?track_id=...&genre=...',
  ],
  authentication: 'none — open access during beta',
  rate_limits: 'none — open access during beta',
}));

// Mount routers
app.route('/api/v1/genres', genresRouter);
app.route('/api/v1/tracks', tracksRouter);
app.route('/api/v1/compare', compareRouter);
app.route('/api/v1/stats', statsRouter);

// 404
app.notFound((c) => c.json({ error: 'Not found', status: 404 }, 404));

// Error handler
app.onError((err, c) => {
  console.error(err);
  return c.json({ error: 'Internal server error', status: 500 }, 500);
});

export default app;
