"""Object-Oriented Programming (OOP) Module and Practice Service.

Provides structured learning modules, design pattern guides, and OOP coding challenges
for the OOP track.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class OOPModule(BaseModel):
    """OOP learning module specification."""
    id: str
    title: str
    category: str  # PILLARS, SOLID, DESIGN_PATTERNS, ARCHITECTURE
    summary: str
    key_concepts: List[str]
    code_example: str
    design_tradeoffs: str


OOP_CURRICULUM_MODULES: List[Dict[str, Any]] = [
    {
        "id": "oop-encapsulation",
        "title": "Encapsulation & Information Hiding",
        "category": "PILLARS",
        "summary": "Bundling data with methods that operate on that data and restricting direct access to object internals.",
        "key_concepts": ["Private/Protected access modifiers", "Getters and Setters", "Invariants preservation", "Data hiding"],
        "code_example": (
            "class BankAccount:\n"
            "    def __init__(self, initial_balance: float):\n"
            "        self._balance = max(0.0, initial_balance)\n\n"
            "    def deposit(self, amount: float) -> bool:\n"
            "        if amount > 0:\n"
            "            self._balance += amount\n"
            "            return True\n"
            "        return False\n\n"
            "    @property\n"
            "    def balance(self) -> float:\n"
            "        return self._balance"
        ),
        "design_tradeoffs": "Prevents invalid internal state at the cost of slight boilerplate.",
    },
    {
        "id": "oop-inheritance-polymorphism",
        "title": "Inheritance & Polymorphism",
        "category": "PILLARS",
        "summary": "Subtyping mechanisms allowing specialized subclasses to override base class behavior while preserving interface substitutability.",
        "key_concepts": ["Method overriding", "Dynamic dispatch", "Abstract Base Classes (ABCs)", "Subtype polymorphism"],
        "code_example": (
            "from abc import ABC, abstractmethod\n\n"
            "class Shape(ABC):\n"
            "    @abstractmethod\n"
            "    def area(self) -> float:\n"
            "        pass\n\n"
            "class Circle(Shape):\n"
            "    def __init__(self, radius: float):\n"
            "        self.radius = radius\n"
            "    def area(self) -> float:\n"
            "        return 3.14159 * self.radius ** 2\n\n"
            "class Rectangle(Shape):\n"
            "    def __init__(self, width: float, height: float):\n"
            "        self.width = width\n"
            "        self.height = height\n"
            "    def area(self) -> float:\n"
            "        return self.width * self.height"
        ),
        "design_tradeoffs": "Promotes code reuse, but deep inheritance hierarchies lead to fragile base class problems.",
    },
    {
        "id": "oop-composition",
        "title": "Composition over Inheritance",
        "category": "ARCHITECTURE",
        "summary": "Designing systems by combining simpler objects into complex ones rather than inheriting behaviors.",
        "key_concepts": ["Has-a vs Is-a relationships", "Delegation", "Loose coupling", "Runtime flexibility"],
        "code_example": (
            "class Engine:\n"
            "    def start(self) -> str:\n"
            "        return 'Engine started'\n\n"
            "class Car:\n"
            "    def __init__(self, engine: Engine):\n"
            "        self._engine = engine  # Composition\n\n"
            "    def drive(self) -> str:\n"
            "        return f'Driving: {self._engine.start()}'"
        ),
        "design_tradeoffs": "Significantly reduces coupling and makes testing trivial via mock injection.",
    },
    {
        "id": "solid-principles",
        "title": "SOLID Design Principles",
        "category": "SOLID",
        "summary": "The five foundational principles for maintainable, scalable object-oriented software design.",
        "key_concepts": [
            "Single Responsibility Principle (SRP)",
            "Open/Closed Principle (OCP)",
            "Liskov Substitution Principle (LSP)",
            "Interface Segregation Principle (ISP)",
            "Dependency Inversion Principle (DIP)",
        ],
        "code_example": (
            "# Dependency Inversion Principle:\n"
            "from abc import ABC, abstractmethod\n\n"
            "class NotificationSender(ABC):\n"
            "    @abstractmethod\n"
            "    def send(self, recipient: str, msg: str) -> None: pass\n\n"
            "class EmailSender(NotificationSender):\n"
            "    def send(self, recipient: str, msg: str) -> None:\n"
            "        print(f'Sending Email to {recipient}: {msg}')\n\n"
            "class UserManager:\n"
            "    def __init__(self, notifier: NotificationSender):\n"
            "        self.notifier = notifier  # Depends on abstraction!"
        ),
        "design_tradeoffs": "Improves modularity and extensibility; requires upfront architectural discipline.",
    },
    {
        "id": "design-patterns-creational-behavioral",
        "title": "Essential Design Patterns",
        "category": "DESIGN_PATTERNS",
        "summary": "Proven software solutions: Factory, Singleton, Strategy, Observer, and Decorator.",
        "key_concepts": ["Factory Method", "Strategy Pattern", "Observer Pattern", "Decorator Pattern"],
        "code_example": (
            "# Strategy Pattern:\n"
            "class PaymentStrategy(ABC):\n"
            "    @abstractmethod\n"
            "    def pay(self, amount: float) -> str: pass\n\n"
            "class CreditCardPayment(PaymentStrategy):\n"
            "    def pay(self, amount: float) -> str:\n"
            "        return f'Paid ${amount} via Credit Card'\n\n"
            "class CryptoPayment(PaymentStrategy):\n"
            "    def pay(self, amount: float) -> str:\n"
            "        return f'Paid ${amount} via Ethereum'"
        ),
        "design_tradeoffs": "Replaces rigid conditionals with polymorphic strategies, allowing seamless extension.",
    },
]


class OOPService:
    """Delivers OOP learning modules and practice guidance."""

    @classmethod
    def list_modules(cls) -> List[OOPModule]:
        """Returns all structured OOP learning modules."""
        return [OOPModule(**m) for m in OOP_CURRICULUM_MODULES]

    @classmethod
    def get_module(cls, module_id: str) -> Optional[OOPModule]:
        """Retrieves an individual OOP module by ID."""
        for m in OOP_CURRICULUM_MODULES:
            if m["id"] == module_id:
                return OOPModule(**m)
        return None
