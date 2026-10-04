DSAapp — Full-Stack AI-Powered DSA Learning & Coding Platform

<p align="center">
  <strong>Learn • Practice • Code • Analyze • Prepare • Improve</strong>
</p>

<p align="center">
  A full-stack AI-powered Data Structures & Algorithms learning, coding,
  interview preparation, competitive programming, and skill-development platform
  built with React, TypeScript, FastAPI, Python, PostgreSQL, SQLAlchemy, and Alembic.
</p>

<p align="center">
  <a href="https://dsa-applogics.up.railway.app">🌐 Live Application</a> •
  <a href="https://dsaapp-production.up.railway.app">⚙️ Backend API</a> •
  <a href="https://github.com/venkatsubbarao123/DSAapp">💻 GitHub Repository</a>
</p>

📌 Project Overview

DSAapp is a production-deployed full-stack AI-powered DSA learning and coding platform engineered around a 20% Theory / 80% Practice learning model.

The platform combines structured DSA education, hands-on coding practice, AI-assisted learning, progress tracking, adaptive revision, interview preparation, competitive programming, contests, gamification, SQL practice, OOP and Design Patterns, administration, analytics, notifications, and PWA capabilities in one integrated application.

The system is designed as a real-world full-stack application with a React/TypeScript frontend, FastAPI/Python backend, PostgreSQL production database, SQLAlchemy data layer, Alembic migrations, secure authentication, REST APIs, and Railway-based deployment.

🚀 Current Production Status

The application is currently deployed with separate frontend and backend services on Railway and PostgreSQL as the production persistent database.

Layer

Current Status

Production Details

Frontend

LIVE

React + TypeScript + Vite on Railway

Backend

LIVE

FastAPI + Python on Railway

Database

CONNECTED

PostgreSQL on Railway

API Health

HEALTHY

Backend health endpoint verified

DSA Content

SYNCED

415 source problems available in production content

CORS

CONFIGURED

Production frontend origin configured

PWA

IMPLEMENTED

Manifest/service-worker based application experience

Redis

FALLBACK

In-memory fallback currently active rather than an active Redis service

Production status in this README reflects the current deployed architecture. Features that are documented in the application source but are not currently enabled in the production environment are not represented as active production infrastructure.

✨ Core Platform Features

1. Foundation & API Gateway

FastAPI application gateway

RESTful API architecture

Correlation/request IDs

Structured JSON logging

Security headers

Request-size protection

Health and diagnostic endpoints

Centralized configuration

Validation and error handling

Production CORS configuration

2. Authentication & Authorization

The platform includes production-oriented authentication and authorization architecture.

Authentication

User registration

Secure password hashing using Argon2id

JWT access-token architecture

Refresh-token architecture

Secure refresh-token cookie configuration

Session/token lifecycle management

Authorization

Role-based access control (RBAC)

Server-side authorization checks

Protected API operations

Admin/content-management permissions

Sensitive-operation protection

Security Controls

CORS restrictions

Allowed-host validation

Security headers

Request validation

Audit logging

Environment-based secrets

No browser exposure of sensitive backend credentials

📚 3. Curriculum & Content Management

The learning system follows a structured hierarchy:

Track
  ↓
Topic
  ↓
Subtopic
  ↓
Lesson
  ↓
Concept
  ↓
Problem
  ↓
Examples / Hints / Test Cases

The content system supports:

Tracks

Topics

Subtopics

Lessons

Concepts

Problems

Examples

Hints

Test cases

Patterns

Tags

Code templates

Content authoring workflows

Admin/editor content management

🧩 4. DSA Problem Library

The platform contains a structured problem library of 415 DSA problems.

Difficulty

Problems

Easy

144

Medium

186

Hard

85

Total

415

Problems are supported with associated:

Examples

Hints

Test cases

Patterns

Tags

Metadata

Programming-language templates

Users can discover problems through topics, difficulty, patterns, search, and practice workflows.

📈 5. Progress Tracking & Revision

The platform tracks learning progress across problems and lessons.

Progress Features

Problem progress

Lesson progress

Submission history

Accuracy tracking

Mistake tracking

Cognitive mistake classification

Revision workflows

