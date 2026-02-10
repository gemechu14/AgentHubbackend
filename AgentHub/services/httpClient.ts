import { getApiUrl } from "@/lib/config";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export interface ApiErrorShape {
  message: string;
  status?: number;
}

export class ApiError extends Error {
  status?: number;

  constructor({ message, status }: ApiErrorShape) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export interface ApiFetchOptions extends RequestInit {
  method?: HttpMethod;
}

export async function apiFetch<TResponse>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<TResponse> {
  const url = getApiUrl(path);

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
    ...options,
  });

  const isJson =
    response.headers.get("content-type")?.includes("application/json") ?? false;

  if (!response.ok) {
    const errorBody = isJson ? await response.json() : null;
    const message =
      (errorBody as ApiErrorShape | null)?.message ??
      `Request to ${url} failed with status ${response.status}`;

    throw new ApiError({ message, status: response.status });
  }

  if (!isJson) {
    // @ts-expect-error - caller is responsible for correct typing when response is not JSON
    return response.text();
  }

  return (await response.json()) as TResponse;
}


