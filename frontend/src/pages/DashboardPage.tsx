import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getCourses, deleteCourse } from '../services/api';
import type { CourseListItem } from '../types';

export default function DashboardPage() {
    const [courses, setCourses] = useState<CourseListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [filter, setFilter] = useState<'all' | 'completed'>('all');
    const navigate = useNavigate();

    useEffect(() => {
        const loadCourses = async () => {
            try {
                const data = await getCourses();
                setCourses(data);
            } catch (err) {
                console.error('Failed to load courses:', err);
                setError('코스 목록을 불러오는 데 실패했습니다.');
            } finally {
                setIsLoading(false);
            }
        };

        loadCourses();
    }, []);

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.preventDefault(); // Prevent navigation
        e.stopPropagation(); // Stop event bubbling to Link
        if (!window.confirm('정말 이 코스를 삭제하시겠습니까? 복구할 수 없습니다.')) return;

        try {
            await deleteCourse(id);
            setCourses(courses.filter(c => c.id !== id));
        } catch (err) {
            console.error('Failed to delete course:', err);
            alert('코스 삭제에 실패했습니다.');
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    const filteredCourses = courses.filter(c => {
        if (filter === 'completed') return c.progress === 100;
        return true;
    });

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-2xl">🎓</span>
                        <h1 className="text-xl font-bold text-gray-900">PopPins II</h1>
                    </div>
                    <Link
                        to="/courses/new"
                        className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors shadow-sm"
                    >
                        + 새로운 교육과정 생성
                    </Link>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Welcome Section */}
                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-gray-900">내 학습 대시보드</h2>
                    <p className="text-gray-600 mt-1">진행 중인 모든 학습을 한눈에 관리하세요.</p>
                </div>

                {/* KPI Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div className="text-sm font-medium text-gray-500">진행 중인 과정</div>
                        <div className="mt-2 text-3xl font-bold text-gray-900">{courses.length}</div>
                    </div>
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
                        <div className="text-sm font-medium text-gray-500">완료한 과정</div>
                        <div className="mt-2 text-3xl font-bold text-green-600">
                            {courses.filter(c => c.progress === 100).length}
                        </div>
                    </div>
                </div>

                {/* Recent Learning Section */}
                <div className="mb-6">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold text-gray-900">최근 학습</h3>

                        {/* Filter Tabs */}
                        <div className="flex bg-gray-100 p-1 rounded-lg">
                            <button
                                onClick={() => setFilter('all')}
                                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${filter === 'all'
                                    ? 'bg-white text-gray-900 shadow-sm'
                                    : 'text-gray-500 hover:text-gray-900'
                                    }`}
                            >
                                전체
                            </button>
                            <button
                                onClick={() => setFilter('completed')}
                                className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${filter === 'completed'
                                    ? 'bg-white text-gray-900 shadow-sm'
                                    : 'text-gray-500 hover:text-gray-900'
                                    }`}
                            >
                                완료됨
                            </button>
                        </div>
                    </div>

                    {isLoading ? (
                        <div className="flex justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                        </div>
                    ) : error ? (
                        <div className="text-center py-12 text-red-600 bg-white rounded-xl border border-red-100">
                            <p>{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="mt-4 text-indigo-600 hover:text-indigo-800 underline"
                            >
                                다시 시도
                            </button>
                        </div>
                    ) : filteredCourses.length === 0 ? (
                        <div className="text-center py-20 bg-white rounded-xl border border-gray-200 border-dashed">
                            <div className="text-4xl mb-4">📝</div>
                            <h3 className="text-lg font-medium text-gray-900">
                                {filter === 'completed' ? '완료된 과정이 없습니다.' : '아직 생성된 교육과정이 없습니다.'}
                            </h3>
                            {filter === 'all' && (
                                <>
                                    <p className="text-gray-500 mt-2 mb-6">첫 번째 학습 여정을 시작해보세요!</p>
                                    <Link
                                        to="/courses/new"
                                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
                                    >
                                        교육과정 생성하기
                                    </Link>
                                </>
                            )}
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {filteredCourses.map((course) => (
                                <div
                                    key={course.id}
                                    className="block group bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden relative"
                                >
                                    <div className="p-6 relative">
                                        <div className="flex items-start justify-between mb-4">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${course.level === '초급' ? 'bg-green-100 text-green-800' :
                                                course.level === '중급' ? 'bg-blue-100 text-blue-800' :
                                                    'bg-purple-100 text-purple-800'
                                                }`}>
                                                {course.level || 'Unknown'}
                                            </span>
                                            {/* Controls - Higher Z-Index to be clickable above the link overlay */}
                                            <div className="flex items-center gap-2 relative z-10">
                                                <span className="text-xs text-gray-500">
                                                    {formatDate(course.created_at)}
                                                </span>
                                                <button
                                                    type="button"
                                                    onClick={(e) => handleDelete(e, course.id)}
                                                    className="p-1 text-gray-400 hover:text-red-500 transition-colors rounded-full hover:bg-gray-100 cursor-pointer"
                                                    title="코스 삭제"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                                    </svg>
                                                </button>
                                            </div>
                                        </div>
                                        <h4 className="text-lg font-bold text-gray-900 mb-2 group-hover:text-indigo-600 transition-colors line-clamp-1">
                                            {/* Main Link via Pseudo-element */}
                                            <Link
                                                to={`/courses/${course.id}`}
                                                className="before:absolute before:inset-0 focus:outline-none"
                                            >
                                                {course.topic}
                                            </Link>
                                        </h4>
                                        <p className="text-sm text-gray-600 mb-4 line-clamp-2 h-10">
                                            {course.description}
                                        </p>

                                        {/* Progress Bar */}
                                        <div className="mb-4">
                                            <div className="flex justify-between text-xs text-gray-500 mb-1">
                                                <span>진행률</span>
                                                <span>{course.progress}%</span>
                                            </div>
                                            <div className="w-full bg-gray-100 rounded-full h-2">
                                                <div
                                                    className={`h-2 rounded-full transition-all duration-500 ${course.progress === 100 ? 'bg-green-500' : 'bg-indigo-600'
                                                        }`}
                                                    style={{ width: `${course.progress}%` }}
                                                ></div>
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t border-gray-100">
                                            <div className="flex items-center gap-1">
                                                <span>📚</span>
                                                <span>{course.completed_chapters}/{course.chapter_count} 챕터 완료</span>
                                            </div>
                                            <span className="text-indigo-600 font-medium group-hover:translate-x-1 transition-transform">
                                                {course.progress === 100 ? '복습하기 →' : '이어서 학습 →'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
}
