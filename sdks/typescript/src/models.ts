/** Response envelope and pagination primitives. */

/** Metadata attached to every Nova API response. */
export interface EnvelopeMeta {
  timestamp?: string;
  correlation_id?: string | null;
  [key: string]: unknown;
}

/** An unwrapped API response: the payload plus envelope details. */
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message: string;
  meta: EnvelopeMeta;
}

/** Pagination details reported by list endpoints. */
export interface PaginationInfo {
  count: number;
  next: string | null;
  previous: string | null;
  page: number;
  total_pages: number;
  page_size: number;
}

export type PageFetcher<T> = (page: number) => Promise<Page<T>>;

/**
 * One page of a list endpoint.
 *
 * - `page.items` holds the current page.
 * - `for await (const item of page)` walks the remaining items across **all** following
 *   pages, fetching them lazily (Stripe/OpenAI-style auto-pagination).
 * - {@link Page.getNextPage} fetches a single following page.
 */
export class Page<T> implements AsyncIterable<T> {
  constructor(
    readonly items: T[],
    readonly pagination: PaginationInfo,
    readonly meta: EnvelopeMeta = {},
    private readonly fetchPage?: PageFetcher<T>,
  ) {}

  /** Number of items on this page. */
  get length(): number {
    return this.items.length;
  }

  /** Whether the server reports another page after this one. */
  get hasNext(): boolean {
    return this.pagination.next !== null;
  }

  /** Fetch the next page, or `null` when this is the last one. */
  async getNextPage(): Promise<Page<T> | null> {
    if (!this.hasNext || this.pagination.page >= this.pagination.total_pages || !this.fetchPage) {
      return null;
    }
    return this.fetchPage(this.pagination.page + 1);
  }

  /** Iterate every page starting at this one. */
  async *iterPages(): AsyncGenerator<Page<T>, void, undefined> {
    let page: Page<T> | null = this;
    for (let guard = 0; page && guard < MAX_PAGES; guard++) {
      yield page;
      page = await page.getNextPage();
    }
  }

  /** Iterate every item starting at this page. */
  async *iterItems(): AsyncGenerator<T, void, undefined> {
    for await (const page of this.iterPages()) yield* page.items;
  }

  [Symbol.asyncIterator](): AsyncIterator<T> {
    return this.iterItems();
  }

  /** Collect every item from this page onward into an array. */
  async toArray(): Promise<T[]> {
    const all: T[] = [];
    for await (const item of this) all.push(item);
    return all;
  }

  /** Build a page from an unwrapped list response. */
  static fromResponse<T>(response: ApiResponse<unknown>, fetchPage?: PageFetcher<T>): Page<T> {
    const data = response.data;
    if (data && typeof data === "object" && !Array.isArray(data) && "results" in data) {
      const body = data as { results?: T[]; pagination?: Partial<PaginationInfo> };
      return new Page<T>(body.results ?? [], normalizePagination(body.pagination), response.meta, fetchPage);
    }
    if (Array.isArray(data)) {
      const items = data as T[];
      return new Page<T>(
        items,
        { count: items.length, next: null, previous: null, page: 1, total_pages: 1, page_size: items.length || 20 },
        response.meta,
        fetchPage,
      );
    }
    return new Page<T>([], normalizePagination(undefined), response.meta, fetchPage);
  }
}

/** Upper bound on pages fetched by one iteration (runaway guard). */
export const MAX_PAGES = 10_000;

function normalizePagination(info: Partial<PaginationInfo> | undefined): PaginationInfo {
  return {
    count: Number(info?.count ?? 0),
    next: info?.next ?? null,
    previous: info?.previous ?? null,
    page: Number(info?.page ?? 1),
    total_pages: Number(info?.total_pages ?? 1),
    page_size: Number(info?.page_size ?? 20),
  };
}
