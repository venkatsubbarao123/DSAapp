import React, { useEffect, useState } from "react";
import "./theme/tokens.css";
import { ErrorBoundary } from "./components/common/ErrorBoundary.tsx";
import { Header } from "./components/common/Header.tsx";
import { Footer } from "./components/common/Footer.tsx";
import { HomePage } from "./pages/HomePage.tsx";
import { SystemStatusPage } from "./pages/SystemStatusPage.tsx";
import { PremiumPage } from "./pages/PremiumPage.tsx";
import { CurriculumPage } from "./pages/CurriculumPage.tsx";
import { TopicsPage } from "./pages/TopicsPage.tsx";
import { LessonPage } from "./pages/LessonPage.tsx";
import { ProblemsPage } from "./pages/ProblemsPage.tsx";
import { ProblemDetailPage } from "./pages/ProblemDetailPage.tsx";
import { ProgressPage } from "./pages/ProgressPage.tsx";
import { SubmissionsPage } from "./pages/SubmissionsPage.tsx";
import { SubmissionDetailPage } from "./pages/SubmissionDetailPage.tsx";
import { MistakesPage } from "./pages/MistakesPage.tsx";
import { RevisionPage } from "./pages/RevisionPage.tsx";
import { AiLearningPage } from "./pages/AiLearningPage.tsx";
import { VisualizersPage } from "./pages/VisualizersPage.tsx";
import { PracticePage } from "./pages/PracticePage.tsx";
import { DailyChallengePage } from "./pages/DailyChallengePage.tsx";
import { AchievementsPage } from "./pages/AchievementsPage.tsx";
import { LeaderboardPage } from "./pages/LeaderboardPage.tsx";
import { NotFoundPage } from "./pages/NotFoundPage.tsx";

import { AuthProvider } from "./context/AuthContext.tsx";
import { AuthModal } from "./components/auth/AuthModal.tsx";
import { fetchApi } from "./services/apiClient.ts";
import { HealthData } from "./types/api.ts";

export const AppContent: React.FC = () => {
  const [currentPath, setCurrentPath] = useState<string>(
    window.location.pathname || "/"
  );
  const [serviceHealthy, setServiceHealthy] = useState<boolean | undefined>(
    undefined
  );

  const navigate = (path: string) => {
    window.history.pushState({}, "", path);
    setCurrentPath(path);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || "/");
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Background passive check for header status pill
  useEffect(() => {
    let isMounted = true;
    fetchApi<HealthData>("/health", {}, 4000)
      .then((res) => {
        if (isMounted) {
          setServiceHealthy(res.data?.status === "healthy");
        }
      })
      .catch(() => {
        if (isMounted) {
          setServiceHealthy(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, [currentPath]);

  const renderCurrentView = () => {
    if (currentPath === "/") {
      return <HomePage onNavigate={navigate} />;
    }
    if (currentPath === "/status") {
      return <SystemStatusPage />;
    }
    if (currentPath === "/premium") {
      return <PremiumPage />;
    }
    if (currentPath === "/curriculum") {
      return <CurriculumPage onNavigate={navigate} />;
    }
    if (currentPath === "/topics") {
      return <TopicsPage onNavigate={navigate} />;
    }
    if (currentPath.startsWith("/topics/")) {
      const topicId = currentPath.replace("/topics/", "");
      return <TopicsPage topicId={topicId} onNavigate={navigate} />;
    }
    if (currentPath.startsWith("/lessons/")) {
      const lessonId = currentPath.replace("/lessons/", "");
      return <LessonPage lessonId={lessonId} onNavigate={navigate} />;
    }
    if (currentPath === "/problems" || currentPath.startsWith("/problems?")) {
      return <ProblemsPage onNavigate={navigate} />;
    }
    if (currentPath.startsWith("/problems/")) {
      const problemId = currentPath.replace("/problems/", "");
      return <ProblemDetailPage problemId={problemId} onNavigate={navigate} />;
    }
    if (currentPath === "/progress") {
      return <ProgressPage onNavigate={navigate} />;
    }
    if (currentPath === "/submissions") {
      return <SubmissionsPage onNavigate={navigate} />;
    }
    if (currentPath.startsWith("/submissions/")) {
      const submissionId = currentPath.replace("/submissions/", "");
      return <SubmissionDetailPage submissionId={submissionId} onNavigate={navigate} />;
    }
    if (currentPath === "/mistakes") {
      return <MistakesPage onNavigate={navigate} />;
    }
    if (currentPath === "/revision") {
      return <RevisionPage onNavigate={navigate} />;
    }
    if (currentPath === "/ai" || currentPath.startsWith("/ai?")) {
      return <AiLearningPage onNavigate={navigate} />;
    }
    if (currentPath === "/visualizers" || currentPath.startsWith("/visualizers?") || currentPath.startsWith("/visualize/")) {
      return <VisualizersPage onNavigate={navigate} />;
    }
    if (currentPath === "/practice" || currentPath.startsWith("/practice?")) {
      return <PracticePage onNavigate={navigate} />;
    }
    if (currentPath === "/daily" || currentPath.startsWith("/daily?")) {
      return <DailyChallengePage onNavigate={navigate} />;
    }
    if (currentPath === "/achievements" || currentPath.startsWith("/achievements?")) {
      return <AchievementsPage onNavigate={navigate} />;
    }
    if (currentPath === "/leaderboard" || currentPath === "/leaderboards" || currentPath.startsWith("/leaderboard")) {
      return <LeaderboardPage onNavigate={navigate} />;
    }
    return <NotFoundPage onNavigate={navigate} />;

  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100vh",
        backgroundColor: "var(--bg-primary)",
        color: "var(--text-primary)",
      }}
    >
      {/* Accessible skip link */}
      <a
        href="#main-content"
        style={{
          position: "absolute",
          top: "-9999px",
          left: "var(--space-4)",
          backgroundColor: "var(--brand-primary)",
          color: "#ffffff",
          padding: "var(--space-2) var(--space-4)",
          borderRadius: "var(--radius-sm)",
          zIndex: 100,
          textDecoration: "none",
          fontWeight: 600,
        }}
        onFocus={(e) => {
          e.currentTarget.style.top = "var(--space-4)";
        }}
        onBlur={(e) => {
          e.currentTarget.style.top = "-9999px";
        }}
      >
        Skip to main content
      </a>

      <Header
        currentPath={currentPath}
        onNavigate={navigate}
        serviceHealthy={serviceHealthy}
      />

      <div id="main-content" style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {renderCurrentView()}
      </div>

      <Footer />
      <AuthModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
