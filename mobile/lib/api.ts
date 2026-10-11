import { API_URL } from '@/constants/config';

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 20000);

  try {
    const response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const responseText = await response.text();
    let data: unknown = {};

    try {
      data = responseText ? JSON.parse(responseText) : {};
    } catch {
      throw new Error(`The server returned an invalid response (HTTP ${response.status}).`);
    }

    if (!response.ok) {
      const detail = typeof data === 'object' && data !== null && 'detail' in data
        ? data.detail
        : undefined;
      throw new Error(typeof detail === 'string' ? detail : `Request failed (HTTP ${response.status}).`);
    }

    return data as T;
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      throw new Error(`The server did not respond within 20 seconds at ${API_URL}.`);
    }
    if (error instanceof TypeError) {
      throw new Error(`Cannot connect to ${API_URL}. Check that the backend is running and reachable on this network.`);
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}