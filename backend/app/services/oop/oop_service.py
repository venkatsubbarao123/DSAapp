"""Object-Oriented Programming (OOP) Module and Practice Service.

Provides structured learning modules, design pattern guides, and OOP coding challenges
for the OOP track.
"""

from typing import Any

from pydantic import BaseModel


class OOPModule(BaseModel):
    """OOP learning module specification."""

    id: str
    title: str
    category: str  # PILLARS, SOLID, DESIGN_PATTERNS, ARCHITECTURE
    summary: str
    key_concepts: list[str]
    code_example: str
    design_tradeoffs: str


class OOPPillar(BaseModel):
    """Four Pillars of Object-Oriented Programming."""

    id: str
    name: str
    summary: str
    explanation: str
    code_examples: dict[str, str]
    common_pitfalls: list[str]


class SOLIDPrinciple(BaseModel):
    """SOLID software design principles."""

    letter: str
    name: str
    summary: str
    bad_example: dict[str, str]
    good_example: dict[str, str]
    benefits: list[str]


class OOPDesignPattern(BaseModel):
    """Gang of Four design pattern specification."""

    name: str
    category: str  # CREATIONAL, STRUCTURAL, BEHAVIORAL
    intent: str
    use_cases: list[str]
    structure_diagram_mermaid: str
    implementation: dict[str, str]
    tradeoffs: list[str]


class OOPOverview(BaseModel):
    """Consolidated overview payload for the frontend OOP hub."""

    pillars: list[OOPPillar]
    solid_principles: list[SOLIDPrinciple]
    design_patterns: list[OOPDesignPattern]


# ---------------------------------------------------------------------------
# Data Definitions
# ---------------------------------------------------------------------------

