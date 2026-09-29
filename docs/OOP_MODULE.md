# DSAapp Object-Oriented Programming (OOP) & System Design Patterns

## Overview
Phase 8 incorporates a dedicated curriculum and reference framework for **Object-Oriented Design**, covering fundamental principles, clean architecture guidelines, and production-tested Gang-of-Four (GoF) design patterns.

---

## 1. The Four Pillars of OOP
The platform provides in-depth interactive breakdowns with code implementations in **Python, Java, C++, and TypeScript**:

1. **Encapsulation**:
   - Bundling state and operations within cohesive classes.
   - Restricting direct external access via access modifiers and property getters/setters.
   - Eliminating temporal coupling and invariant violations.
2. **Abstraction**:
   - Hiding implementation complexities behind clean, declarative interfaces.
   - Using abstract base classes (ABCs) and interface contracts.
3. **Inheritance**:
   - Code reuse and taxonomic specialization.
   - Favoring composition over inheritance to prevent fragile base class problems.
4. **Polymorphism**:
   - Dynamic dispatch, duck typing, and interface polymorphism.
   - Allowing uniform manipulation of divergent concrete types at runtime.

---

## 2. SOLID Design Principles
Each principle features a realistic before/after refactoring case study:

- **S — Single Responsibility Principle (SRP)**: A module or class should have one, and only one, reason to change.
- **O — Open/Closed Principle (OCP)**: Software entities should be open for extension, but closed for modification.
- **L — Liskov Substitution Principle (LSP)**: Subtypes must be substitutable for their base types without altering program correctness.
- **I — Interface Segregation Principle (ISP)**: Clients should not be forced to depend upon interfaces they do not use.
- **D — Dependency Inversion Principle (DIP)**: High-level modules should depend on abstractions, not on concrete low-level implementations.

---

## 3. GoF Design Patterns
The pattern catalog classifies patterns into three canonical categories with Mermaid architecture diagrams, trade-off analyses, and multi-language samples:

1. **Creational**:
   - *Factory Method*: Subclasses decide which class to instantiate.
   - *Singleton / Monostate*: Controlled single-instance access with thread-safety.
2. **Structural**:
   - *Adapter*: Bridging incompatible interfaces.
   - *Decorator*: Dynamically attaching additional responsibilities without subclass proliferation.
3. **Behavioral**:
   - *Observer*: Publish-subscribe event notification model.
   - *Strategy*: Encapsulating interchangeable families of algorithms.
