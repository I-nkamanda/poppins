import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { generateCourse, getCourses } from './api';

// Mock axios
vi.mock('axios');
const mockedAxios = axios as any;

describe('API Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('generateCourse', () => {
    it('should call the correct endpoint with request data', async () => {
      const mockData = {
        topic: 'Python',
        difficulty: '초급',
        max_chapters: 3,
      };

      const mockResponse = {
        data: {
          course: {
            id: 1,
            chapters: [
              { chapterId: 1, chapterTitle: 'Chapter 1', chapterDescription: 'Desc 1' },
            ],
          },
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      const result = await generateCourse(mockData);

      expect(mockedAxios.post).toHaveBeenCalledWith(
        expect.stringContaining('/generate-course'),
        mockData
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('getCourses', () => {
    it('should fetch courses list', async () => {
      const mockResponse = {
        data: [
          { id: 1, topic: 'Python', progress: 50 },
          { id: 2, topic: 'JavaScript', progress: 75 },
        ],
      };

      mockedAxios.get.mockResolvedValue(mockResponse);

      const result = await getCourses();

      expect(mockedAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/courses')
      );
      expect(result).toEqual(mockResponse.data);
    });
  });
});

