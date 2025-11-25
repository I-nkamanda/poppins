import axios from 'axios';
import type { GenerateRequest, StudyMaterialResponse, CourseResponse, ChapterContent, ChapterRequest } from '../types';

const API_BASE_URL = 'http://localhost:8001';

export const generateStudyMaterial = async (data: GenerateRequest): Promise<StudyMaterialResponse> => {
    const response = await axios.post(`${API_BASE_URL}/generate-study-material`, data);
    return response.data;
};

export const generateCourse = async (data: GenerateRequest): Promise<CourseResponse> => {
    const response = await axios.post(`${API_BASE_URL}/generate-course`, data);
    return response.data;
};

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

export interface QuizGradingRequest {
    question: string;
    answer: string;
    chapter_title: string;
    chapter_description: string;
}

export interface QuizGradingResponse {
    score: number;
    feedback: string;
    correct_points: string[];
    improvements: string[];
}

export const gradeQuiz = async (data: QuizGradingRequest): Promise<QuizGradingResponse> => {
    const response = await axios.post(`${API_BASE_URL}/grade-quiz`, data);
    return response.data;
};