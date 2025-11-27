import { useLocation, useNavigate, useParams, Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import type { Course, ChapterContent, QuizGradingResponse } from '../types';
import { generateChapterContent, downloadChapter, gradeQuiz, submitFeedback } from '../services/api';
import MarkdownViewer from '../components/MarkdownViewer';
import SurveyModal from '../components/SurveyModal';

type TabType = 'concept' | 'exercise' | 'quiz' | 'advanced';

export default function ChapterPage() {
    const { chapterId } = useParams();
    const location = useLocation();
    const navigate = useNavigate();

    const [activeTab, setActiveTab] = useState<TabType>('concept');
    const [content, setContent] = useState<ChapterContent | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [quizAnswers, setQuizAnswers] = useState<{ [key: number]: string }>({});
    const [mcqAnswers, setMcqAnswers] = useState<{ [key: number]: string }>({}); // For MCQs
    const [mcqResults, setMcqResults] = useState<{ [key: number]: boolean | null }>({}); // null: not checked, true: correct, false: incorrect
    const [quizGradings, setQuizGradings] = useState<{ [key: number]: QuizGradingResponse | null }>({});
    const [gradingLoading, setGradingLoading] = useState<{ [key: number]: boolean }>({});

    // Feedback State
    const [rating, setRating] = useState<number>(0);
    const [comment, setComment] = useState('');

    // Survey State
    const [showSurvey, setShowSurvey] = useState(false);
    const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
    const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

    const course = location.state?.course as Course | undefined;
    const requestInfo = location.state?.requestInfo;

    useEffect(() => {
        if (!course || !requestInfo || !chapterId) {
            navigate('/');
            return;
        }

        const chapter = course.chapters.find(c => c.chapterId === parseInt(chapterId));
        if (!chapter) return;

        // 이미 같은 챕터의 콘텐츠가 로드되어 있으면 다시 요청하지 않음
        if (content && content.chapter.chapterId === parseInt(chapterId)) {
            return;
        }

        const loadContent = async () => {
            setIsLoading(true);
            setError(null);
            setContent(null); // Reset content while loading

            // Show survey only if not completed yet in this session
            const hasCompletedSurvey = sessionStorage.getItem('survey_completed');
            if (!hasCompletedSurvey) {
                setShowSurvey(true);
            }

            try {
                const data = await generateChapterContent({
                    course_title: requestInfo.topic,
                    course_description: requestInfo.topic, // Simple fallback
                    chapter_title: chapter.chapterTitle,
                    chapter_description: chapter.chapterDescription,
                });
                setContent(data);
            } catch (err: any) {
                console.error('챕터 콘텐츠 생성 실패:', err);
                const errorMessage = err?.response?.data?.detail || err?.message || '챕터 내용을 불러오는 데 실패했습니다.';
                setError(`오류: ${errorMessage}`);
            } finally {
                setIsLoading(false);
            }
        };

        loadContent();
    }, [chapterId]); // chapterId만 dependency로 변경

    if (!course || !chapterId) return null;

    const chapterIndex = course.chapters.findIndex(
        c => c.chapterId === parseInt(chapterId)
    );

    if (chapterIndex === -1) return <div>Chapter not found</div>;

    const currentChapter = course.chapters[chapterIndex];

    const handleNext = () => {
        if (chapterIndex < course.chapters.length - 1) {
            const nextChapterId = course.chapters[chapterIndex + 1].chapterId;
            navigate(`/chapter/${nextChapterId}`, { state: { course, requestInfo } });
            setActiveTab('concept');
            // Reset feedback state for new chapter
            setRating(0);
            setComment('');
            setFeedbackSubmitted(false);
        }
    };

    const handlePrev = () => {
        if (chapterIndex > 0) {
            const prevChapterId = course.chapters[chapterIndex - 1].chapterId;
            navigate(`/chapter/${prevChapterId}`, { state: { course, requestInfo } });
            setActiveTab('concept');
            // Reset feedback state for new chapter
            setRating(0);
            setComment('');
            setFeedbackSubmitted(false);
        }
    };

    const handleDownload = async () => {
        if (!content || !requestInfo) return;

        try {
            const chapter = course.chapters.find(c => c.chapterId === parseInt(chapterId || '0'));
            if (!chapter) return;

            const data = await downloadChapter({
                course_title: requestInfo.topic,
                course_description: requestInfo.topic,
                chapter_title: chapter.chapterTitle,
                chapter_description: chapter.chapterDescription,
            });

            // Chrome 호환성을 위해 data URL 사용
            const dataUrl = 'data:text/markdown;charset=utf-8,' + encodeURIComponent(data.content);
            const a = document.createElement('a');
            a.href = dataUrl;
            a.download = data.filename;
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();

            // cleanup
            setTimeout(() => {
                document.body.removeChild(a);
            }, 100);
        } catch (err) {
            console.error('다운로드 실패:', err);
            alert('다운로드 중 오류가 발생했습니다.');
        }
    };

    const handleGradeQuiz = async (quizIndex: number, question: string) => {
        const answer = quizAnswers[quizIndex];
        if (!answer || !answer.trim()) {
            alert('답변을 입력해주세요.');
            return;
        }

        if (!content || !requestInfo) return;
        const chapter = course.chapters.find(c => c.chapterId === parseInt(chapterId || '0'));
        if (!chapter) return;

        setGradingLoading({ ...gradingLoading, [quizIndex]: true });

        try {
            const result = await gradeQuiz({
                question,
                answer,
                chapter_title: chapter.chapterTitle,
                chapter_description: chapter.chapterDescription,
            });
            setQuizGradings({ ...quizGradings, [quizIndex]: result });
        } catch (err) {
            console.error('채점 실패:', err);
            alert('채점 중 오류가 발생했습니다.');
        } finally {
            setGradingLoading({ ...gradingLoading, [quizIndex]: false });
        }
    };

    const handleFeedbackSubmit = async () => {
        if (rating === 0) {
            alert('별점을 선택해주세요.');
            return;
        }
        if (!content) return;

        setIsSubmittingFeedback(true);
        try {
            await submitFeedback({
                chapter_title: content.chapter.chapterTitle,
                rating,
                comment
            });
            setFeedbackSubmitted(true);
            alert('피드백이 제출되었습니다. 감사합니다!');
        } catch (err) {
            console.error('피드백 제출 실패:', err);
            alert('피드백 제출 중 오류가 발생했습니다.');
        } finally {
            setIsSubmittingFeedback(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex flex-col">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Link to="/result" state={{ data: { course }, requestInfo }} className="text-gray-500 hover:text-gray-700">
                            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                            </svg>
                        </Link>
                        <h1 className="text-lg font-bold text-gray-900 truncate max-w-md">
                            {currentChapter.chapterTitle}
                        </h1>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="text-sm text-gray-500">
                            Chapter {chapterIndex + 1} / {course.chapters.length}
                        </div>
                        {content && (
                            <button
                                onClick={handleDownload}
                                className="px-3 py-1.5 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100 transition-colors"
                            >
                                📥 다운로드
                            </button>
                        )}
                    </div>
                </div>
            </header>

            <main className="flex-grow max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {/* Tabs */}
                <div className="border-b border-gray-200 mb-8">
                    <nav className="-mb-px flex space-x-8" aria-label="Tabs">
                        {[
                            { id: 'concept', name: '개념 학습' },
                            { id: 'exercise', name: '실습 과제' },
                            { id: 'quiz', name: '퀴즈 (객관식)' },
                            { id: 'advanced', name: '심화 학습 (주관식)' },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as TabType)}
                                disabled={isLoading}
                                className={`
                  whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                  ${activeTab === tab.id
                                        ? 'border-indigo-500 text-indigo-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
                `}
                            >
                                {tab.name}
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Content Area */}
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 min-h-[500px]">
                    {isLoading ? (
                        <div className="flex flex-col items-center justify-center h-full py-20">
                            <svg className="animate-spin h-10 w-10 text-indigo-600 mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <p className="text-gray-600">AI가 학습 자료를 생성하고 있습니다... (약 15초 소요)</p>
                        </div>
                    ) : error ? (
                        <div className="text-center py-20 text-red-600">
                            <p>{error}</p>
                            <button
                                onClick={() => window.location.reload()}
                                className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
                            >
                                다시 시도
                            </button>
                        </div>
                    ) : content ? (
                        <>
                            {activeTab === 'concept' && (
                                <div className="animate-fadeIn">
                                    <h2 className="text-2xl font-bold text-gray-900 mb-4">{content.concept.title}</h2>
                                    <p className="text-gray-600 mb-8 italic">{content.concept.description}</p>
                                    <MarkdownViewer content={content.concept.contents} />
                                </div>
                            )}

                            {activeTab === 'exercise' && (
                                <div className="animate-fadeIn">
                                    <h2 className="text-2xl font-bold text-gray-900 mb-4">{content.exercise.title}</h2>
                                    <p className="text-gray-600 mb-8 italic">{content.exercise.description}</p>
                                    <MarkdownViewer content={content.exercise.contents} />
                                </div>
                            )}

                            {activeTab === 'quiz' && (
                                <div className="animate-fadeIn">
                                    <h2 className="text-2xl font-bold text-gray-900 mb-6">학습 점검 퀴즈 (객관식)</h2>
                                    <div className="space-y-8">
                                        {content.quiz.quizes.map((q, idx) => {
                                            const isCorrect = mcqResults[idx];
                                            const selectedAnswer = mcqAnswers[idx];

                                            return (
                                                <div key={idx} className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                                                    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800 mb-3">
                                                        문제 {idx + 1}
                                                    </span>
                                                    <h3 className="text-lg font-medium text-gray-900 mb-4">{q.question}</h3>

                                                    <div className="space-y-3">
                                                        {q.options.map((option, optIdx) => (
                                                            <label
                                                                key={optIdx}
                                                                className={`flex items-center p-3 rounded-md border cursor-pointer transition-colors ${selectedAnswer === option
                                                                    ? 'border-indigo-500 bg-indigo-50 ring-1 ring-indigo-500'
                                                                    : 'border-gray-300 bg-white hover:bg-gray-50'
                                                                    } ${isCorrect !== undefined && isCorrect !== null && option === q.answer ? 'bg-green-50 border-green-500 ring-1 ring-green-500' : ''}`}
                                                            >
                                                                <input
                                                                    type="radio"
                                                                    name={`quiz-${idx}`}
                                                                    value={option}
                                                                    checked={selectedAnswer === option}
                                                                    onChange={() => {
                                                                        if (isCorrect === undefined || isCorrect === null) {
                                                                            setMcqAnswers({ ...mcqAnswers, [idx]: option });
                                                                        }
                                                                    }}
                                                                    disabled={isCorrect !== undefined && isCorrect !== null}
                                                                    className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                                                                />
                                                                <span className="ml-3 text-gray-900">{option}</span>
                                                            </label>
                                                        ))}
                                                    </div>

                                                    {isCorrect === undefined || isCorrect === null ? (
                                                        <button
                                                            onClick={() => {
                                                                if (!selectedAnswer) return;
                                                                const correct = selectedAnswer === q.answer;
                                                                setMcqResults({ ...mcqResults, [idx]: correct });
                                                            }}
                                                            disabled={!selectedAnswer}
                                                            className={`mt-4 px-4 py-2 rounded-md text-sm font-medium ${!selectedAnswer
                                                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                                : 'bg-indigo-600 text-white hover:bg-indigo-700'
                                                                }`}
                                                        >
                                                            정답 확인
                                                        </button>
                                                    ) : (
                                                        <div className={`mt-4 p-4 rounded-md ${isCorrect ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                                                            <p className={`font-bold ${isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                                                                {isCorrect ? '✓ 정답입니다!' : '✗ 오답입니다.'}
                                                            </p>
                                                            <p className="mt-2 text-gray-700">
                                                                <span className="font-semibold">해설:</span> {q.explanation}
                                                            </p>
                                                            {!isCorrect && (
                                                                <button
                                                                    onClick={() => {
                                                                        setMcqResults({ ...mcqResults, [idx]: null });
                                                                        setMcqAnswers({ ...mcqAnswers, [idx]: '' });
                                                                    }}
                                                                    className="mt-3 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
                                                                >
                                                                    다시 풀기
                                                                </button>
                                                            )}
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}

                            {activeTab === 'advanced' && (
                                <div className="animate-fadeIn">
                                    <h2 className="text-2xl font-bold text-gray-900 mb-6">심화 학습 (주관식)</h2>
                                    <div className="space-y-8">
                                        {content.advanced_learning.quizes.map((q, idx) => {
                                            const grading = quizGradings[idx];
                                            const isGrading = gradingLoading[idx];
                                            return (
                                                <div key={idx} className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                                                    <span className="inline-block px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 mb-3">
                                                        심화 문제 {idx + 1}
                                                    </span>
                                                    <h3 className="text-lg font-medium text-gray-900 mb-4">{q.quiz}</h3>
                                                    <textarea
                                                        className="w-full h-32 p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 mb-3 text-gray-900 bg-white placeholder:text-gray-400"
                                                        placeholder="답변을 입력하세요..."
                                                        value={quizAnswers[idx] || ''}
                                                        onChange={(e) => setQuizAnswers({ ...quizAnswers, [idx]: e.target.value })}
                                                        disabled={!!grading}
                                                    />
                                                    {!grading ? (
                                                        <button
                                                            onClick={() => handleGradeQuiz(idx, q.quiz)}
                                                            disabled={isGrading || !quizAnswers[idx]?.trim()}
                                                            className={`px-4 py-2 rounded-md text-sm font-medium ${isGrading || !quizAnswers[idx]?.trim()
                                                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                                                : 'bg-indigo-600 text-white hover:bg-indigo-700'
                                                                }`}
                                                        >
                                                            {isGrading ? '채점 중...' : '✓ 채점하기'}
                                                        </button>
                                                    ) : (
                                                        <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
                                                            <div className="flex items-center justify-between mb-3">
                                                                <span className="text-lg font-bold text-gray-900">점수: {grading.score}점</span>
                                                            </div>
                                                            <div className="mb-3">
                                                                <h4 className="font-medium text-gray-900 mb-2">피드백:</h4>
                                                                <p className="text-gray-700">{grading.feedback}</p>
                                                            </div>
                                                            {grading.correct_points.length > 0 && (
                                                                <div className="mb-3">
                                                                    <h4 className="font-medium text-green-700 mb-2">✓ 잘한 점:</h4>
                                                                    <ul className="list-disc list-inside text-sm text-gray-700">
                                                                        {grading.correct_points.map((point, i) => (
                                                                            <li key={i}>{point}</li>
                                                                        ))}
                                                                    </ul>
                                                                </div>
                                                            )}
                                                            {grading.improvements.length > 0 && (
                                                                <div>
                                                                    <h4 className="font-medium text-orange-700 mb-2">📝 개선할 점:</h4>
                                                                    <ul className="list-disc list-inside text-sm text-gray-700">
                                                                        {grading.improvements.map((improvement, i) => (
                                                                            <li key={i}>{improvement}</li>
                                                                        ))}
                                                                    </ul>
                                                                </div>
                                                            )}
                                                            <button
                                                                onClick={() => {
                                                                    setQuizGradings({ ...quizGradings, [idx]: null });
                                                                    setQuizAnswers({ ...quizAnswers, [idx]: '' });
                                                                }}
                                                                className="mt-4 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 hover:border-gray-400 transition-colors shadow-sm"
                                                            >
                                                                다시 답변하기
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : null}
                </div>

                {/* Feedback Section */}
                {
                    content && (
                        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                            <h3 className="text-lg font-bold text-gray-900 mb-4">이 챕터는 어떠셨나요?</h3>
                            {!feedbackSubmitted ? (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-2">
                                        {[1, 2, 3, 4, 5].map((star) => (
                                            <button
                                                key={star}
                                                onClick={() => setRating(star)}
                                                className={`text-2xl focus:outline-none transition-transform hover:scale-110 ${rating >= star ? 'text-yellow-400' : 'text-gray-300'
                                                    }`}
                                            >
                                                ★
                                            </button>
                                        ))}
                                        <span className="text-sm text-gray-500 ml-2">
                                            {rating > 0 ? `${rating}점` : '별점을 선택해주세요'}
                                        </span>
                                    </div>
                                    <textarea
                                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-gray-900 placeholder:text-gray-400"
                                        placeholder="좋았던 점이나 아쉬웠던 점을 자유롭게 남겨주세요 (선택사항)"
                                        rows={3}
                                        value={comment}
                                        onChange={(e) => setComment(e.target.value)}
                                    />
                                    <div className="flex justify-end">
                                        <button
                                            onClick={handleFeedbackSubmit}
                                            disabled={isSubmittingFeedback || rating === 0}
                                            className={`px-4 py-2 rounded-md text-sm font-medium text-white ${isSubmittingFeedback || rating === 0
                                                ? 'bg-gray-300 cursor-not-allowed'
                                                : 'bg-indigo-600 hover:bg-indigo-700'
                                                }`}
                                        >
                                            {isSubmittingFeedback ? '제출 중...' : '피드백 보내기'}
                                        </button>
                                    </div>
                                </div>
                            ) : (
                                <div className="text-center py-4 text-green-600 bg-green-50 rounded-lg">
                                    <p className="font-medium">✓ 소중한 의견 감사합니다!</p>
                                    <p className="text-sm mt-1">다음 학습 콘텐츠 생성에 반영하겠습니다.</p>
                                </div>
                            )}
                        </div>
                    )
                }


                {/* Navigation Buttons */}
                <div className="flex justify-between mt-8">
                    <button
                        onClick={handlePrev}
                        disabled={chapterIndex === 0 || isLoading}
                        className={`px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 ${(chapterIndex === 0 || isLoading) ? 'opacity-50 cursor-not-allowed' : ''
                            }`}
                    >
                        이전 챕터
                    </button>
                    {chapterIndex === course.chapters.length - 1 ? (
                        <button
                            onClick={() => navigate('/dashboard')}
                            disabled={isLoading}
                            className={`px-6 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-green-600 hover:bg-green-700 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            ✓ 학습 완료
                        </button>
                    ) : (
                        <button
                            onClick={handleNext}
                            disabled={isLoading}
                            className={`px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                        >
                            다음 챕터
                        </button>
                    )}
                </div>
            </main >

            <SurveyModal
                isOpen={showSurvey}
                onComplete={() => {
                    sessionStorage.setItem('survey_completed', 'true');
                    setShowSurvey(false);
                }}
                isGenerating={isLoading}
            />
        </div >
    );
}