Weak-area identification

Spaced repetition

Revision Models

The project architecture includes:

Leitner-style revision

SM-2 spaced-repetition intervals

This allows users to revisit concepts and problems based on their learning history rather than following only a fixed sequence.

💻 6. Online Judge & Secure Code Execution

The project includes a secure online-judge architecture designed around isolated execution.

Supported programming languages include:

Python

Java

C++

JavaScript

The judge architecture uses Docker-based isolation with resource controls and security boundaries.

User Code
   ↓
FastAPI Submission API
   ↓
Submission Validation
   ↓
Judge / Worker Layer
   ↓
Isolated Docker Sandbox
   ↓
Compile / Execute
   ↓
Test Cases
   ↓
Verdict
   ↓
Submission Result

Security principles

Untrusted code is not executed directly inside the FastAPI application process.

Resource limits are applied by the sandbox architecture.

Judge failures are designed to fail closed rather than fabricate successful verdicts.

Production execution capability depends on deployment infrastructure supporting Docker.

🤖 7. AI Tutor & AI-Powered Learning

DSAapp includes AI-assisted learning workflows designed to help users learn instead of simply receiving final answers.

AI Tutor capabilities

Guided problem solving

Multi-turn tutoring

Progressive hints

Concept explanations

Complexity analysis

Problem-solving assistance

Learning-oriented feedback

AI architecture

React Frontend
      ↓
FastAPI AI API
      ↓
Server-side AI Provider
      ↓
AI Response / Learning Guidance
      ↓
Frontend

AI provider credentials remain server-side and are supplied through deployment environment variables.

📊 8. Algorithm Visualizers

Interactive visual learning is included for algorithm and data-structure concepts.

The visualizer layer is designed to help users understand algorithm execution step-by-step rather than relying only on static explanations.

🎯 9. Adaptive Practice Engine

DSAapp provides multiple practice modes:

Mode

Purpose

QUICK

Fast general practice

TOPIC

Practice a selected topic

PATTERN

Practice a specific DSA pattern

DIFFICULTY

Practice by difficulty

WEAK_AREA

Target weak skills

MISTAKES

Revisit previous mistakes

REVISION

Spaced-revision practice

The practice engine can use learning history and user performance to guide practice selection.

🏆 10. Gamification

The platform includes server-authoritative gamification capabilities.

Gamification components

XP

Levels

Daily streaks

Skill ratings

Achievements

Leaderboards

Learning milestones

The application uses server-side state for important gamification operations to reduce client-side manipulation.

📅 11. Daily Challenges

Daily learning activities are supported through challenge-oriented content and progress tracking.

Daily challenges integrate with the wider practice, progress, streak, XP, and achievement systems.

🏁 12. Contest Arena

The project includes a contest architecture with server-authoritative contest lifecycle management.

Capabilities include:

Contest lifecycle

Contest problems

Time-bound participation

ICPC-style scoring/penalty concepts

Submission throttling

Anti-cheat-oriented controls

Code similarity detection architecture

Contest ranking

Where Redis is enabled, caching/coordination can be used by contest-related infrastructure; the current production environment uses the configured fallback where Redis is unavailable.

🎤 13. AI Interview Simulator

The platform includes an AI-powered interview preparation workflow.

Interview capabilities

Multiple interview tracks

Session-based interviews

Countdown/timing architecture

Interview questions

AI-assisted interaction

Multi-dimensional scoring

Interview reports

Performance feedback

The interview system is designed to simulate realistic technical interview preparation rather than functioning only as a static question bank.

🏅 14. Competitive Programming

Competitive programming features include:

Competitive problem catalogue

Rating bands

Rating tracking

Contest participation

Competitive performance tracking

The architecture supports separate competitive-rating concepts from the general learning/gamification system.

🧮 15. Interactive SQL Learning

DSAapp includes an interactive SQL practice environment.

The SQL learning architecture uses an isolated SQLite execution model with query validation/firewall controls.

Security-oriented restrictions include rejection of:

Non-SELECT operations

System-catalog access

Chained/multi-statement queries

The goal is to provide hands-on SQL practice without exposing the main production database.

🏗️ 16. OOP & Design Patterns

