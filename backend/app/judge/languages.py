"""Controlled Language Registry for Online Judge execution.

Defines verified runtimes, compilers, flags, and source extensions.
Client-supplied compile or runtime commands are strictly forbidden.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LanguageDefinition:
    """Immutable configuration for a supported judge programming language."""
    language_id: str
    display_name: str
    source_filename: str
    is_compiled: bool
    compile_command: Optional[List[str]]
    run_command: List[str]
    default_time_limit_ms: int
    default_memory_limit_mb: int
    docker_image: str


# Controlled, immutable language registry.
# Dynamic client command injection is strictly prohibited.
LANGUAGE_REGISTRY: Dict[str, LanguageDefinition] = {
    "python": LanguageDefinition(
        language_id="python",
        display_name="Python 3.12",
        source_filename="solution.py",
        is_compiled=False,
        compile_command=None,
        run_command=["python3", "solution.py"],
        default_time_limit_ms=2000,
        default_memory_limit_mb=256,
        docker_image="dsaapp-judge-python:latest",
    ),
    "cpp": LanguageDefinition(
        language_id="cpp",
        display_name="C++20 (GCC 13)",
        source_filename="solution.cpp",
        is_compiled=True,
        compile_command=["g++", "-O3", "-std=c++20", "-Wall", "solution.cpp", "-o", "solution"],
        run_command=["./solution"],
        default_time_limit_ms=1000,
        default_memory_limit_mb=256,
        docker_image="dsaapp-judge-cpp:latest",
    ),
    "java": LanguageDefinition(
        language_id="java",
        display_name="Java 17 (OpenJDK)",
        source_filename="Solution.java",
        is_compiled=True,
        compile_command=["javac", "Solution.java"],
        run_command=["java", "-Xmx256m", "-Xss64m", "-XX:+UseSerialGC", "Solution"],
        default_time_limit_ms=2000,
        default_memory_limit_mb=256,
        docker_image="dsaapp-judge-java:latest",
    ),
    "javascript": LanguageDefinition(
        language_id="javascript",
        display_name="JavaScript (Node.js 20)",
        source_filename="solution.js",
        is_compiled=False,
        compile_command=None,
        run_command=["node", "--max-old-space-size=256", "solution.js"],
        default_time_limit_ms=2000,
        default_memory_limit_mb=256,
        docker_image="dsaapp-judge-javascript:latest",
    ),
    "typescript": LanguageDefinition(
        language_id="typescript",
        display_name="TypeScript 5.x",
        source_filename="solution.ts",
        is_compiled=True,
        compile_command=["tsc", "--target", "ES2022", "--module", "commonjs", "solution.ts"],
        run_command=["node", "--max-old-space-size=256", "solution.js"],
        default_time_limit_ms=2000,
        default_memory_limit_mb=256,
        docker_image="dsaapp-judge-typescript:latest",
    ),
}


def get_language_definition(language_id: str) -> Optional[LanguageDefinition]:
    """Retrieves language configuration by case-insensitive ID."""
    return LANGUAGE_REGISTRY.get(language_id.strip().lower())


def is_language_supported(language_id: str) -> bool:
    """Checks if language is part of the controlled registry."""
    return language_id.strip().lower() in LANGUAGE_REGISTRY
