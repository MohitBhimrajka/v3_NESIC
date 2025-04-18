import axios from 'axios';
import { FormValues } from '../pages/generate/WizardContext';

// Create axios instance with configuration
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_BACKEND_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  }
});

// Types
export interface GenerationRequest extends FormValues {}

export interface Task {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  updated_at: string;
  request: GenerationRequest;
  error?: string;
}

// API functions
export const api = {
  /**
   * Create a new research task
   */
  async createTask(payload: GenerationRequest): Promise<{ task_id: string }> {
    const response = await apiClient.post('/generate', payload);
    return response.data;
  },

  /**
   * Get the status of a task
   */
  async getTaskStatus(id: string): Promise<Task> {
    const response = await apiClient.get(`/status/${id}`);
    return response.data;
  },

  /**
   * Download the PDF result of a completed task
   */
  async downloadPdf(id: string): Promise<Blob> {
    const response = await apiClient.get(`/result/${id}/pdf`, {
      responseType: 'blob'
    });
    return response.data;
  },

  /**
   * List all tasks for the current user
   */
  async listTasks(): Promise<Task[]> {
    const response = await apiClient.get('/tasks');
    return response.data;
  }
};

export default api; 