OOP_PILLARS_DATA: list[dict[str, Any]] = [
    {
        "id": "encapsulation",
        "name": "Encapsulation",
        "summary": "Bundling data and operations into a single unit while restricting direct access to internal state.",
        "explanation": "Encapsulation ensures an object controls its own integrity. State is kept private, and access is mediated through validated public methods (getters, setters, or domain actions). This prevents outside callers from leaving the object in an invalid invariant state.",
        "code_examples": {
            "python": (
                "class BankAccount:\n"
                "    def __init__(self, owner: str, balance: float = 0.0):\n"
                "        self.owner = owner\n"
                "        self._balance = max(0.0, balance)\n\n"
                "    def deposit(self, amount: float) -> bool:\n"
                "        if amount <= 0:\n"
                "            return False\n"
                "        self._balance += amount\n"
                "        return True\n\n"
                "    def withdraw(self, amount: float) -> bool:\n"
                "        if 0 < amount <= self._balance:\n"
                "            self._balance -= amount\n"
                "            return True\n"
                "        return False\n\n"
                "    @property\n"
                "    def balance(self) -> float:\n"
                "        return self._balance\n"
            ),
            "java": (
                "public class BankAccount {\n"
                "    private final String owner;\n"
                "    private double balance;\n\n"
                "    public BankAccount(String owner, double initialBalance) {\n"
                "        this.owner = owner;\n"
                "        this.balance = Math.max(0.0, initialBalance);\n"
                "    }\n\n"
                "    public boolean deposit(double amount) {\n"
                "        if (amount <= 0) return false;\n"
                "        this.balance += amount;\n"
                "        return true;\n"
                "    }\n\n"
                "    public double getBalance() {\n"
                "        return this.balance;\n"
                "    }\n"
                "}\n"
            ),
            "cpp": (
                "#include <string>\n"
                "#include <algorithm>\n\n"
                "class BankAccount {\n"
                "private:\n"
                "    std::string owner;\n"
                "    double balance;\n\n"
                "public:\n"
                "    BankAccount(std::string o, double init_bal)\n"
                "        : owner(std::move(o)), balance(std::max(0.0, init_bal)) {}\n\n"
                "    bool deposit(double amount) {\n"
                "        if (amount <= 0) return false;\n"
                "        balance += amount;\n"
                "        return true;\n"
                "    }\n"
                "    double getBalance() const { return balance; }\n"
                "};\n"
            ),
            "typescript": (
                "export class BankAccount {\n"
                "  private _balance: number;\n\n"
                "  constructor(public readonly owner: string, initialBalance: number = 0) {\n"
                "    this._balance = Math.max(0, initialBalance);\n"
                "  }\n\n"
                "  public deposit(amount: number): boolean {\n"
                "    if (amount <= 0) return false;\n"
                "    this._balance += amount;\n"
                "    return true;\n"
                "  }\n\n"
                "  public get balance(): number {\n"
                "    return this._balance;\n"
                "  }\n"
                "}\n"
            ),
        },
        "common_pitfalls": [
            "Exposing internal mutable collections directly through public getters without copying.",
            "Creating boilerplate getters and setters for every private field without actual invariants or encapsulation.",
            "Violating Law of Demeter by chaining deeply nested object calls (e.g. order.getCustomer().getAddress().getZip()).",
        ],
    },
    {
        "id": "abstraction",
        "name": "Abstraction",
        "summary": "Hiding implementation complexity behind a concise, purpose-driven interface.",
        "explanation": "Abstraction allows client code to interact with high-level contracts without caring about the concrete implementation details. Whether sending a notification via SMS, Email, or Webhook, callers only invoke send_notification(msg).",
        "code_examples": {
            "python": (
                "from abc import ABC, abstractmethod\n\n"
                "class PaymentProcessor(ABC):\n"
                "    @abstractmethod\n"
                "    def process_payment(self, amount: float) -> bool:\n"
                "        pass\n\n"
                "class StripeProcessor(PaymentProcessor):\n"
                "    def process_payment(self, amount: float) -> bool:\n"
                "        # Internal Stripe API calls, tokenization, TLS handshake\n"
                "        return True\n"
            ),
            "java": (
                "public interface PaymentProcessor {\n"
                "    boolean processPayment(double amount);\n"
                "}\n\n"
                "public class StripeProcessor implements PaymentProcessor {\n"
                "    @Override\n"
                "    public boolean processPayment(double amount) {\n"
                "        // complex payment orchestration\n"
                "        return true;\n"
                "    }\n"
                "}\n"
            ),
            "cpp": (
                "class PaymentProcessor {\n"
                "public:\n"
                "    virtual ~PaymentProcessor() = default;\n"
                "    virtual bool processPayment(double amount) = 0;\n"
                "};\n"
            ),
            "typescript": (
                "export interface PaymentProcessor {\n"
                "  processPayment(amount: number): Promise<boolean>;\n"
                "}\n"
            ),
        },
        "common_pitfalls": [
            "Leaky abstractions where underlying implementation exceptions bubble up raw to caller.",
            "Over-abstraction creating dozens of single-implementation interfaces that add indirection without value.",
        ],
    },
    {
        "id": "inheritance",
        "name": "Inheritance",
        "summary": "Deriving specialized classes from general base classes to promote structural reuse.",
        "explanation": "Inheritance establishes an 'is-a' relationship between classes, enabling subclasses to inherit attributes and methods from a superclass. When used judiciously with shallow hierarchies, it cleanly models domain hierarchies.",
        "code_examples": {
            "python": (
                "class Vehicle:\n"
                "    def __init__(self, brand: str, model: str):\n"
                "        self.brand = brand\n"
                "        self.model = model\n\n"
                "    def describe(self) -> str:\n"
                "        return f'{self.brand} {self.model}'\n\n"
                "class ElectricCar(Vehicle):\n"
                "    def __init__(self, brand: str, model: str, battery_kwh: int):\n"
                "        super().__init__(brand, model)\n"
                "        self.battery_kwh = battery_kwh\n"
            ),
            "java": (
                "public class Vehicle {\n"
                "    protected String brand;\n"
                "    protected String model;\n\n"
                "    public Vehicle(String brand, String model) {\n"
                "        this.brand = brand;\n"
                "        this.model = model;\n"
                "    }\n"
                "}\n"
            ),
            "cpp": (
                "class Vehicle {\n"
                "protected:\n"
                "    std::string brand;\n"
                "    std::string model;\n"
                "public:\n"
                "    Vehicle(std::string b, std::string m) : brand(b), model(m) {}\n"
                "};\n"
            ),
            "typescript": (
                "export class Vehicle {\n"
                "  constructor(public brand: string, public model: string) {}\n"
                "}\n"
            ),
        },
        "common_pitfalls": [
            "Deep inheritance trees leading to fragile base class problems.",
            "Using inheritance for code reuse when composition ('has-a') is the more appropriate model.",
        ],
    },
    {
        "id": "polymorphism",
        "name": "Polymorphism",
        "summary": "Treating objects of different subclasses through a uniform interface with runtime dynamic dispatch.",
        "explanation": "Polymorphism lets a single function or caller operate on diverse object types uniformly. At runtime, the language invokes the overriding implementation specific to each instance.",
        "code_examples": {
            "python": (
                "from abc import ABC, abstractmethod\n\n"
                "class Shape(ABC):\n"
                "    @abstractmethod\n"
                "    def area(self) -> float:\n"
                "        pass\n\n"
                "class Circle(Shape):\n"
                "    def __init__(self, radius: float):\n"
                "        self.radius = radius\n"
                "    def area(self) -> float:\n"
                "        return 3.14159 * (self.radius ** 2)\n\n"
                "class Rectangle(Shape):\n"
                "    def __init__(self, w: float, h: float):\n"
                "        self.w, self.h = w, h\n"
                "    def area(self) -> float:\n"
                "        return self.w * self.h\n\n"
                "def calculate_total_area(shapes: list[Shape]) -> float:\n"
                "    return sum(s.area() for s in shapes)  # Polymorphic dispatch\n"
            ),
            "java": (
                "public abstract class Shape {\n    public abstract double area();\n}\n"
            ),
            "cpp": (
                "class Shape {\n"
                "public:\n"
                "    virtual ~Shape() = default;\n"
                "    virtual double area() const = 0;\n"
                "};\n"
            ),
            "typescript": ("export interface Shape {\n  area(): number;\n}\n"),
        },
        "common_pitfalls": [
            "Relying on type checks (isinstance / instanceof) instead of overriding polymorphic methods.",
            "Violating Liskov Substitution Principle by changing method preconditions or postconditions in subclasses.",
        ],
    },
]