The OOP learning module covers:

OOP

Four pillars of OOP

Encapsulation

Abstraction

Inheritance

Polymorphism

Design Principles

SOLID principles

Refactoring concepts

Code-quality practices

Design Patterns

Gang of Four patterns

Python examples

Java examples

C++ examples

TypeScript examples

👨‍💼 17. Admin & Governance

The platform contains administrative and governance capabilities for managing the learning ecosystem.

Features include:

User directory

User management

Role-based administrative access

Content management

Problem management

Test-case management

Publishing workflows

Platform diagnostics

Audit trail

Governance controls

Sensitive administrative operations are protected by server-side authorization.

📊 18. Platform Analytics

The analytics layer provides database-driven platform metrics across multiple subsystems.

Analytics areas include:

Learning analytics

User analytics

Practice analytics

Gamification analytics

Contest analytics

Interview analytics

SQL analytics

OOP analytics

Judge analytics

AI analytics

Premium/payment-related monitoring

System health

The analytics architecture is intended to derive metrics from authoritative application data rather than fabricate client-side values.

🔔 19. Notifications

The notification system supports:

In-app notifications

Unread notification counts

Notification preferences

Transactional email architecture

Deduplication keys

Notification delivery tracking

Administrative broadcasts

Multi-channel notification architecture

📱 20. Progressive Web App (PWA)

DSAapp includes PWA capabilities for a more app-like web experience.

Components include:

Web App Manifest

Service Worker

Static asset caching

Offline shell

Update handling

Install experience

Network-only handling for sensitive API operations

🏗️ 21. Full-Stack Architecture

                         USER
                           │
                           ▼
              ┌────────────────────────┐
              │ React + TypeScript     │
              │ Vite + PWA             │
              │ Responsive Frontend    │
              └───────────┬────────────┘
                          │
                    HTTPS / REST APIs
                          │
                          ▼
              ┌────────────────────────┐
              │ FastAPI Backend        │
              │ Python                 │
              │ Auth / RBAC / Logic    │
              │ AI / Practice / Admin  │
              └───────────┬────────────┘
                          │
                     SQLAlchemy
                          │
                          ▼
              ┌────────────────────────┐
              │ PostgreSQL             │
              │ Production Database    │
              └────────────────────────┘

       Optional / supporting infrastructure
       ├── Redis caching / queue abstraction
       ├── Docker judge sandbox
       ├── AI provider integration
       └── Notification infrastructure

🔄 22. Application Data Flow

User Action
    ↓
React Component
    ↓
API Client
    ↓
FastAPI Endpoint
    ↓
Authentication / Authorization
    ↓
Validation / Business Logic
    ↓
Service / Repository Layer
    ↓
SQLAlchemy
    ↓
PostgreSQL
    ↓
Response
    ↓
React State / UI

For AI workflows:

User
 ↓
React AI Interface
 ↓
FastAPI AI Endpoint
 ↓
Server-side AI Provider
 ↓
AI Response
 ↓
Learning UI

For code execution:

Code Submission
 ↓
Submission API
 ↓
Validation
 ↓
Judge Layer
 ↓
Docker Sandbox
 ↓
Test Cases
 ↓
Verdict
 ↓
Submission History / Progress

🧰 23. Technology Stack

Frontend

React

TypeScript

Vite

HTML5

CSS

REST API integration

PWA technologies

Backend

Python

FastAPI

REST APIs

SQLAlchemy

Alembic

JWT authentication

Argon2id

Database

PostgreSQL

SQLite for local/isolated practice scenarios where applicable

Alembic migrations

Infrastructure

Railway

Docker architecture

Redis abstraction/fallback

Git

GitHub

AI

Server-side AI provider integration

AI Tutor workflows

AI interview workflows

🗄️ 24. Database Architecture

The production PostgreSQL database stores structured data for the platform's major domains.

Core data areas include:

Users
 ├── Authentication / Roles
 ├── Progress
 ├── Submissions
 ├── Mistakes
 ├── Revision
 ├── XP / Levels
 ├── Achievements
 ├── Ratings
 └── Notifications

