"""Tests for controlled language registry."""

import pytest
from backend.app.judge.languages import (
    LANGUAGE_REGISTRY,
    get_language_definition,
    is_language_supported,
)


def test_language_registry_supported_runtimes():
    expected_languages = ["python", "cpp", "java", "javascript", "typescript"]
    for lang in expected_languages:
        assert is_language_supported(lang)
        defn = get_language_definition(lang)
        assert defn is not None
        assert defn.language_id == lang
        assert defn.docker_image.startswith("dsaapp-judge-")
        assert len(defn.run_command) > 0


def test_language_registry_compiled_vs_interpreted():
    py_def = get_language_definition("python")
    assert py_def.is_compiled is False
    assert py_def.compile_command is None

    cpp_def = get_language_definition("cpp")
    assert cpp_def.is_compiled is True
    assert cpp_def.compile_command == ["g++", "-O3", "-std=c++20", "-Wall", "solution.cpp", "-o", "solution"]

    java_def = get_language_definition("java")
    assert java_def.is_compiled is True
    assert java_def.compile_command == ["javac", "Solution.java"]


def test_language_registry_case_insensitivity_and_rejections():
    assert is_language_supported("PYTHON") is True
    assert is_language_supported("  Cpp  ") is True
    assert is_language_supported("bash") is False
    assert is_language_supported("php") is False
    assert get_language_definition("ruby") is None
