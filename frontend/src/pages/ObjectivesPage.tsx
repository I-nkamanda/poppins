import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { generateObjectives, generateCourse } from '../services/api';
import type { ObjectiveItem } from '../types';

export default function ObjectivesPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const { topic, difficulty, maxChapters, language } = location.state || {};

    const [objectives, setObjectives] = useState<ObjectiveItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isGeneratingCourse, setIsGeneratingCourse] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!topic) {
            navigate('/');
            return;
        }

        const fetchObjectives = async () => {
            try {
                const response = await generateObjectives(topic, language);
                setObjectives(response.objectives);
            } catch (err) {
                console.error('Failed to generate objectives:', err);
                setError('학습 목표를 제안하는 중 오류가 발생했습니다.');
            } finally {
                setIsLoading(false);
            }
        };

        fetchObjectives();
    }, [topic, language, navigate]);

    const handleSelectObjective = async (objective: ObjectiveItem) => {
        setIsGeneratingCourse(true);
        try {
            const data = await generateCourse({
                topic,
                difficulty,
                max_chapters: maxChapters,
                selected_objective: `${objective.title}: ${objective.description}`,
                language
            });
            navigate('/result', { state: { data, requestInfo: { topic, difficulty, maxChapters, language } } });
        } catch (err) {
            console.error('Failed to generate course:', err);
            alert('커리큘럼 생성 중 오류가 발생했습니다.');
        } finally {
            setIsGeneratingCourse(false);
        }
    };

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
                <div className="text-center">
                    <svg className="animate-spin h-10 w-10 text-indigo-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <h2 className="text-xl font-semibold text-gray-900">학습 목표를 분석하고 있습니다...</h2>
                    <p className="text-gray-500 mt-2">잠시만 기다려주세요.</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
                <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full text-center">
                    <div className="text-red-500 text-5xl mb-4">⚠️</div>
                    <h2 className="text-xl font-bold text-gray-900 mb-2">오류 발생</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button
                        onClick={() => navigate('/')}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors"
                    >
                        홈으로 돌아가기
                    </button>
                </div>
            </div>
        );
    }

    if (isGeneratingCourse) {
        return (
            <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
                <div className="text-center">
                    <svg className="animate-spin h-10 w-10 text-indigo-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <h2 className="text-xl font-semibold text-gray-900">맞춤형 커리큘럼을 생성하고 있습니다...</h2>
                    <p className="text-gray-500 mt-2">선택하신 목표에 맞춰 최적의 경로를 설계 중입니다.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-5xl mx-auto">
                <div className="text-center mb-12">
                    <h1 className="text-3xl font-extrabold text-gray-900 sm:text-4xl">
                        어떤 방향으로 학습하시겠습니까?
                    </h1>
                    <p className="mt-4 text-lg text-gray-600">
                        주제 <span className="font-bold text-indigo-600">'{topic}'</span>에 대해 3가지 학습 경로를 제안해 드립니다.
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
                    {objectives.map((obj) => (
                        <div key={obj.id} className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition-shadow duration-300 flex flex-col border border-gray-100">
                            <div className="p-6 flex-grow">
                                <div className="text-xs font-semibold tracking-wide uppercase text-indigo-500 mb-2">
                                    Option {obj.id}
                                </div>
                                <h3 className="text-xl font-bold text-gray-900 mb-3">{obj.title}</h3>
                                <p className="text-gray-600 mb-4">{obj.description}</p>
                                <div className="bg-gray-50 p-3 rounded-lg">
                                    <span className="text-sm font-medium text-gray-500">추천 대상:</span>
                                    <p className="text-sm text-gray-700 mt-1">{obj.target_audience}</p>
                                </div>
                            </div>
                            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
                                <button
                                    onClick={() => handleSelectObjective(obj)}
                                    className="w-full flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
                                >
                                    이 경로 선택하기
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-12 text-center">
                    <button
                        onClick={() => navigate('/')}
                        className="text-indigo-600 hover:text-indigo-800 font-medium"
                    >
                        &larr; 주제 다시 입력하기
                    </button>
                </div>
            </div>
        </div>
    );
}
