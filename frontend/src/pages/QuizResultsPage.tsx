import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizResults } from '../services/api';
import type { QuizResultItem } from '../types';

export const QuizResultsPage: React.FC = () => {
    const navigate = useNavigate();
    const [results, setResults] = useState<QuizResultItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const response = await getQuizResults();
                setResults(response.results);
            } catch (err) {
                setError('퀴즈 결과를 불러오는데 실패했습니다.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchResults();
    }, []);

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-900">나의 퀴즈 답변</h1>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                    >
                        대시보드로 돌아가기
                    </button>
                </div>

                {loading ? (
                    <div className="flex justify-center items-center h-64">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                    </div>
                ) : error ? (
                    <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative" role="alert">
                        <strong className="font-bold">오류!</strong>
                        <span className="block sm:inline"> {error}</span>
                    </div>
                ) : results.length === 0 ? (
                    <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
                        아직 제출한 퀴즈 답변이 없습니다.
                    </div>
                ) : (
                    <div className="space-y-6">
                        {results.map((result) => (
                            <div key={result.id} className="bg-white shadow overflow-hidden sm:rounded-lg border border-gray-200">
                                <div className="px-4 py-5 sm:px-6 bg-gray-50 flex justify-between items-center">
                                    <div>
                                        <h3 className="text-lg leading-6 font-medium text-gray-900">
                                            {result.chapter_title}
                                        </h3>
                                        <p className="mt-1 max-w-2xl text-sm text-gray-500">
                                            제출일: {formatDate(result.timestamp)}
                                        </p>
                                    </div>
                                    <div className={`px-3 py-1 rounded-full text-sm font-bold ${result.score >= 80 ? 'bg-green-100 text-green-800' :
                                        result.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                                            'bg-red-100 text-red-800'
                                        }`}>
                                        {result.score}점
                                    </div>
                                </div>
                                <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
                                    <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-1">
                                        <div className="sm:col-span-1">
                                            <dt className="text-sm font-medium text-gray-500">나의 답변</dt>
                                            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-3 rounded-md whitespace-pre-wrap">
                                                {result.user_answer || '(답변 내용 없음)'}
                                            </dd>
                                        </div>

                                        {result.feedback && (
                                            <div className="sm:col-span-1">
                                                <dt className="text-sm font-medium text-gray-500">AI 피드백</dt>
                                                <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                                                    {result.feedback}
                                                </dd>
                                            </div>
                                        )}

                                        {result.correct_points && (
                                            <div className="sm:col-span-1">
                                                <dt className="text-sm font-medium text-green-600">✓ 잘한 점</dt>
                                                <dd className="mt-1 text-sm text-gray-900">
                                                    <ul className="list-disc list-inside">
                                                        {JSON.parse(result.correct_points).map((point: string, idx: number) => (
                                                            <li key={idx}>{point}</li>
                                                        ))}
                                                    </ul>
                                                </dd>
                                            </div>
                                        )}

                                        <div className="sm:col-span-1">
                                            <dt className="text-sm font-medium text-orange-600">📝 개선할 점</dt>
                                            <dd className="mt-1 text-sm text-gray-900">
                                                <ul className="list-disc list-inside">
                                                    {JSON.parse(result.weak_points).map((point: string, idx: number) => (
                                                        <li key={idx}>{point}</li>
                                                    ))}
                                                </ul>
                                            </dd>
                                        </div>
                                    </dl>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
