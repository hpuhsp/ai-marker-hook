// === AI GENERATED FILE | claude-sonnet-4-6 | 2026-06-18 | DESKTOP-NEC290S\HSP ===
package com.example.demo;

import java.util.HashMap;
import java.util.Map;

public class UserService {

    private final Map<Integer, String> users = new HashMap<>();

    public void addUser(int id, String name) {
        users.put(id, name);
    }

    public String getUser(int id) {
        return users.getOrDefault(id, "unknown");
    }

    public boolean removeUser(int id) {
        return users.remove(id) != null;
    }
}