OOP_SOLID_DATA: list[dict[str, Any]] = [
    {
        "letter": "S",
        "name": "Single Responsibility Principle",
        "summary": "A class should have one, and only one, reason to change.",
        "bad_example": {
            "python": (
                "class UserReport:\n"
                "    def generate_report(self, user_id: str) -> str:\n"
                "        return f'Report for {user_id}'\n\n"
                "    def save_to_database(self, data: str) -> None:\n"
                "        # Direct DB connection and queries\n"
                "        pass\n\n"
                "    def send_email_notification(self, email: str) -> None:\n"
                "        # SMTP socket operations\n"
                "        pass\n"
            ),
            "java": "// Bad: mixing data parsing, persistence, and network transport in one God class\n",
            "cpp": "// Bad: multi-responsibility class coupled to DB, UI, and filesystem\n",
            "typescript": "// Bad: single service handling auth, billing, email, and logging\n",
        },
        "good_example": {
            "python": (
                "class UserReportGenerator:\n"
                "    def generate(self, user_id: str) -> str:\n"
                "        return f'Report for {user_id}'\n\n"
                "class ReportRepository:\n"
                "    def save(self, report_data: str) -> None:\n"
                "        pass\n\n"
                "class NotificationDispatcher:\n"
                "    def notify_user(self, email: str, report: str) -> None:\n"
                "        pass\n"
            ),
            "java": "// Good: Separated into ReportGenerator, ReportStore, and EmailService\n",
            "cpp": "// Good: decoupled modules with cohesive, single-purpose roles\n",
            "typescript": "// Good: Dedicated classes for formatting, storage, and notifications\n",
        },
        "benefits": [
            "Lower coupling and higher cohesion across components.",
            "Isolated unit tests that verify domain logic without mocking entire external infrastructures.",
            "Easier maintenance as feature changes affect only the corresponding single-responsibility module.",
        ],
    },
    {
        "letter": "O",
        "name": "Open/Closed Principle",
        "summary": "Software entities should be open for extension, but closed for modification.",
        "bad_example": {
            "python": (
                "class DiscountCalculator:\n"
                "    def calculate(self, order_type: str, amount: float) -> float:\n"
                "        if order_type == 'REGULAR': return amount * 0.95\n"
                "        elif order_type == 'VIP': return amount * 0.85\n"
                "        elif order_type == 'BLACK_FRIDAY': return amount * 0.70\n"
                "        # Adding a new discount requires editing existing tested code!\n"
            ),
            "java": "// Bad: chained if/else or switch-case over types that require edits on every new feature\n",
            "cpp": "// Bad: modifying production classes to add variant algorithms\n",
            "typescript": "// Bad: switch statement over polymorphic actions requiring frequent modification\n",
        },
        "good_example": {
            "python": (
                "from abc import ABC, abstractmethod\n\n"
                "class DiscountStrategy(ABC):\n"
                "    @abstractmethod\n"
                "    def apply(self, amount: float) -> float: pass\n\n"
                "class VIPDiscount(DiscountStrategy):\n"
                "    def apply(self, amount: float) -> float: return amount * 0.85\n\n"
                "class BlackFridayDiscount(DiscountStrategy):\n"
                "    def apply(self, amount: float) -> float: return amount * 0.70\n"
            ),
            "java": "// Good: Polymorphic Strategy pattern where new tiers are added by creating new classes\n",
            "cpp": "// Good: extension via inheritance or templates without editing existing core\n",
            "typescript": "// Good: Implement DiscountRule interface for every new discount type\n",
        },
        "benefits": [
            "Minimizes regression risk in battle-tested production routines.",
            "Enables plug-and-play architecture for new business rules.",
        ],
    },
    {
        "letter": "L",
        "name": "Liskov Substitution Principle",
        "summary": "Subtypes must be substitutable for their base types without altering program correctness.",
        "bad_example": {
            "python": (
                "class Rectangle:\n"
                "    def __init__(self, w: float, h: float):\n"
                "        self.w, self.h = w, h\n"
                "    def set_width(self, w: float): self.w = w\n"
                "    def set_height(self, h: float): self.h = h\n\n"
                "class Square(Rectangle):\n"
                "    def set_width(self, w: float):\n"
                "        self.w = self.h = w  # Breaks invariant expected by caller!\n"
            ),
            "java": "// Bad: Square extending Rectangle and mutating both dimensions in setWidth\n",
            "cpp": "// Bad: Subclass throwing UnexpectedException on base virtual method\n",
            "typescript": "// Bad: Child class overriding method to reject valid parent inputs\n",
        },
        "good_example": {
            "python": (
                "class Shape(ABC):\n"
                "    @abstractmethod\n"
                "    def area(self) -> float: pass\n\n"
                "class Rectangle(Shape):\n"
                "    def __init__(self, w: float, h: float): self.w, self.h = w, h\n"
                "    def area(self) -> float: return self.w * self.h\n\n"
                "class Square(Shape):\n"
                "    def __init__(self, side: float): self.side = side\n"
                "    def area(self) -> float: return self.side ** 2\n"
            ),
            "java": "// Good: Both implement Shape interface independently with valid contracts\n",
            "cpp": "// Good: Shape base contract with no invalid dimension mutation assumptions\n",
            "typescript": "// Good: Clear interface without contradictory state invariants\n",
        },
        "benefits": [
            "Predictable polymorphism without unexpected runtime crashes.",
            "Honors preconditions, postconditions, and invariants.",
        ],
    },
    {
        "letter": "I",
        "name": "Interface Segregation Principle",
        "summary": "Clients should not be forced to depend on interfaces they do not use.",
        "bad_example": {
            "python": (
                "class Worker(ABC):\n"
                "    @abstractmethod\n"
                "    def code(self): pass\n"
                "    @abstractmethod\n"
                "    def manage_budget(self): pass\n"
                "    @abstractmethod\n"
                "    def write_tests(self): pass\n"
                "# An intern coder is forced to implement manage_budget()!\n"
            ),
            "java": "// Bad: Fat interface forcing implementors to throw UnsupportedOperationException\n",
            "cpp": "// Bad: bloated pure virtual interface\n",
            "typescript": "// Bad: Giant interface with dozens of unrelated method signatures\n",
        },
        "good_example": {
            "python": (
                "class CodeDeveloper(ABC):\n"
                "    @abstractmethod\n"
                "    def code(self): pass\n\n"
                "class BudgetManager(ABC):\n"
                "    @abstractmethod\n"
                "    def manage_budget(self): pass\n"
            ),
            "java": "// Good: Fine-grained interfaces: Codable, BudgetManageable\n",
            "cpp": "// Good: small composable abstract mixin interfaces\n",
            "typescript": "// Good: Focused interfaces composed with TypeScript intersection types\n",
        },
        "benefits": [
            "Eliminates empty or throwing dummy methods.",
            "Keeps module interfaces lean, readable, and decoupled.",
        ],
    },
    {
        "letter": "D",
        "name": "Dependency Inversion Principle",
        "summary": "High-level modules should not depend on low-level modules. Both should depend on abstractions.",
        "bad_example": {
            "python": (
                "class MySQLDatabase:\n"
                "    def save(self, data: str): pass\n\n"
                "class OrderService:\n"
                "    def __init__(self):\n"
                "        self.db = MySQLDatabase()  # Tightly coupled to concrete implementation!\n"
            ),
            "java": "// Bad: directly instantiating low-level SQL connection in business layer\n",
            "cpp": "// Bad: hardcoded concrete dependency in constructor\n",
            "typescript": "// Bad: hardcoding concrete AWS S3 client in file upload handler\n",
        },
        "good_example": {
            "python": (
                "class DatabaseStorage(ABC):\n"
                "    @abstractmethod\n"
                "    def save(self, data: str): pass\n\n"
                "class OrderService:\n"
                "    def __init__(self, storage: DatabaseStorage):\n"
                "        self.storage = storage  # Injected abstraction!\n"
            ),
            "java": "// Good: Dependency injection via interface in constructor\n",
            "cpp": "// Good: Inversion of Control via unique_ptr<StorageInterface>\n",
            "typescript": "// Good: Injected StorageProvider via constructor or IoC container\n",
        },
        "benefits": [
            "Seamless swapping of databases, 3rd party providers, and cache tiers.",
            "Trivial mocking during automated unit and integration testing.",
        ],
    },
]

