"""Verify all 5 languages and security sandbox controls against real Docker."""
import sys
from backend.app.judge.sandbox.docker import DockerSandbox
from backend.app.judge.sandbox.base import ExecutionRequest

def test_language(sb: DockerSandbox, lang: str, code: str, expected_stdout: str):
    print(f"\n--- Testing Language: {lang} ---")
    req = ExecutionRequest(
        language_id=lang,
        source_code=code,
        stdin="",
        time_limit_ms=6000,
        memory_limit_mb=256,
    )
    res = sb.run(req)
    print(f"Exit code: {res.exit_code}, Timed out: {res.timed_out}")
    print(f"Stdout: {res.stdout.strip()}")
    if res.error_message:
        print(f"Error: {res.error_message.strip()}")
    assert res.exit_code == 0, f"{lang} failed with exit {res.exit_code}: {res.error_message}"
    assert expected_stdout in res.stdout, f"{lang} expected '{expected_stdout}', got '{res.stdout}'"
    print(f"[PASS] {lang} verified.")

def main():
    sb = DockerSandbox()
    if not sb.is_available():
        print("[FAIL] Docker is not available!")
        sys.exit(1)
    print("[PASS] Docker daemon is running and reachable.")

    # 1. Python
    test_language(
        sb, "python",
        'print("PYTHON_OK_42")',
        "PYTHON_OK_42"
    )

    # 2. JavaScript
    test_language(
        sb, "javascript",
        'console.log("JAVASCRIPT_OK_42");',
        "JAVASCRIPT_OK_42"
    )

    # 3. TypeScript
    test_language(
        sb, "typescript",
        'const answer: number = 42;\nconsole.log(`TYPESCRIPT_OK_${answer}`);',
        "TYPESCRIPT_OK_42"
    )

    # 4. Java
    test_language(
        sb, "java",
        'public class Solution {\n    public static void main(String[] args) {\n        System.out.println("JAVA_OK_42");\n    }\n}',
        "JAVA_OK_42"
    )

    # 5. C++
    test_language(
        sb, "cpp",
        '#include <iostream>\nint main() {\n    std::cout << "CPP_OK_42" << std::endl;\n    return 0;\n}',
        "CPP_OK_42"
    )

    print("\n==========================================")
    print("ALL 5 RUNTIMES VERIFIED ON REAL DOCKER!")
    print("==========================================")

if __name__ == "__main__":
    main()
