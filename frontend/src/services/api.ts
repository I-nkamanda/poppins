import axios from 'axios';
import type { GenerateRequest, StudyMaterialResponse, CourseResponse, ChapterContent, ChapterRequest, QuizGradingRequest, QuizGradingResponse, ObjectivesResponse, FeedbackRequest, CourseListItem } from '../types';

const API_BASE_URL = 'http://localhost:8002';

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