OOP_PATTERNS_DATA: list[dict[str, Any]] = [
    {
        "name": "Factory Method",
        "category": "CREATIONAL",
        "intent": "Defines an interface for creating an object, but lets subclasses or creator functions decide which class to instantiate.",
        "use_cases": [
            "Cross-platform UI element generation (ButtonFactory -> WindowsButton, MacButton).",
            "Document export pipelines (PDF, Markdown, HTML converters).",
            "Database connection factories configured by environment variables.",
        ],
        "structure_diagram_mermaid": "classDiagram\n  Creator <|-- ConcreteCreator\n  Product <|-- ConcreteProduct",
        "implementation": {
            "python": (
                "from abc import ABC, abstractmethod\n\n"
                "class Notification(ABC):\n"
                "    @abstractmethod\n"
                "    def send(self, recipient: str, msg: str) -> None: pass\n\n"
                "class SMSNotification(Notification):\n"
                "    def send(self, recipient: str, msg: str) -> None:\n"
                "        print(f'Sending SMS to {recipient}: {msg}')\n\n"
                "class EmailNotification(Notification):\n"
                "    def send(self, recipient: str, msg: str) -> None:\n"
                "        print(f'Sending Email to {recipient}: {msg}')\n\n"
                "class NotificationFactory:\n"
                "    @staticmethod\n"
                "    def create(channel: str) -> Notification:\n"
                "        registry = {\n"
                "            'sms': SMSNotification,\n"
                "            'email': EmailNotification,\n"
                "        }\n"
                "        target = registry.get(channel.lower())\n"
                "        if not target:\n"
                "            raise ValueError(f'Unsupported channel: {channel}')\n"
                "        return target()\n"
            ),
            "java": (
                "public abstract class NotificationFactory {\n"
                "    public abstract Notification createNotification();\n"
                "}\n"
            ),
            "cpp": (
                "class NotificationFactory {\n"
                "public:\n"
                "    static std::unique_ptr<Notification> create(const std::string& type);\n"
                "};\n"
            ),
            "typescript": (
                "export class NotificationFactory {\n"
                "  public static create(type: 'sms' | 'email'): Notification {\n"
                "    return type === 'sms' ? new SMSNotification() : new EmailNotification();\n"
                "  }\n"
                "}\n"
            ),
        },
        "tradeoffs": [
            "Eliminates tight coupling to concrete classes.",
            "Can introduce extra boilerplate classes for simple object setups.",
        ],
    },
    {
        "name": "Singleton",
        "category": "CREATIONAL",
        "intent": "Ensures a class has only one instance and provides a global access point to it.",
        "use_cases": [
            "Hardware thread pools and connection connection managers.",
            "Global application telemetry and logger registry.",
            "Configuration managers loaded once on startup.",
        ],
        "structure_diagram_mermaid": "classDiagram\n  class Singleton {\n    -instance: Singleton\n    +getInstance(): Singleton\n  }",
        "implementation": {
            "python": (
                "class DatabaseConnectionPool:\n"
                "    _instance = None\n\n"
                "    def __new__(cls, *args, **kwargs):\n"
                "        if not cls._instance:\n"
                "            cls._instance = super().__new__(cls)\n"
                "            cls._instance.connections = 10\n"
                "        return cls._instance\n"
            ),
            "java": (
                "public class DatabasePool {\n"
                "    private static volatile DatabasePool instance;\n"
                "    private DatabasePool() {}\n"
                "    public static DatabasePool getInstance() {\n"
                "        if (instance == null) {\n"
                "            synchronized (DatabasePool.class) {\n"
                "                if (instance == null) instance = new DatabasePool();\n"
                "            }\n"
                "        }\n"
                "        return instance;\n"
                "    }\n"
                "}\n"
            ),
            "cpp": (
                "class DatabasePool {\n"
                "public:\n"
                "    static DatabasePool& getInstance() {\n"
                "        static DatabasePool instance;\n"
                "        return instance;\n"
                "    }\n"
                "private:\n"
                "    DatabasePool() = default;\n"
                "};\n"
            ),
            "typescript": (
                "export class DatabasePool {\n"
                "  private static instance: DatabasePool;\n"
                "  private constructor() {}\n"
                "  public static getInstance(): DatabasePool {\n"
                "    if (!this.instance) this.instance = new DatabasePool();\n"
                "    return this.instance;\n"
                "  }\n"
                "}\n"
            ),
        },
        "tradeoffs": [
            "Guarantees single instance across process lifecycle.",
            "Can mask tight coupling and make unit test parallelism challenging if state is mutable.",
        ],
    },
    {
        "name": "Adapter",
        "category": "STRUCTURAL",
        "intent": "Converts the interface of a class into another interface clients expect, enabling incompatible classes to cooperate.",
        "use_cases": [
            "Integrating modern cloud telemetry into legacy logging systems.",
            "Normalizing third-party payment gateway callbacks (Stripe vs PayPal vs Razorpay).",
            "Wrapping legacy C libraries inside modern C++ or Python object APIs.",
        ],
        "structure_diagram_mermaid": "classDiagram\n  Target <|-- Adapter\n  Adapter --> Adaptee",
        "implementation": {
            "python": (
                "class LegacyLogger:\n"
                "    def log_xml(self, xml_payload: str):\n"
                "        print(f'Legacy log: {xml_payload}')\n\n"
                "class ModernLogger(ABC):\n"
                "    @abstractmethod\n"
                "    def log(self, message: str) -> None: pass\n\n"
                "class LegacyLoggerAdapter(ModernLogger):\n"
                "    def __init__(self, legacy: LegacyLogger):\n"
                "        self.legacy = legacy\n\n"
                "    def log(self, message: str) -> None:\n"
                "        xml_formatted = f'<entry><msg>{message}</msg></entry>'\n"
                "        self.legacy.log_xml(xml_formatted)\n"
            ),
            "java": "// Java Adapter implementing ModernLogger wrapping LegacyLogger\n",
            "cpp": "// C++ Adapter inheriting from Target and holding Adaptee pointer\n",
            "typescript": "// TypeScript Adapter wrapping legacy API into modern Promise interface\n",
        },
        "tradeoffs": [
            "Separates interface or data conversion code from primary business logic.",
            "Adds slight architectural overhead compared to rewriting the client directly.",
        ],
    },
    {
        "name": "Decorator",
        "category": "STRUCTURAL",
        "intent": "Attaches additional responsibilities to an object dynamically without altering its structure.",
        "use_cases": [
            "Adding metrics/timing and caching transparently to repository calls.",
            "Applying middleware layers (auth, compression, encryption) to HTTP request handlers.",
            "Dynamic UI component wrappers (BorderDecorator, ScrollDecorator).",
        ],
        "structure_diagram_mermaid": "classDiagram\n  Component <|-- Decorator\n  Decorator --> Component",
        "implementation": {
            "python": (
                "import time\n\n"
                "class DataFetcher(ABC):\n"
                "    @abstractmethod\n"
                "    def fetch(self, query: str) -> str: pass\n\n"
                "class RealDataFetcher(DataFetcher):\n"
                "    def fetch(self, query: str) -> str:\n"
                "        return f'Result for {query}'\n\n"
                "class TimingDecorator(DataFetcher):\n"
                "    def __init__(self, wrapped: DataFetcher):\n"
                "        self.wrapped = wrapped\n\n"
                "    def fetch(self, query: str) -> str:\n"
                "        start = time.perf_counter()\n"
                "        result = self.wrapped.fetch(query)\n"
                "        print(f'Execution took {time.perf_counter() - start:.4f}s')\n"
                "        return result\n"
            ),
            "java": "// Java decorator wrapping Component and delegating calls\n",
            "cpp": "// C++ decorator wrapping unique_ptr<Component>\n",
            "typescript": "// TypeScript decorator wrapping service interface\n",
        },
        "tradeoffs": [
            "Greater flexibility than static inheritance.",
            "Can result in many small decorator wrapper layers that complicate debugging.",
        ],
    },
    {
        "name": "Strategy",
        "category": "BEHAVIORAL",
        "intent": "Defines a family of algorithms, encapsulates each one, and makes them interchangeable at runtime.",
        "use_cases": [
            "Route planning algorithms (Fastest, Shortest, Scenic, Avoid Tolls).",
            "Data compression codecs (GZIP, Snappy, Zstandard, LZ4).",
            "Dynamic sorting or pricing rules in e-commerce checkout.",
        ],
        "structure_diagram_mermaid": "classDiagram\n  Strategy <|-- ConcreteStrategyA\n  Strategy <|-- ConcreteStrategyB\n  Context --> Strategy",
        "implementation": {
            "python": (
                "class CompressionStrategy(ABC):\n"
                "    @abstractmethod\n"
                "    def compress(self, data: bytes) -> bytes: pass\n\n"
                "class ZipCompression(CompressionStrategy):\n"
                "    def compress(self, data: bytes) -> bytes:\n"
                "        return b'ZIP:' + data\n\n"
                "class Lz4Compression(CompressionStrategy):\n"
                "    def compress(self, data: bytes) -> bytes:\n"
                "        return b'LZ4:' + data\n\n"
                "class ArchiveCompressor:\n"
                "    def __init__(self, strategy: CompressionStrategy):\n"
                "        self.strategy = strategy\n\n"
                "    def process(self, files: bytes) -> bytes:\n"
                "        return self.strategy.compress(files)\n"
            ),
            "java": "// Java Strategy pattern with runtime algorithm injection\n",
            "cpp": "// C++ Strategy with runtime polymorphism or template policies\n",
            "typescript": "// TypeScript Strategy interface with interchangeable handler objects\n",
        },
        "tradeoffs": [
            "Isolates algorithmic implementation details from consuming context.",
            "Eliminates complex conditional statements (switch / if-else branches).",
        ],
    },
    {
        "name": "Observer",
        "category": "BEHAVIORAL",
        "intent": "Defines a one-to-many dependency between objects so that when one changes state, all its dependents are notified automatically.",
        "use_cases": [
            "Event-driven UI state management (React / Vue reactivity, Redux listeners).",
            "Stock exchange order books broadcasting price ticks to trading terminals.",
            "Pub/Sub event busses triggering asynchronous background jobs.",
        ],
        "structure_diagram_mermaid": "classDiagram\n  Subject --> Observer\n  Observer <|-- ConcreteObserver",
        "implementation": {
            "python": (
                "class StockObserver(ABC):\n"
                "    @abstractmethod\n"
                "    def update(self, ticker: str, price: float) -> None: pass\n\n"
                "class StockMarket:\n"
                "    def __init__(self):\n"
                "        self._observers: list[StockObserver] = []\n\n"
                "    def subscribe(self, observer: StockObserver) -> None:\n"
                "        self._observers.append(observer)\n\n"
                "    def notify(self, ticker: str, price: float) -> None:\n"
                "        for obs in self._observers:\n"
                "            obs.update(ticker, price)\n"
            ),
            "java": "// Java Observer pattern with PropertyChangeListener or custom subscribers\n",
            "cpp": "// C++ Observer pattern using std::vector<std::weak_ptr<Observer>>\n",
            "typescript": "// TypeScript EventEmitter / Subscriber implementation\n",
        },
        "tradeoffs": [
            "Enables loose coupling between subject and subscribers.",
            "Subscribers must be unsubscribed when destroyed to prevent memory leaks.",
        ],
    },
]

