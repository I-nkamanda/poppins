import { useState, useEffect } from 'react';
import { saveUserPreference } from '../services/api';

interface SurveyModalProps {
    isOpen: boolean;
    onComplete: () => void;
    isGenerating: boolean;
}

export default function SurveyModal({ isOpen, onComplete, isGenerating }: SurveyModalProps) {
    const [step, setStep] = useState(1);
    const [answers, setAnswers] = useState({
        learning_goal: '',
        learning_style: '',
        desired_depth: '',
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isSubmitted, setIsSubmitted] = useState(false);

    // Auto-close when generation finishes if already submitted
    useEffect(() => {
        if (isSubmitted && !isGenerating) {
            const timer = setTimeout(() => {
                onComplete();
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, [isSubmitted, isGenerating, onComplete]);

    if (!isOpen) return null;

    const handleSelect = (key: string, value: string) => {
        setAnswers(prev => ({ ...prev, [key]: value }));
        if (step < 3) {
            setStep(prev => prev + 1);
        }
    };

    const handleSubmit = async () => {
        setIsSubmitting(true);
        try {
            await saveUserPreference(answers);
            setIsSubmitted(true);
            setTimeout(() => {
                onComplete();
            }, 1000);
        } catch (error) {
            console.error('Failed to save preferences:', error);
            onComplete();
        } finally {
            setIsSubmitting(false);
        }
    };

    if (isSubmitted) {
        return (
            <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50">
                <div className="bg-white rounded-2xl p-8 max-w-md w-full text-center animate-fade-in relative">
                    {!isGenerating && (
                        <button
                            onClick={onComplete}
                            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
                        >
                            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                        </button>
                    )}
                    <div className="text-5xl mb-4">✨</div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-3">설문 완료!</h3>
                    <p className="text-gray-700 text-lg mb-6">
                        답변해주셔서 감사합니다.<br />
                        {isGenerating ? 'AI가 열심히 커리큘럼을 만들고 있어요...' : '커리큘럼 생성이 완료되었습니다!'}
                    </p>
                    {isGenerating ? (
                        <div className="flex justify-center">
                            <div className="animate-spin rounded-full h-10 w-10 border-b-3 border-indigo-600"></div>
                        </div>
                    ) : (
                        <button
                            onClick={onComplete}
                            className="bg-indigo-600 text-white text-lg px-8 py-3 rounded-xl font-semibold hover:bg-indigo-700 transition-colors shadow-lg"
                        >
                            학습 시작하기
                        </button>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl p-10 max-w-lg w-full shadow-2xl">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="text-2xl font-bold text-gray-900">
                        잠시만요! ✋
                    </h3>
                    <span className="text-lg font-semibold text-indigo-600 bg-indigo-50 px-4 py-2 rounded-full">
                        {step}/3
                    </span>
                </div>

                <div className="mb-10">
                    {step === 1 && (
                        <div className="animate-slide-in">
                            <h4 className="text-2xl font-bold mb-8 text-gray-900">
                                이 주제를 배우려는 목적이 무엇인가요?
                            </h4>
                            <div className="space-y-4">
                                {['취업/이직 준비', '업무 스킬 향상', '취미/자기계발', '학교 과제/연구'].map((opt) => (
                                    <button
                                        key={opt}
                                        onClick={() => handleSelect('learning_goal', opt)}
                                        className={`w-full p-5 text-left text-lg rounded-xl border-2 transition-all font-medium ${answers.learning_goal === opt
                                                ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-md'
                                                : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-sm text-gray-800'
                                            }`}
                                    >
                                        {opt}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 2 && (
                        <div className="animate-slide-in">
                            <h4 className="text-2xl font-bold mb-8 text-gray-900">
                                선호하는 학습 스타일은 무엇인가요?
                            </h4>
                            <div className="space-y-4">
                                {['이론 중심 (원리부터 차근차근)', '실습 중심 (코드부터 짜보면서)', '균형 있게 (이론 반 실습 반)'].map((opt) => (
                                    <button
                                        key={opt}
                                        onClick={() => handleSelect('learning_style', opt)}
                                        className={`w-full p-5 text-left text-lg rounded-xl border-2 transition-all font-medium ${answers.learning_style === opt
                                                ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-md'
                                                : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-sm text-gray-800'
                                            }`}
                                    >
                                        {opt}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {step === 3 && (
                        <div className="animate-slide-in">
                            <h4 className="text-2xl font-bold mb-8 text-gray-900">
                                어느 정도 깊이로 배우고 싶으신가요?
                            </h4>
                            <div className="space-y-4">
                                {['핵심만 빠르게 (Quick Overview)', '적당한 깊이로 (Standard)', '아주 상세하게 (Deep Dive)'].map((opt) => (
                                    <button
                                        key={opt}
                                        onClick={() => setAnswers(prev => ({ ...prev, desired_depth: opt }))}
                                        className={`w-full p-5 text-left text-lg rounded-xl border-2 transition-all font-medium ${answers.desired_depth === opt
                                                ? 'border-indigo-600 bg-indigo-50 text-indigo-700 shadow-md'
                                                : 'border-gray-300 hover:border-indigo-400 hover:bg-indigo-50 hover:shadow-sm text-gray-800'
                                            }`}
                                    >
                                        {opt}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex justify-between items-center pt-6 border-t border-gray-200">
                    {step > 1 && (
                        <button
                            onClick={() => setStep(prev => prev - 1)}
                            className="text-gray-600 hover:text-gray-900 text-base font-semibold px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                            ← 이전
                        </button>
                    )}
                    {step === 3 && (
                        <button
                            onClick={handleSubmit}
                            disabled={!answers.desired_depth || isSubmitting}
                            className="ml-auto bg-indigo-600 text-white text-lg px-8 py-3 rounded-xl font-semibold hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-lg hover:shadow-xl"
                        >
                            {isSubmitting ? '저장 중...' : '제출하기'}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
