import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Eye } from 'lucide-react';

import api, { Task } from '../api/client';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';

// Status variants mapping for badges
const statusVariant = (status: string) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'processing':
    case 'pending':
      return 'info';
    case 'failed':
      return 'warning';
    default:
      return 'default';
  }
};

// Format date to readable string
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export default function HistoryPage() {
  const navigate = useNavigate();
  
  // Fetch tasks
  const { data: tasks, isLoading, error, refetch } = useQuery({
    queryKey: ['tasks'],
    queryFn: api.listTasks,
    refetchOnWindowFocus: false,
    staleTime: 60000, // 1 minute
  });

  // View task result or progress
  const handleViewTask = (task: Task) => {
    if (task.status === 'completed') {
      navigate(`/task/${task.id}/result`);
    } else {
      navigate(`/task/${task.id}`);
    }
  };

  // Refresh list every minute
  useEffect(() => {
    const intervalId = setInterval(() => {
      refetch();
    }, 60000);
    
    return () => clearInterval(intervalId);
  }, [refetch]);
  
  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">Research History</h1>
        
        <div className="bg-navy rounded-xl p-6 shadow-lg">
          {isLoading ? (
            <div className="text-center py-8">
              <p className="text-white">Loading task history...</p>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-orange">Error loading task history</p>
              <Button onClick={() => refetch()} className="mt-4" variant="outline">
                Try Again
              </Button>
            </div>
          ) : tasks && tasks.length > 0 ? (
            <Table>
              <TableCaption>Your account research task history</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>Task ID</TableHead>
                  <TableHead>Company</TableHead>
                  <TableHead>Language</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell className="font-medium text-white">
                      {task.id.substring(0, 8)}...
                    </TableCell>
                    <TableCell className="text-white">
                      {task.request.targetCompany || 'N/A'}
                    </TableCell>
                    <TableCell className="text-white">
                      {task.request.language || 'English'}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(task.status)}>
                        {task.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-gray-lt">
                      {formatDate(task.created_at)}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewTask(task)}
                        className="text-blue hover:text-blue"
                      >
                        <Eye className="h-4 w-4 mr-1" />
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-12">
              <p className="text-white mb-4">No research tasks found</p>
              <Button onClick={() => navigate('/generate')} variant="primary">
                Create Your First Report
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 