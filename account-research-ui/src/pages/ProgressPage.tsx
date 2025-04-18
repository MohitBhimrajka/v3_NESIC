import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  Clock, 
  Loader2 
} from 'lucide-react';

import api, { Task } from '../api/client';
import { Progress } from '../components/ui/progress';
import { Button } from '../components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';

// Define the user info schema
const userInfoSchema = z.object({
  name: z.string().min(2, 'Name is required'),
  email: z.string().email('Invalid email address'),
  designation: z.string().min(2, 'Designation is required'),
});

type UserInfo = z.infer<typeof userInfoSchema>;

// Task section statuses mapped to UI components
const StatusIcon = ({ status }: { status: string }) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-5 h-5 text-lime" />;
    case 'error':
      return <XCircle className="w-5 h-5 text-orange" />;
    case 'pending':
      return <Clock className="w-5 h-5 text-blue" />;
    case 'processing':
      return <Loader2 className="w-5 h-5 text-blue animate-spin" />;
    default:
      return <AlertCircle className="w-5 h-5 text-gray-lt" />;
  }
};

export default function ProgressPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [userInfoDialogOpen, setUserInfoDialogOpen] = useState(true);
  const [hasUserInfo, setHasUserInfo] = useState(false);

  // Check local storage for user info
  useEffect(() => {
    const storedUserInfo = localStorage.getItem('userInfo');
    if (storedUserInfo) {
      setHasUserInfo(true);
      setUserInfoDialogOpen(false);
    }
  }, []);

  // Form handling
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<UserInfo>({
    resolver: zodResolver(userInfoSchema),
  });

  // Handle form submission
  const onSubmit = async (data: UserInfo) => {
    localStorage.setItem('userInfo', JSON.stringify(data));
    setHasUserInfo(true);
    setUserInfoDialogOpen(false);
  };

  // Task status polling
  const { data: task, error } = useQuery<Task>({
    queryKey: ['task', id],
    queryFn: () => api.getTaskStatus(id!),
    enabled: !!id && hasUserInfo,
    refetchInterval: 3000, // Poll every 3 seconds
    refetchOnWindowFocus: false,
  });

  // Handle task completion or failure
  useEffect(() => {
    if (task) {
      if (task.status === 'completed') {
        navigate(`/task/${id}/result`);
      }
    }
  }, [task, id, navigate]);

  // Mock log data structure (in real app, this would come from the API)
  const taskLogs = [
    { id: 'init', label: 'Initializing task', status: 'completed' },
    { id: 'data', label: 'Gathering company data', status: task?.status === 'pending' ? 'pending' : 'processing' },
    { id: 'analysis', label: 'Running analysis', status: task?.progress && task.progress > 30 ? 'processing' : 'pending' },
    { id: 'report', label: 'Generating report', status: task?.progress && task.progress > 70 ? 'processing' : 'pending' },
  ];

  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">Task Progress</h1>

        {/* User Info Modal */}
        <Dialog open={userInfoDialogOpen} onOpenChange={setUserInfoDialogOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Enter your information</DialogTitle>
              <DialogDescription>
                We need a few details to track your request. This will help us personalize your results.
              </DialogDescription>
            </DialogHeader>
            
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 py-4">
              <div className="grid w-full items-center gap-1.5">
                <label htmlFor="name" className="text-sm font-medium text-white">
                  Name
                </label>
                <input
                  id="name"
                  className="w-full p-2 rounded-md border-gray-dk bg-navy text-white focus:border-lime focus:outline-none focus:ring-1 focus:ring-lime"
                  {...register("name")}
                />
                {errors.name && (
                  <p className="text-orange text-sm">{errors.name.message}</p>
                )}
              </div>

              <div className="grid w-full items-center gap-1.5">
                <label htmlFor="email" className="text-sm font-medium text-white">
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  className="w-full p-2 rounded-md border-gray-dk bg-navy text-white focus:border-lime focus:outline-none focus:ring-1 focus:ring-lime"
                  {...register("email")}
                />
                {errors.email && (
                  <p className="text-orange text-sm">{errors.email.message}</p>
                )}
              </div>

              <div className="grid w-full items-center gap-1.5">
                <label htmlFor="designation" className="text-sm font-medium text-white">
                  Job Title / Designation
                </label>
                <input
                  id="designation"
                  className="w-full p-2 rounded-md border-gray-dk bg-navy text-white focus:border-lime focus:outline-none focus:ring-1 focus:ring-lime"
                  {...register("designation")}
                />
                {errors.designation && (
                  <p className="text-orange text-sm">{errors.designation.message}</p>
                )}
              </div>

              <DialogFooter>
                <Button type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Saving..." : "Continue"}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Task progress content */}
        <div className="bg-navy rounded-xl p-6 shadow-lg">
          {error || task?.status === 'failed' ? (
            <div className="bg-navy border border-orange/30 rounded-lg p-4 text-white">
              <div className="flex items-center gap-2 text-orange mb-2">
                <AlertCircle className="w-5 h-5" />
                <h3 className="font-semibold">Task Failed</h3>
              </div>
              <p className="text-gray-lt">{task?.error || 'An error occurred while processing your request. Please try again.'}</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={() => navigate('/generate')}
              >
                Start New Request
              </Button>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <div className="flex justify-between text-white mb-2">
                  <span>Processing your request</span>
                  <span>{task?.progress ? `${task.progress}%` : 'Initializing...'}</span>
                </div>
                <Progress value={task?.progress} />
              </div>

              <div className="space-y-4 mt-8">
                <h3 className="text-white font-medium mb-4">Progress Log</h3>
                
                {taskLogs.map((log) => (
                  <div key={log.id} className="flex items-center gap-3 text-white border-b border-gray-dk pb-3">
                    <StatusIcon status={log.status} />
                    <span>{log.label}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
} 