Learning Content
 ├── Tracks
 ├── Topics
 ├── Subtopics
 ├── Lessons
 ├── Concepts
 ├── Problems
 ├── Examples
 ├── Hints
 ├── Test Cases
 ├── Patterns
 └── Tags

Advanced Systems
 ├── Contests
 ├── Contest Problems
 ├── Interviews
 ├── Competitive Programming
 ├── SQL Practice
 ├── OOP
 ├── Analytics
 └── Audit Logs

Database schema changes are managed through Alembic migrations.

🔐 25. Security Architecture

Security is applied across multiple layers.

Application Security

Authentication

Authorization

RBAC

Input validation

Secure cookies

CORS restrictions

Allowed-host validation

Security headers

Request-size limits

Audit logging

Secret Management

Sensitive values are provided through environment variables and are not intended to be committed to Git.

Examples include:

Database credentials

JWT secret

AI provider keys

Payment credentials

Deployment-specific configuration

Code Execution Security

Untrusted code is isolated from the API process and relies on sandbox infrastructure when execution is enabled.

📁 26. Project Structure

A simplified high-level structure is:

DSAapp/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.*
│
├── alembic/
├── scripts/
├── infra/
├── docs/
├── docker-compose.yml
├── .env.example
└── README.md

The exact repository tree may evolve as modules are added or reorganized. The structure above represents the major architectural separation of the project.

⚙️ 27. Local Development Setup

Prerequisites

Python 3.x

Node.js / npm

PostgreSQL for production-style development where required

Docker Desktop for Docker-based execution features

Git

Environment Configuration

cp .env.example .env

Configure required secrets and service settings in .env.

🐍 28. Backend Setup

Windows PowerShell:

python -m venv backend/.venv
.\backend\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

Run migrations:

python -m alembic -c backend/alembic.ini upgrade head

Start the backend:

uvicorn backend.app.main:app --reload --port 8000

⚛️ 29. Frontend Setup

cd frontend
npm install
npm run dev

Production build:

npm run build

TypeScript validation:

npm run typecheck

🧪 30. Testing & Verification

The project contains backend and frontend testing infrastructure.

Backend

.\backend\.venv\Scripts\pytest backend/tests -v --ignore=backend/tests/test_real_docker_integration.py

Docker integration tests

Requires a running Docker daemon:

.\backend\.venv\Scripts\pytest backend/tests/test_real_docker_integration.py -v

Frontend

cd frontend
npm run test
npm run typecheck
npm run build

Production acceptance

python scripts/verify_production_acceptance.py

🗃️ 31. Database Migrations

Alembic is used to manage production schema changes.

Upgrade:

python -m alembic -c backend/alembic.ini upgrade head

The production deployment does not rely on blindly running SQLAlchemy create_all() against an Alembic-managed PostgreSQL schema.

This prevents PostgreSQL enum/type collisions and keeps schema evolution migration-controlled.

🌐 32. Production Deployment

The current production architecture uses Railway.

Tier

Service

Production URL

Frontend

Railway

https://dsa-applogics.up.railway.app

Backend

Railway

https://dsaapp-production.up.railway.app

Database

Railway PostgreSQL

Private production database

Deployment flow

Local Development
       ↓
Git
       ↓
GitHub
       ↓
Railway
   ┌───┼──────────────┐
   ↓   ↓              ↓
Frontend Backend   PostgreSQL

🔗 33. Live Application

Frontend

https://dsa-applogics.up.railway.app

Backend

https://dsaapp-production.up.railway.app

GitHub

https://github.com/venkatsubbarao123/DSAapp

🛠️ 34. Production Engineering & Debugging

During deployment and production verification, real application issues were identified and resolved, including:

Frontend API routing

The frontend initially attempted to communicate with the wrong API origin. The production API base URL was corrected so frontend requests reach the FastAPI backend.

SPA routing

Routes containing query parameters required handling compatible with the deployed single-page application.

PostgreSQL migrations

Production schema creation was moved through Alembic-managed migrations rather than relying on automatic table creation.

Production content synchronization

The local application content was synchronized into the production PostgreSQL environment, including the 415-problem source library.

CORS

The production frontend origin was explicitly configured in the backend CORS policy.

Health verification

