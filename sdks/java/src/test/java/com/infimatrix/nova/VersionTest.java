package com.infimatrix.nova;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Test;

class VersionTest {
    @Test
    void sdkVersionMatchesThePom() {
        assertNotNull(System.getProperty("project.version"), "run through Maven");
        assertEquals(System.getProperty("project.version"), Version.VERSION);
    }
}
