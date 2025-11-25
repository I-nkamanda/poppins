export interface Chapter {
    chapterId: number;
    chapterTitle: string;
    chapterDescription: string;
}

export interface Course {
    id: number;
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

export interface QuizItem {
    quiz: string;
}

export interface Quiz {
    quizes: QuizItem[];
}

export interface ChapterContent {
    chapter: Chapter;
    concept: Concept;
    exercise: Exercise;
    quiz: Quiz;
}

export interface StudyMaterialResponse {
    course: Course;
    chapters: ChapterContent[];
}

export interface GenerateRequest {
    topic: string;
    difficulty: string;
    max_chapters: number;
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
