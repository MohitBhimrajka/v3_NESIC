import axios from 'axios';
import { FormValues } from '../pages/generate/WizardContext';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export type Task = {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
  formData: FormValues;
  result?: any;
};

export const apiService = {
  async createTask(formData: FormValues): Promise<{ taskId: string }> {
    // In a real app, this would be an actual API call
    // For now, let's simulate a successful response
    await new Promise(resolve => setTimeout(resolve, 1000));
    const taskId = `task-${Date.now()}`;
    console.log('Created task with ID:', taskId, 'Form data:', formData);
    return { taskId };
  },
  
  async getTask(taskId: string): Promise<Task> {
    // In a real app, this would be an actual API call
    await new Promise(resolve => setTimeout(resolve, 500));
    return {
      id: taskId,
      status: 'pending',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      formData: {} as FormValues,
    };
  }
};

export default apiService; 