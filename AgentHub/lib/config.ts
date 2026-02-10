export const APP_NAME = "AgentHub";

const FALLBACK_BASE_API_URL = "/api/mock";

export const BASE_API_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? FALLBACK_BASE_API_URL;

export const getApiUrl = (path: string) => {
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  const normalizedBase = BASE_API_URL.endsWith("/")
    ? BASE_API_URL.slice(0, -1)
    : BASE_API_URL;

  return `${normalizedBase}/${normalizedPath}`;
};


