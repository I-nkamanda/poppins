/**
 * 새 코스 생성 페이지 (HomePage)
 * 
 * 사용자가 학습하고 싶은 주제를 입력하는 첫 화면입니다.
 * 주제, 난이도, 챕터 수, 언어를 선택할 수 있습니다.
 * 
 * 사용자 플로우:
 * 1. 주제 입력 및 설정 선택
 * 2. "학습 자료 생성하기" 버튼 클릭
 * 3. ObjectivesPage로 이동하여 학습 목표 선택
 * 
 * @component
 * @returns {JSX.Element} 새 코스 생성 폼
 * 
 * @example
 * ```tsx
 * // 라우팅에 의해 자동으로 렌더링됩니다
 * <Route path="/courses/new" element={<HomePage />} />
 * ```
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function HomePage() {
    const navigate = useNavigate();
    const [topic, setTopic] = useState('');
    const [difficulty, setDifficulty] = useState('중급');
    const [maxChapters, setMaxChapters] = useState(3);
    const [language, setLanguage] = useState('ko');

    /**
     * 폼 제출 핸들러
     * 
     * 사용자가 입력한 정보를 ObjectivesPage로 전달하여 학습 목표 선택 화면으로 이동합니다.
     * 
     * @param e - 폼 제출 이벤트
     * 
     * @example
     * 사용자가 "파이썬 리스트"를 입력하고 제출하면:
     * - topic: "파이썬 리스트"
     * - difficulty: "중급"
     * - maxChapters: 3
     * - language: "ko"
     * 이 정보가 ObjectivesPage로 전달됩니다.
     */
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault(); // 기본 폼 제출 동작 방지
        if (!topic.trim()) return; // 주제가 비어있으면 제출하지 않음

        // 학습 목표 선택 페이지로 이동 (상태 전달)
        navigate('/objectives', { state: { topic, difficulty, maxChapters, language } });
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 py-4">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
                    <h1 className="text-2xl font-bold text-indigo-600">PopPins II</h1>
                </div>
            </header>

            <main className="flex-grow flex flex-col items-center justify-center p-4 sm:px-6 lg:px-8">
                <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-xl shadow-lg border border-gray-100">
                    <div className="text-center">
                        <h2 className="mt-2 text-3xl font-extrabold text-gray-900">
                            나만의 배움 여정 시작하기
                        </h2>
                        <p className="mt-2 text-sm text-gray-600">
                            배우고 싶은 주제를 입력하면 AI가 맞춤형 PBL 학습 자료를 만들어드립니다.
                        </p>
                    </div>

                    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                        <div className="rounded-md shadow-sm space-y-4">
                            <div>
                                <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-1">
                                    학습 주제
                                </label>
                                <input
                                    id="topic"
                                    name="topic"
                                    type="text"
                                    required
                                    className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                    placeholder="예: 파이썬 리스트, 리액트 기초"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-1">
                                        난이도
                                    </label>
                                    <select
                                        id="difficulty"
                                        name="difficulty"
                                        className="appearance-none block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm bg-white"
                                        value={difficulty}
                                        onChange={(e) => setDifficulty(e.target.value)}
                                    >
                                        <option value="초급">초급</option>
                                        <option value="중급">중급</option>
                                        <option value="고급">고급</option>
                                    </select>
                                </div>

                                <div>
                                    <label htmlFor="chapters" className="block text-sm font-medium text-gray-700 mb-1">
                                        챕터 수 (1-10)
                                    </label>
                                    <input
                                        id="chapters"
                                        name="chapters"
                                        type="number"
                                        min="1"
                                        max="10"
                                        required
                                        className="appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                        value={maxChapters}
                                        onChange={(e) => setMaxChapters(parseInt(e.target.value))}
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    언어 / Language
                                </label>
                                <div className="flex space-x-4">
                                    <button
                                        type="button"
                                        onClick={() => setLanguage('ko')}
                                        className={`flex-1 py-2 px-4 rounded-md border ${language === 'ko'
                                            ? 'bg-indigo-50 border-indigo-500 text-indigo-700 ring-1 ring-indigo-500'
                                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                                            } text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                                    >
                                        한국어
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => setLanguage('en')}
                                        className={`flex-1 py-2 px-4 rounded-md border ${language === 'en'
                                            ? 'bg-indigo-50 border-indigo-500 text-indigo-700 ring-1 ring-indigo-500'
                                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                                            } text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                                    >
                                        English
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors duration-200"
                            >
                                학습 자료 생성하기
                            </button>
                        </div>
                    </form>
                </div>
            </main>
        </div>
    );
}
