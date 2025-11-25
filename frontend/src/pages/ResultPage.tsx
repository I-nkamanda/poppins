import { useLocation, useNavigate, Link } from 'react-router-dom';
import type { CourseResponse } from '../types';
import { useEffect } from 'react';

export default function ResultPage() {
    const location = useLocation();
    const navigate = useNavigate();

    const data = location.state?.data as CourseResponse | undefined;
    const requestInfo = location.state?.requestInfo;

    useEffect(() => {
        if (!data) {
            navigate('/');
        }
    }, [data, navigate]);

    if (!data) return null;

    const { course } = data;

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link to="/" className="text-gray-500 hover:text-gray-700">
                            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </Link>
                        <h1 className="text-lg font-bold text-gray-900">
                            학습 커리큘럼
                        </h1>
                    </div>
                </div>
            </header>

            <main className="flex-grow max-w-3xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                    <div className="p-6 border-b border-gray-200 bg-indigo-50">
                        <h2 className="text-2xl font-bold text-gray-900 mb-2">
                            {requestInfo?.topic} 마스터하기
                        </h2>
                        <p className="text-gray-600">
                            총 {course.chapters.length}개의 챕터로 구성된 맞춤형 학습 과정입니다.
                        </p>
                    </div>

                    <ul className="divide-y divide-gray-200">
                        {course.chapters.map((chapter, index) => (
                            <li key={chapter.chapterId} className="hover:bg-gray-50 transition-colors">
                                <Link
                                    to={`/chapter/${chapter.chapterId}`}
                                    state={{ course, requestInfo }} // Pass context for lazy loading
                                    className="block p-6"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <span className="inline-flex items-center justify-center h-6 w-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold">
                                                    {index + 1}
                                                </span>
                                                <h3 className="text-lg font-medium text-gray-900">
                                                    {chapter.chapterTitle}
                                                </h3>
                                            </div>
                                            <p className="text-gray-500 text-sm ml-9">
                                                {chapter.chapterDescription}
                                            </p>
                                        </div>
                                        <div className="ml-4 flex-shrink-0">
                                            <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                                            </svg>
                                        </div>
                                    </div>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>
            </main>
        </div>
    );
}
