import { fetchJson } from './client';

export type JobStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'cancelled';

export interface JobOut<T> {
  jobId: string;
  status: JobStatus;
  progress: number;
  result: T | null;
  error: string | null;
}

export function getJob<T>(jobId: string) {
  return fetchJson<JobOut<T>>(`/jobs/${jobId}`);
}
