package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.infimatrix.nova.MockServer.Reply;
import com.infimatrix.nova.models.Template;
import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.Optional;
import org.junit.jupiter.api.Test;

class PaginationTest {

    private static MockServer paged(int totalPages) {
        return new MockServer().reply(r -> {
            String query = r.query() == null ? "" : r.query();
            int number = query.contains("page=") ? Integer.parseInt(query.replaceAll(".*page=(\\d+).*", "$1")) : 1;
            return Reply.ok(MockServer.page(number, totalPages,
                    "[{\"id\":\"" + number + "-a\"},{\"id\":\"" + number + "-b\"}]"));
        });
    }

    @Test
    void exposesItemsPaginationAndHasNext() {
        try (MockServer server = paged(2)) {
            Page<Template> first = server.clientBuilder().build().templates().list(Query.empty());
            assertEquals(2, first.size());
            assertEquals("1-a", first.items().get(0).id());
            assertTrue(first.hasNext());
            assertEquals(2, first.pagination().totalPages());
            assertEquals(4, first.pagination().count());
        }
    }

    @Test
    void fetchesTheNextPageAndEndsWithEmpty() {
        try (MockServer server = paged(2)) {
            Page<Template> first = server.clientBuilder().build().templates().list(Query.empty());
            Optional<Page<Template>> second = first.nextPage();
            assertEquals("2-a", second.orElseThrow().items().get(0).id());
            assertTrue(second.get().nextPage().isEmpty());
        }
    }

    @Test
    void iteratingAPageWalksEveryFollowingPageLazily() {
        try (MockServer server = paged(3)) {
            Page<Template> first = server.clientBuilder().build().templates().list(Query.builder().search("x").build());
            List<String> ids = new ArrayList<>();
            for (Template t : first) {
                ids.add(t.id());
            }
            assertEquals(List.of("1-a", "1-b", "2-a", "2-b", "3-a", "3-b"), ids);
            assertEquals(3, server.requests().size());
            assertTrue(server.requests().stream().allMatch(r -> r.query().contains("search=x")));
        }
    }

    @Test
    void streamAndToListMatchIteration() {
        try (MockServer server = paged(2)) {
            Page<Template> first = server.clientBuilder().build().templates().list(Query.empty());
            assertEquals(4, first.toList().size());
            assertEquals(2, first.stream().filter(t -> t.id().endsWith("a")).count());
        }
    }

    @Test
    void pagesIterableYieldsEachPage() {
        try (MockServer server = paged(3)) {
            Page<Template> first = server.clientBuilder().build().templates().list(Query.empty());
            List<Integer> numbers = new ArrayList<>();
            first.pages().forEach(p -> numbers.add(p.pagination().page()));
            assertEquals(List.of(1, 2, 3), numbers);
        }
    }

    @Test
    void startsAtTheRequestedPage() {
        try (MockServer server = paged(3)) {
            Page<Template> from2 = server.clientBuilder().build().templates().list(Query.builder().page(2).build());
            assertEquals(4, from2.toList().size());
            assertEquals(2, server.requests().size());
        }
    }

    @Test
    void singlePageDoesNotFetchMore() {
        try (MockServer server = paged(1)) {
            Page<Template> only = server.clientBuilder().build().templates().list(Query.empty());
            assertFalse(only.hasNext());
            assertEquals(2, only.toList().size());
            assertEquals(1, server.requests().size());
        }
    }

    @Test
    void bareArraysAndUnexpectedPayloadsBecomeOnePage() {
        try (MockServer server = new MockServer()) {
            NovaClient client = server.clientBuilder().build();
            server.reply(Reply.ok("[{\"id\":\"a\"},{\"id\":\"b\"}]"));
            Page<Template> bare = client.templates().list(Query.empty());
            assertEquals(2, bare.size());
            assertFalse(bare.hasNext());
            server.reply(Reply.ok("null"));
            assertEquals(0, client.templates().list(Query.empty()).size());
            server.reply(Reply.ok("{\"unexpected\":true}"));
            assertEquals(0, client.templates().list(Query.empty()).size());
        }
    }

    @Test
    void iteratorThrowsWhenExhausted() {
        try (MockServer server = paged(1)) {
            var iterator = server.clientBuilder().build().templates().list(Query.empty()).iterator();
            iterator.next();
            iterator.next();
            assertThrows(NoSuchElementException.class, iterator::next);
        }
    }

    @Test
    void queryBuilderCopiesAreIndependent() {
        Query base = Query.builder().search("a").build();
        Query derived = base.toBuilder().page(3).build();
        assertEquals(1, base.params().size());
        assertEquals(2, derived.params().size());
    }
}
