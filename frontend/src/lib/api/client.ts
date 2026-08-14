export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = init?.body instanceof FormData ? init.headers : { 'Content-Type': 'application/json', ...init?.headers };
  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const payload = await response.json() as { error?: string };
      message = payload.error ?? message;
    } catch {
      // Respuesta no JSON: alcanza con estado HTTP.
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}
