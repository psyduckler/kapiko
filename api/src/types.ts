export interface Env {
  DB: D1Database;
}

export interface Genre {
  id: string;
  name: string;
  description: string | null;
  track_count: number;
  avg_tempo: number | null;
  avg_energy: number | null;
  avg_valence: number | null;
  avg_loudness: number | null;
  avg_acousticness: number | null;
  avg_danceability: number | null;
  avg_instrumentalness: number | null;
  avg_speechiness: number | null;
  updated_at: string;
}

export interface Track {
  id: string;
  name: string;
  artists: string | null;
  album: string | null;
  genre_id: string | null;
  popularity: number | null;
  duration_ms: number | null;
  tempo: number | null;
  energy: number | null;
  valence: number | null;
  loudness: number | null;
  acousticness: number | null;
  danceability: number | null;
  instrumentalness: number | null;
  speechiness: number | null;
  liveness: number | null;
  key: number | null;
  mode: number | null;
  time_signature: number | null;
  source: string;
  created_at: string;
}

export interface ApiResponse<T> {
  data: T;
  meta?: {
    total?: number;
    limit?: number;
    offset?: number;
    genre?: string;
  };
}

export interface ApiError {
  error: string;
  status: number;
}

export interface TrackQueryParams {
  genre?: string;
  artist?: string;
  min_energy?: string;
  max_energy?: string;
  min_tempo?: string;
  max_tempo?: string;
  key?: string;
  mode?: string;
  sort?: string;
  limit?: string;
  offset?: string;
}

export interface CompareResult {
  track: Track;
  genre: Genre;
  comparison: {
    tempo: FeatureComparison;
    energy: FeatureComparison;
    valence: FeatureComparison;
    loudness: FeatureComparison;
    acousticness: FeatureComparison;
    danceability: FeatureComparison;
    instrumentalness: FeatureComparison;
    speechiness: FeatureComparison;
  };
}

export interface FeatureComparison {
  track_value: number | null;
  genre_avg: number | null;
  delta: number | null;
  percentile_label: string;
}