The backend health endpoint was used to verify service availability and database connectivity.

🔒 35. Environment Variables

Important backend configuration categories include:

Variable

Purpose

ENVIRONMENT

Runtime environment

SECRET_KEY

JWT/security signing

DATABASE_URL

PostgreSQL connection

CORS_ORIGINS

Allowed frontend origins

ALLOWED_HOSTS

Trusted backend hosts

GOOGLE_AI_API_KEY

Server-side AI provider credential

AI_PROVIDER

AI provider selection

SECURE_COOKIES

Secure authentication cookies

REDIS_URL

Optional Redis connection

REDIS_REQUIRED

Redis requirement/fallback behavior

PHONEPE_*

Payment configuration when enabled

Frontend:

VITE_API_BASE_URL

The production frontend currently points to:

https://dsaapp-production.up.railway.app

Never commit real secrets, API keys, passwords, database credentials, or private tokens to GitHub.

📖 36. Documentation

Project documentation includes architecture, security, development, testing, administration, analytics, notifications, PWA, and phase completion documentation.

Relevant documentation areas:

Architecture Blueprint
Security Specification
Local Development Guide
Testing & Verification Guide
Administration Manual
Analytics Specification
Notifications Engine
PWA Documentation
Phase Completion Reports

👨‍💻 37. Developer

Choppavarapu Venkata Subba Rao

AI/ML Developer

📧 Email: venkatsubbarao000@gmail.com

📱 Phone: 7093260994

💼 LinkedIn: https://www.linkedin.com/in/venkatasubbarao09

💻 GitHub: https://github.com/venkatsubbarao123

📌 38. Resume-Ready Description

DSAapp — Full-Stack AI-Powered DSA Learning & Coding Platform

Developed and deployed a full-stack AI-powered DSA learning and coding platform using React, TypeScript, Vite, Python, FastAPI, SQLAlchemy, PostgreSQL, Alembic, JWT authentication, Docker-based sandbox architecture, and Railway. Built a structured learning ecosystem with 415 DSA problems, curriculum management, examples, hints, test cases, progress tracking, spaced revision, adaptive practice, AI-assisted tutoring, algorithm visualizers, gamification, contests, AI interview simulation, competitive programming, SQL/OOP learning, analytics, notifications, and PWA support. Implemented secure REST APIs, authentication/RBAC, production database migrations, CORS configuration, content synchronization, health verification, and production deployment.

🎤 39. Interview Explanation

“DSAapp is a full-stack AI-powered DSA learning and coding platform that follows a 20% theory and 80% practice approach. I worked with React and TypeScript for the frontend, FastAPI and Python for the backend, and PostgreSQL with SQLAlchemy and Alembic for the production data layer. The platform contains 415 DSA problems with topics, examples, hints and test cases, along with progress tracking, spaced revision, adaptive practice, AI tutoring, algorithm visualizers, gamification, contests, AI interview simulation, competitive programming, SQL and OOP learning. I also worked on authentication, RBAC, API integration, database migrations, CORS, production debugging, content synchronization, and Railway deployment.”

⭐ Project Highlights

Full-stack React + FastAPI architecture

AI-powered learning workflows

415 structured DSA problems

20% Theory / 80% Practice learning model

Secure authentication and RBAC

PostgreSQL production database

Alembic migration management

Adaptive practice engine

Progress and spaced revision

AI Tutor

Algorithm visualizers

Gamification and leaderboards

Contest system

AI Interview Simulator

Competitive programming

Interactive SQL learning

OOP and Design Patterns

Admin and analytics platform

Notifications

PWA

Railway production deployment

🌐 Project Links

Resource

Link

🌐 Live Application

https://dsa-applogics.up.railway.app

⚙️ Backend API

https://dsaapp-production.up.railway.app

💻 GitHub Repository

https://github.com/venkatsubbarao123/DSAapp

💼 LinkedIn

https://www.linkedin.com/in/venkatasubbarao09

📄 License

This project is maintained as a personal software engineering and portfolio project. Refer to the repository for the applicable licensing terms.

<p align="center">
  <strong>DSAapp — Learn Smarter. Practice Better. Code Confidently.</strong>
</p>
