import { NovaClient, type FetchLike, type NovaClientOptions } from "../src/index.js";

export const TENANT = "11111111-1111-1111-1111-111111111111";

export interface Call {
  url: string;
  method: string;
  headers: Record<string, string>;
  body: unknown;
  rawBody: unknown;
}

export function envelope(data: unknown, init: { status?: number; headers?: Record<string, string> } = {}): Response {
  return new Response(
    JSON.stringify({
      success: true,
      message: "Operation completed successfully.",
      data,
      errors: null,
      meta: { timestamp: "2026-10-26T00:00:00Z", correlation_id: "corr-1" },
    }),
    { status: init.status ?? 200, headers: { "Content-Type": "application/json", ...init.headers } },
  );
}

export function errorEnvelope(
  status: number,
  message: string,
  code = "API_ERROR",
  details: unknown = {},
  headers: Record<string, string> = {},
): Response {
  return new Response(
    JSON.stringify({
      success: false,
      message,
      data: null,
      error: { code, message, details },
      errors: { code, message, details },
      meta: { timestamp: "2026-10-26T00:00:00Z", correlation_id: "corr-err" },
    }),
    { status, headers: { "Content-Type": "application/json", ...headers } },
  );
}

export function page(results: unknown[], pageNo = 1, totalPages = 1, count = results.length): unknown {
  return {
    success: true,
    pagination: {
      count,
      next: pageNo < totalPages ? `http://x/?page=${pageNo + 1}` : null,
      previous: pageNo > 1 ? `http://x/?page=${pageNo - 1}` : null,
      page: pageNo,
      total_pages: totalPages,
      page_size: results.length,
    },
    results,
  };
}

/** Build a client whose fetch is `handler`, recording every call. */
export function mockClient(
  handler: (call: Call) => Response | Promise<Response>,
  options: NovaClientOptions = {},
): { client: NovaClient; calls: Call[] } {
  const calls: Call[] = [];
  const fetch: FetchLike = async (url, init = {}) => {
    const headers = Object.fromEntries(Object.entries((init.headers ?? {}) as Record<string, string>));
    let body: unknown = init.body;
    if (typeof init.body === "string") {
      try {
        body = JSON.parse(init.body);
      } catch {
        body = init.body;
      }
    }
    const call: Call = { url, method: String(init.method), headers, body, rawBody: init.body };
    calls.push(call);
    return handler(call);
  };
  const client = new NovaClient({
    apiKey: "nova_key_test_secret_1234567890",
    retryBackoffMs: 1,
    retryJitter: false,
    ...options,
    fetch,
  });
  return { client, calls };
}