OOP_CURRICULUM_MODULES: list[dict[str, Any]] = [
    {
        "id": "oop-encapsulation",
        "title": "Encapsulation & Information Hiding",
        "category": "PILLARS",
        "summary": "Bundling data with methods that operate on that data and restricting direct access to object internals.",
        "key_concepts": [
            "Private/Protected access modifiers",
            "Getters and Setters",
            "Invariants preservation",
            "Data hiding",
        ],
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
        "key_concepts": [
            "Method overriding",
            "Dynamic dispatch",
            "Abstract Base Classes (ABCs)",
            "Subtype polymorphism",
        ],
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
        "key_concepts": [
            "Has-a vs Is-a relationships",
            "Delegation",
            "Loose coupling",
            "Runtime flexibility",
        ],
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
        "key_concepts": [
            "Factory Method",
            "Strategy Pattern",
            "Observer Pattern",
            "Decorator Pattern",
        ],
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
    """Delivers OOP learning modules, GoF patterns, and SOLID guides."""

    @classmethod
    def list_modules(cls) -> list[OOPModule]:
        """Returns all structured OOP learning modules."""
        return [OOPModule(**m) for m in OOP_CURRICULUM_MODULES]

    @classmethod
    def get_module(cls, module_id: str) -> OOPModule | None:
        """Retrieves an individual OOP module by ID."""
        for m in OOP_CURRICULUM_MODULES:
            if m["id"] == module_id:
                return OOPModule(**m)
        return None

    @classmethod
    def get_pillars(cls) -> list[OOPPillar]:
        """Returns the Four Pillars of OOP."""
        return [OOPPillar(**p) for p in OOP_PILLARS_DATA]

    @classmethod
    def get_solid_principles(cls) -> list[SOLIDPrinciple]:
        """Returns the five SOLID software design principles."""
        return [SOLIDPrinciple(**s) for s in OOP_SOLID_DATA]

    @classmethod
    def get_design_patterns(cls) -> list[OOPDesignPattern]:
        """Returns the Gang of Four design patterns."""
        return [OOPDesignPattern(**dp) for dp in OOP_PATTERNS_DATA]

    @classmethod
    def get_overview(cls) -> OOPOverview:
        """Returns the consolidated OOP overview for the frontend."""
        return OOPOverview(
            pillars=cls.get_pillars(),
            solid_principles=cls.get_solid_principles(),
            design_patterns=cls.get_design_patterns(),
        )
