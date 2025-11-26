import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ResultPage from './pages/ResultPage';
import ChapterPage from './pages/ChapterPage';
import ObjectivesPage from './pages/ObjectivesPage';
import DashboardPage from './pages/DashboardPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen w-full">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<DashboardPage />} /> {/* Explicit route */}
          <Route path="/courses/new" element={<HomePage />} />
          <Route path="/objectives" element={<ObjectivesPage />} />
          <Route path="/result" element={<ResultPage />} /> {/* Legacy support */}
          <Route path="/courses/:courseId" element={<ResultPage />} />
          <Route path="/chapter/:chapterId" element={<ChapterPage />} /> {/* Legacy support */}
          <Route path="/courses/:courseId/chapters/:chapterId" element={<ChapterPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
