package com.infimatrix.nova;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Optional;
import java.util.function.IntFunction;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;

/**
 * One page of a list endpoint.
 *
 * <ul>
 *   <li>{@link #items()} holds the current page.
 *   <li>Iterating the page itself ({@code for (var x : page)}) walks the remaining items across <b>all</b>
 *       following pages, fetching them lazily.
 *   <li>{@link #nextPage()} fetches a single following page.
 * </ul>
 *
 * @param <T> item type
 */
public final class Page<T> implements Iterable<T> {
    /** Upper bound on pages fetched by one iteration (runaway guard). */
    public static final int MAX_PAGES = 10_000;

    private final List<T> items;
    private final Pagination pagination;
    private final IntFunction<Page<T>> fetcher;

    /** Creates a page; {@code fetcher} loads another page by number and may be {@code null}. */
    public Page(List<T> items, Pagination pagination, IntFunction<Page<T>> fetcher) {
        this.items = List.copyOf(items);
        this.pagination = pagination;
        this.fetcher = fetcher;
    }

    /** Items of this page (unmodifiable). */
    public List<T> items() {
        return items;
    }

    /** Pagination details. */
    public Pagination pagination() {
        return pagination;
    }

    /** Number of items on this page. */
    public int size() {
        return items.size();
    }

    /** Whether the server reports another page after this one. */
    public boolean hasNext() {
        return pagination.next() != null;
    }

    /** Fetches the next page, or returns empty when this is the last one. */
    public Optional<Page<T>> nextPage() {
        if (!hasNext() || pagination.page() >= pagination.totalPages() || fetcher == null) {
            return Optional.empty();
        }
        return Optional.of(fetcher.apply(pagination.page() + 1));
    }

    /** Iterates every page starting at this one. */
    public Iterable<Page<T>> pages() {
        return () -> new Iterator<>() {
            private Page<T> current = Page.this;
            private int fetched;

            @Override
            public boolean hasNext() {
                return current != null && fetched < MAX_PAGES;
            }

            @Override
            public Page<T> next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                Page<T> result = current;
                fetched++;
                current = result.nextPage().orElse(null);
                return result;
            }
        };
    }

    /** Iterates every item starting at this page, fetching following pages lazily. */
    @Override
    public Iterator<T> iterator() {
        Iterator<Page<T>> pageIterator = pages().iterator();
        return new Iterator<>() {
            private Iterator<T> inner = List.<T>of().iterator();

            @Override
            public boolean hasNext() {
                while (!inner.hasNext() && pageIterator.hasNext()) {
                    inner = pageIterator.next().items().iterator();
                }
                return inner.hasNext();
            }

            @Override
            public T next() {
                if (!hasNext()) {
                    throw new NoSuchElementException();
                }
                return inner.next();
            }
        };
    }

    /** A sequential stream of every item from this page onward. */
    public Stream<T> stream() {
        return StreamSupport.stream(spliterator(), false);
    }

    /** Collects every item from this page onward. */
    public List<T> toList() {
        List<T> all = new ArrayList<>();
        forEach(all::add);
        return all;
    }
}
