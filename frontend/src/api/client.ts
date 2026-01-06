

export type HttpMethod = "GET" | "POST";

// Get auth token from store (for use outside React components)
const getAuthToken = () => {
  const stored = localStorage.getItem("debate-auth");
  if (stored) {
    try {
      const parsed = JSON.parse(stored);
      return parsed.state?.token || null;
    } catch {
      return null;
    }
  }
  return null;
};

export const createClient = (baseUrl: string) => {
  const request = async <T>(path: string, method: HttpMethod, body?: unknown): Promise<T> => {
    const token = getAuthToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json"
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${baseUrl}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed with ${response.status}`);
    }
    return (await response.json()) as T;
  };

  return {
    get: <T>(path: string) => request<T>(path, "GET"),
    post: <T>(path: string, body: unknown) => request<T>(path, "POST", body)
  };
};
