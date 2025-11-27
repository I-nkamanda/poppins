export interface Chapter {
    chapterId: number;
    chapterTitle: string;
    chapterDescription: string;
}

export interface Course {
    id: number;
    topic?: string;
    description?: string;
    level?: string;
    chapters: Chapter[];
}

export interface Concept {
    title: string;
    description: string;
    contents: string;
}

export interface Exercise {
    title: string;
    description: string;
    contents: string;
}

export interface MCQItem {
    question: string;
    options: string[];
    answer: string;
    explanation: string;
}

export interface Quiz {
    quizes: MCQItem[];
}

export interface AdvancedItem {
    quiz: string;
}

export interface AdvancedLearning {
    quizes: AdvancedItem[];
}

export interface ChapterContent {
    chapter: Chapter;
    concept: Concept;
    exercise: Exercise;
    quiz: Quiz;
    advanced_learning: AdvancedLearning;
}

export interface StudyMaterialResponse {
    course: Course;
    chapters: ChapterContent[];
}

export interface GenerateRequest {
    topic: string;
    difficulty: string;
    chapter_count?: number;
    max_chapters?: number; // Keeping for backward compatibility if needed
    course_description?: string;
    selected_objective?: string;
    language?: string;
}

export interface ChapterRequest {
    course_title: string;
    course_description: string;
    chapter_title: string;
    chapter_description: string;
}

export interface CourseResponse {
    course: Course;
}

export interface ObjectiveItem {
    id: number;
    title: string;
    description: string;
    target_audience: string;
}

export interface ObjectivesResponse {
    objectives: ObjectiveItem[];
}

export interface FeedbackRequest {
    chapter_title: string;
    rating: number;
    comment: string;
}

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

export interface CourseListItem {
    id: number;
    topic: string;
    description: string;
    level: string;
    created_at: string;
    chapter_count: number;
    completed_chapters: number;
    progress: number;
}

export interface QuizResultItem {
    id: number;
    chapter_title: string;
    score: number;
    weak_points: string; // JSON string
    correct_points?: string; // JSON string
    feedback?: string;
    user_answer?: string;
    timestamp: string;
}

export interface QuizResultListResponse {
    results: QuizResultItem[];
}
