import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { Document, Page, pdfjs } from 'react-pdf';
import { Download, ExternalLink, FileText, AlertCircle } from 'lucide-react';

import api from '../api/client';
import { Button } from '../components/ui/button';

// Set up the worker for PDF.js
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

export default function ResultPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [numPages, setNumPages] = useState<number | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<boolean>(false);

  // Fetch task data once
  const { data: task, isLoading: taskLoading, error: taskError } = useQuery({
    queryKey: ['task', id],
    queryFn: () => api.getTaskStatus(id!),
    enabled: !!id,
    refetchOnWindowFocus: false,
    refetchInterval: false,
    staleTime: Infinity,
  });

  // Load PDF data
  useEffect(() => {
    const loadPdf = async () => {
      try {
        const blob = await api.downloadPdf(id!);
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
      } catch (error) {
        console.error('Error loading PDF:', error);
        setPdfError(true);
      }
    };

    if (id && task?.status === 'completed') {
      loadPdf();
    }
  }, [id, task]);

  // Handle PDF document loading
  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages);
  }

  // Handle PDF download
  const handleDownload = async () => {
    try {
      const blob = await api.downloadPdf(id!);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `account-research-${id}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading PDF:', error);
    }
  };

  if (taskLoading) {
    return (
      <div className="min-h-screen bg-black p-6 flex items-center justify-center">
        <div className="text-white">Loading result...</div>
      </div>
    );
  }

  if (taskError || task?.status === 'failed') {
    return (
      <div className="min-h-screen bg-black p-6">
        <div className="max-w-6xl mx-auto bg-navy rounded-xl p-6 shadow-lg">
          <div className="flex items-center gap-2 text-orange mb-4">
            <AlertCircle className="w-5 h-5" />
            <h2 className="text-xl font-semibold text-white">Error Loading Result</h2>
          </div>
          <p className="text-gray-lt mb-6">
            We encountered an error retrieving this report. The task may have failed or the report is no longer available.
          </p>
          <Button
            variant="primary"
            onClick={() => navigate('/generate')}
          >
            Start New Report
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-white mb-6">Report Results</h1>
        
        <div className="flex flex-col lg:flex-row gap-6">
          {/* PDF Preview - Left Column (2/3) */}
          <div className="w-full lg:w-2/3 bg-navy rounded-xl p-6 shadow-lg mb-6 lg:mb-0">
            <h2 className="text-xl font-semibold text-white mb-4">
              Account Research Report
            </h2>
            
            <div className="bg-white rounded-lg min-h-[700px] w-full overflow-auto">
              {pdfUrl ? (
                <Document
                  file={pdfUrl}
                  onLoadSuccess={onDocumentLoadSuccess}
                  onLoadError={() => setPdfError(true)}
                  loading={
                    <div className="flex items-center justify-center h-full min-h-[500px]">
                      <p className="text-gray-dk">Loading PDF...</p>
                    </div>
                  }
                  error={
                    <div className="flex items-center justify-center h-full min-h-[500px]">
                      <div className="text-center">
                        <AlertCircle className="w-12 h-12 text-orange mx-auto mb-4" />
                        <p className="text-gray-dk">Failed to load PDF preview</p>
                        <p className="text-gray-dk text-sm mt-2">Please try downloading the file directly</p>
                      </div>
                    </div>
                  }
                >
                  {Array.from(new Array(numPages || 0), (_, index) => (
                    <Page 
                      key={`page_${index + 1}`} 
                      pageNumber={index + 1} 
                      renderTextLayer={false}
                      renderAnnotationLayer={false}
                      className="mb-4"
                      width={Math.min(window.innerWidth * 0.6, 800)}
                    />
                  ))}
                </Document>
              ) : pdfError ? (
                <div className="flex items-center justify-center h-full min-h-[500px]">
                  <div className="text-center">
                    <AlertCircle className="w-12 h-12 text-orange mx-auto mb-4" />
                    <p className="text-gray-dk">Failed to load PDF preview</p>
                    <p className="text-gray-dk text-sm mt-2">Please try downloading the file directly</p>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center h-full min-h-[500px]">
                  <p className="text-gray-dk">Loading PDF...</p>
                </div>
              )}
            </div>
            
            <div className="mt-6">
              <Button variant="primary" onClick={handleDownload} className="flex items-center gap-2">
                <Download className="w-4 h-4" />
                Download PDF
              </Button>
            </div>
          </div>
          
          {/* Tips Card - Right Column (1/3) */}
          <div className="w-full lg:w-1/3">
            <div className="bg-navy rounded-xl p-6 shadow-lg mb-6">
              <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Next Steps & Tips
              </h2>
              
              <ul className="space-y-4 text-gray-lt">
                <li className="flex gap-2">
                  <span className="text-lime font-bold">1.</span>
                  <span>Large reports can take a minute to render in your browser—download if preview is blank.</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-lime font-bold">2.</span>
                  <span>Check inline citations inside the PDF for source traceability.</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-lime font-bold">3.</span>
                  <span>Need more sections? Re-run with Advanced options.</span>
                </li>
              </ul>
              
              <div className="mt-6">
                <Button 
                  variant="outline" 
                  onClick={() => navigate('/generate')}
                  className="w-full"
                >
                  Start Another Report
                </Button>
              </div>
            </div>
            
            {task?.request && (
              <div className="bg-navy rounded-xl p-6 shadow-lg">
                <h3 className="text-lg font-semibold text-white mb-3">Report Details</h3>
                
                <div className="space-y-2 text-sm">
                  <div>
                    <span className="text-gray-lt">Target Company:</span>
                    <span className="ml-2 text-white">{task.request.targetCompany}</span>
                  </div>
                  <div>
                    <span className="text-gray-lt">Language:</span>
                    <span className="ml-2 text-white">{task.request.language}</span>
                  </div>
                  <div>
                    <span className="text-gray-lt">Generated:</span>
                    <span className="ml-2 text-white">
                      {new Date(task.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {task.request.sections && task.request.sections.length > 0 && (
                    <div>
                      <span className="text-gray-lt">Sections:</span>
                      <span className="ml-2 text-white">
                        {task.request.sections.length} selected
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 