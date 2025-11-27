/**
 * PopPins II - API 클라이언트 서비스
 * 
 * 백엔드 API와 통신하는 모든 함수를 제공합니다.
 * axios를 사용하여 HTTP 요청을 처리하며, 타입 안정성을 보장합니다.
 * 
 * 주요 기능:
 * - 학습 목표 생성
 * - 커리큘럼 생성
 * - 챕터 콘텐츠 생성
 * - 퀴즈 채점
 * - 코스 관리 (조회, 삭제)
 * 
 * @module services/api
 * @author PopPins II 개발팀
 * @version 1.0.0
 */

import axios from 'axios';
import type { GenerateRequest, StudyMaterialResponse, CourseResponse, ChapterContent, ChapterRequest, QuizGradingRequest, QuizGradingResponse, ObjectivesResponse, FeedbackRequest, CourseListItem } from '../types';

/**
 * 백엔드 API 기본 URL
 * 
 * 환경 변수 VITE_API_BASE_URL을 사용하며, 설정되지 않은 경우 기본값으로 localhost:8001을 사용합니다.
 * 
 * 개발 환경: .env 파일에 VITE_API_BASE_URL=http://localhost:8001 설정
 * 프로덕션 환경: 배포 환경에 맞게 VITE_API_BASE_URL 설정
 * 
 * @example
 * // .env 파일
 * VITE_API_BASE_URL=http://localhost:8001
 * 
 * // 프로덕션
 * VITE_API_BASE_URL=https://api.example.com
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

export const generateStudyMaterial = async (data: GenerateRequest): Promise<StudyMaterialResponse> => {
    const response = await axios.post(`${API_BASE_URL}/generate-study-material`, data);
    return response.data;
};

/**
 * 커리큘럼(목차)을 생성합니다.
 * 
 * 사용자가 입력한 주제를 바탕으로 AI가 교육 커리큘럼을 생성합니다.
 * 챕터 목록만 먼저 생성하여 사용자가 구조를 확인할 수 있습니다.
 * 
 * @param data - 커리큘럼 생성 요청 데이터
 *   - topic: 학습 주제 (필수)
 *   - difficulty: 난이도 (초급/중급/고급)
 *   - max_chapters: 최대 챕터 수
 *   - selected_objective: 선택된 학습 목표 (선택사항)
 *   - language: 출력 언어 (ko/en)
 * 
 * @returns 생성된 커리큘럼 정보
 *   - course: 코스 정보 (id, topic, chapters 등)
 * 
 * @throws {AxiosError} API 요청 실패 시
 *   - 500: 서버 오류 (AI 생성 실패 등)
 * 
 * @example
 * ```typescript
 * const course = await generateCourse({
 *   topic: "파이썬 리스트",
 *   difficulty: "중급",
 *   max_chapters: 3
 * });
 * console.log(course.course.chapters); // 챕터 목록
 * ```
 */
export const generateCourse = async (data: GenerateRequest): Promise<CourseResponse> => {
    const response = await axios.post(`${API_BASE_URL}/generate-course`, data);
    return response.data;
};

/**
 * 특정 챕터의 상세 콘텐츠를 생성합니다.
 * 
 * 사용자가 챕터를 클릭했을 때 호출됩니다.
 * 개념 설명, 실습 과제, 퀴즈 문제를 한 번에 생성합니다.
 * 
 * @param data - 챕터 콘텐츠 생성 요청 데이터
 *   - course_title: 코스 제목
 *   - course_description: 코스 설명
 *   - chapter_title: 챕터 제목
 *   - chapter_description: 챕터 설명
 * 
 * @returns 챕터의 전체 콘텐츠
 *   - chapter: 챕터 기본 정보
 *   - concept: 개념 설명 (Markdown)
 *   - exercise: 실습 과제 (Markdown)
 *   - quiz: 퀴즈 문제 목록
 * 
 * @throws {AxiosError} API 요청 실패 시
 *   - 500: 서버 오류 (AI 생성 실패 등)
 * 
 * @example
 * ```typescript
 * const content = await generateChapterContent({
 *   course_title: "파이썬 리스트",
 *   course_description: "...",
 *   chapter_title: "리스트 기초",
 *   chapter_description: "..."
 * });
 * console.log(content.concept.contents); // 개념 설명
 * ```
 */
export const generateChapterContent = async (data: ChapterRequest): Promise<ChapterContent> => {
    const response = await axios.post(`${API_BASE_URL}/generate-chapter-content`, data);
    return response.data;
};

export const checkHealth = async (): Promise<boolean> => {
    try {
        await axios.get(`${API_BASE_URL}/health`);
        return true;
    } catch (error) {
        return false;
    }
};

export const downloadChapter = async (data: ChapterRequest): Promise<{ filename: string; content: string }> => {
    const response = await axios.post(`${API_BASE_URL}/download-chapter`, data);
    return response.data;
};

export const gradeQuiz = async (data: QuizGradingRequest): Promise<QuizGradingResponse> => {
    const response = await axios.post(`${API_BASE_URL}/grade-quiz`, data);
    return response.data;
};

export const generateObjectives = async (topic: string, language: string = 'ko'): Promise<ObjectivesResponse> => {
    const response = await axios.post(`${API_BASE_URL}/generate-objectives`, { topic, language });
    return response.data;
};

export const submitFeedback = async (data: FeedbackRequest): Promise<{ status: string; message: string }> => {
    const response = await axios.post(`${API_BASE_URL}/feedback`, data);
    return response.data;
};

/**
 * 저장된 모든 코스 목록을 조회합니다.
 * 
 * 대시보드에서 사용자의 모든 코스를 표시하기 위해 호출됩니다.
 * 각 코스의 진행률, 완료된 챕터 수 등 통계 정보도 포함됩니다.
 * 
 * @returns 코스 목록 배열
 *   각 항목은 다음 정보 포함:
 *   - id: 코스 ID
 *   - topic: 코스 제목
 *   - description: 코스 설명
 *   - level: 난이도
 *   - created_at: 생성일시
 *   - chapter_count: 전체 챕터 수
 *   - completed_chapters: 완료된 챕터 수
 *   - progress: 진행률 (0-100)
 * 
 * @throws {AxiosError} API 요청 실패 시
 * 
 * @example
 * ```typescript
 * const courses = await getCourses();
 * courses.forEach(course => {
 *   console.log(`${course.topic}: ${course.progress}% 완료`);
 * });
 * ```
 */
export const getCourses = async (): Promise<CourseListItem[]> => {
    const response = await axios.get(`${API_BASE_URL}/courses`);
    return response.data;
};

export const getCourse = async (courseId: number): Promise<CourseResponse> => {
    const response = await axios.get(`${API_BASE_URL}/courses/${courseId}`);
    return response.data;
};

export const deleteCourse = async (courseId: number): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/courses/${courseId}`);
};

export const saveUserPreference = async (preferences: {
    learning_goal: string;
    learning_style: string;
    desired_depth: string;
}): Promise<void> => {
    await axios.post(`${API_BASE_URL}/user/preferences`, preferences);
};