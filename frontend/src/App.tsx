import { BrowserRouter, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import ResultPage from './pages/ResultPage';
import ChapterPage from './pages/ChapterPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen w-full">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/result" element={<ResultPage />} />
          <Route path="/chapter/:chapterId" element={<ChapterPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
