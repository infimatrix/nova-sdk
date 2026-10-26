import { describe, expect, it } from "vitest";
import { Page } from "../src/index.js";
import { envelope, mockClient, page } from "./helpers.js";

function pagedClient(totalPages: number, seen: number[] = []) {
  return mockClient((call) => {
    const pageNo = Number(new URL(call.url).searchParams.get("page") ?? 1);
    seen.push(pageNo);
    return envelope(page([{ id: `${pageNo}-a` }, { id: `${pageNo}-b` }], pageNo, totalPages));
  });
}

describe("Page", () => {
  it("exposes items, pagination and hasNext", async () => {
    const { client } = pagedClient(2);
    const first = await client.templates.list();
    expect(first.items.map((i) => i.id)).toEqual(["1-a", "1-b"]);
    expect(first.length).toBe(2);
    expect(first.hasNext).toBe(true);
    expect(first.pagination.total_pages).toBe(2);
  });

  it("fetches the next page on demand and returns null at the end", async () => {
    const { client } = pagedClient(2);
    const first = await client.templates.list();
    const second = await first.getNextPage();
    expect(second?.items[0]?.id).toBe("2-a");
    expect(await second?.getNextPage()).toBeNull();
  });

  it("auto-paginates with for await", async () => {
    const seen: number[] = [];
    const { client } = pagedClient(3, seen);
    const ids: string[] = [];
    for await (const item of await client.templates.list({ search: "x" })) ids.push(item.id);
    expect(ids).toEqual(["1-a", "1-b", "2-a", "2-b", "3-a", "3-b"]);
    expect(seen).toEqual([1, 2, 3]);
  });

  it("keeps query params across pages and starts from a given page", async () => {
    const { client, calls } = pagedClient(3);
    const all = await (await client.contacts.list({ search: "acme", page: 2 })).toArray();
    expect(all).toHaveLength(4);
    expect(calls.map((c) => new URL(c.url).searchParams.get("search"))).toEqual(["acme", "acme"]);
    expect(calls.map((c) => new URL(c.url).searchParams.get("page"))).toEqual(["2", "3"]);
  });

  it("iterates pages", async () => {
    const { client } = pagedClient(2);
    const pages: number[] = [];
    for await (const p of (await client.templates.list()).iterPages()) pages.push(p.pagination.page);
    expect(pages).toEqual([1, 2]);
  });

  it("stops after a single page", async () => {
    const seen: number[] = [];
    const { client } = pagedClient(1, seen);
    expect(await (await client.templates.list()).toArray()).toHaveLength(2);
    expect(seen).toEqual([1]);
  });

  it("wraps bare arrays as one page", () => {
    const wrapped = Page.fromResponse<number>({ data: [1, 2, 3], success: true, message: "", meta: {} });
    expect(wrapped.items).toEqual([1, 2, 3]);
    expect(wrapped.hasNext).toBe(false);
  });

  it("tolerates unexpected payloads", () => {
    const wrapped = Page.fromResponse<number>({ data: null, success: true, message: "", meta: {} });
    expect(wrapped.items).toEqual([]);
  });
});
