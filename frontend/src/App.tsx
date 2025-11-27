/**
 * PopPins II - 메인 애플리케이션 컴포넌트
 * 
 * React Router를 사용하여 전체 애플리케이션의 라우팅을 관리합니다.
 * 
 * 라우트 구조:
 * - /: 대시보드 (최근 학습 목록)
 * - /dashboard: 대시보드 (명시적 라우트)
 * - /courses/new: 새 코스 생성 (주제 입력)
 * - /objectives: 학습 목표 선택
 * - /courses/:courseId: 커리큘럼 화면
 * - /courses/:courseId/chapters/:chapterId: 챕터 상세 화면
 * 
 * @component
 * @returns {JSX.Element} 라우팅이 설정된 애플리케이션
 * 
 * @example
 * ```tsx
 * // App.tsx는 일반적으로 index.tsx에서 렌더링됩니다
 * ReactDOM.createRoot(document.getElementById('root')!).render(
 *   <React.StrictMode>
 *     <App />
 *   </React.StrictMode>
 * );
 * ```
 */
import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ResultPage from './pages/ResultPage';
import ChapterPage from './pages/ChapterPage';
import ObjectivesPage from './pages/ObjectivesPage';
import DashboardPage from './pages/DashboardPage';
import { QuizResultsPage } from './pages/QuizResultsPage';
import { ApiKeyModal } from './components/ApiKeyModal';
import { checkConfig } from './services/api';

function App() {
  const [needsConfig, setNeedsConfig] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const check = async () => {
      try {
        const status = await checkConfig();
        if (!status.configured) {
          setNeedsConfig(true);
        }
      } catch (e) {
        console.error("Failed to check config:", e);
      } finally {
        setChecking(false);
      }
    };

    // 1초 후 체크 (백엔드 부팅 대기)
    const timer = setTimeout(check, 1000);
    return () => clearTimeout(timer);
  }, []);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      {needsConfig && <ApiKeyModal onConfigured={() => setNeedsConfig(false)} />}
      <div className="min-h-screen w-full">
        <Routes>
          {/* 대시보드 - 최근 학습 목록 */}
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} /> {/* 명시적 라우트 */}

          {/* 새 코스 생성 - 주제 입력 화면 */}
          <Route path="/courses/new" element={<HomePage />} />

          {/* 학습 목표 선택 화면 */}
          <Route path="/objectives" element={<ObjectivesPage />} />

          {/* 커리큘럼 화면 - 챕터 목록 표시 */}
          <Route path="/result" element={<ResultPage />} /> {/* 레거시 지원 */}
          <Route path="/courses/:courseId" element={<ResultPage />} />

          {/* 챕터 상세 화면 - 개념/실습/퀴즈 표시 */}
          <Route path="/chapter/:chapterId" element={<ChapterPage />} /> {/* 레거시 지원 */}
          <Route path="/courses/:courseId/chapters/:chapterId" element={<ChapterPage />} />

          {/* 퀴즈 결과 목록 화면 */}
          <Route path="/quiz-results" element={<QuizResultsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
