// === AI GENERATED FILE | unknown-model | 2026-06-18 | v?.?.? | DESKTOP-NEC290S\HSP ===
package com.example.demo;

public class TestBean {

// === AI REPLACED BEGIN | unknown-model | 2026-06-18 | v?.?.? | replaced | DESKTOP-NEC290S\HSP ===
// [ORIGINAL]
//     private String name;
//     private int age;
// [/ORIGINAL]
    private String firstName;
    private String lastName;
    private int birthYear;
    private String email;
    private boolean active;
// === AI REPLACED END ===


    public TestBean(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getAge() {
        return age;
    }

    public void setAge(int age) {
        this.age = age;
    }

// === AI MODIFIED BEGIN | unknown-model | 2026-06-18 | v?.?.? | modified | DESKTOP-NEC290S\HSP ===
    @Override
    public String toString() {
        StringBuilder sb = new StringBuilder();
        sb.append("TestBean{\n");
        sb.append("  name  = ").append(name).append("\n");
        sb.append("  age   = ").append(age).append("\n");
        sb.append("  adult = ").append(age >= 18 ? "yes" : "no").append("\n");
        sb.append("}");
        return sb.toString();
    }
// === AI MODIFIED END ===


}
