# Judge Languages & Runtime Registry (Phase 5)

## 1. Controlled Runtimes

All compilation and execution commands are strictly predefined in `backend/app/judge/languages.py`. Client-supplied commands or parameters are strictly forbidden.

| Language | Version / Toolchain | Docker Image | Source File | Compile Command | Default Run Command | Default Limits |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Python** | Python 3.12 (Alpine) | `dsaapp-judge-python:latest` | `solution.py` | *None (Interpreted)* | `python3 solution.py` | 2000 ms, 256 MB |
| **C++** | C++20 (GCC 13) | `dsaapp-judge-cpp:latest` | `solution.cpp` | `g++ -O3 -std=c++20 -Wall solution.cpp -o solution` | `./solution` | 1000 ms, 256 MB |
| **Java** | Java 17 (OpenJDK) | `dsaapp-judge-java:latest` | `Solution.java` | `javac Solution.java` | `java -Xmx256m -XX:+UseSerialGC Solution` | 2000 ms, 256 MB |
| **JavaScript** | Node.js 20 (Alpine) | `dsaapp-judge-javascript:latest` | `solution.js` | *None (Interpreted)* | `node --max-old-space-size=256 solution.js` | 2000 ms, 256 MB |
| **TypeScript** | TypeScript 5.x | `dsaapp-judge-typescript:latest` | `solution.ts` | `tsc --target ES2022 --module commonjs solution.ts` | `node --max-old-space-size=256 solution.js` | 2000 ms, 256 MB |

---

## 2. Dockerfiles

Sandbox container definitions are located in `infra/judge/`:
- `infra/judge/python/Dockerfile`
- `infra/judge/cpp/Dockerfile`
- `infra/judge/java/Dockerfile`
- `infra/judge/javascript/Dockerfile`
- `infra/judge/typescript/Dockerfile`
