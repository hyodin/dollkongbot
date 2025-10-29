/**
 * 파일 업로드 컴포넌트
 * 드래그앤드롭과 파일 선택 기능 제공
 */

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';
import apiClient, { UploadResponse } from '../api/client';

interface FileUploadProps {
  onUploadSuccess?: (result: UploadResponse) => void;
  onUploadStart?: () => void;
  className?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUploadSuccess,
  onUploadStart,
  className = '',
}) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);

  // 지원되는 파일 형식
  const acceptedFileTypes = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'text/plain': ['.txt'],
  };

  const maxFileSize = 10 * 1024 * 1024; // 10MB

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    await handleFileUpload(file);
  }, []);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    maxFiles: 1,
    maxSize: maxFileSize,
  });

  const handleFileUpload = async (file: File) => {
    if (isUploading) return;

    setIsUploading(true);
    setUploadProgress(0);
    setUploadedFile(null);
    
    if (onUploadStart) {
      onUploadStart();
    }

    try {
      // 프로그레스 시뮬레이션 (실제로는 백엔드에서 프로그레스 제공해야 함)
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 300);

      const response = await apiClient.uploadFileSync(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.status === 'success') {
        setUploadedFile(file.name);
        toast.success(`파일 업로드 성공: ${file.name}`);
        
        if (onUploadSuccess) {
          onUploadSuccess(response);
        }
      } else {
        throw new Error(response.message || '업로드 실패');
      }

    } catch (error: any) {
      console.error('파일 업로드 오류:', error);
      
      // API 클라이언트에서 이미 에러 메시지를 처리했으므로 그대로 사용
      // toast.error는 제거 (잠자는 돌콩이 알림창이 대신 표시됨)
      
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
      
      // 3초 후 프로그레스 바 초기화
      setTimeout(() => {
        setUploadProgress(0);
        setUploadedFile(null);
      }, 3000);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* 드래그앤드롭 영역 */}
      <div
        {...getRootProps()}
        className={`upload-zone cursor-pointer ${
          isDragActive ? 'drag-over' : ''
        } ${isUploading ? 'pointer-events-none opacity-50' : ''}`}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {/* 업로드 아이콘 */}
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
            {isUploading ? (
              <div className="loading-spinner"></div>
            ) : (
              <svg
                className="w-8 h-8 text-primary-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            )}
          </div>

          {/* 텍스트 */}
          <div className="text-center">
            {isUploading ? (
              <div>
                <p className="text-lg font-medium text-gray-900">
                  파일 처리 중...
                </p>
                <p className="text-sm text-gray-500">
                  잠시만 기다려주세요
                </p>
              </div>
            ) : isDragActive ? (
              <div>
                <p className="text-lg font-medium text-primary-600">
                  파일을 여기에 놓으세요
                </p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-900">
                  파일을 드래그하거나 <span className="text-primary-600">클릭</span>하여 업로드
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  PDF, DOCX, XLSX, TXT 파일만 지원 (최대 10MB)
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 프로그레스 바 */}
      {uploadProgress > 0 && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">
              {uploadedFile || '파일 업로드 중...'}
            </span>
            <span className="text-gray-900 font-medium">
              {uploadProgress}%
            </span>
          </div>
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* 파일 형식 안내 */}
      <div className="bg-gray-50 rounded-lg p-4">
        <h4 className="text-sm font-medium text-gray-900 mb-2">
          지원되는 파일 형식
        </h4>
        <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-red-500 rounded-full"></span>
            <span>PDF 문서</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
            <span>Word 문서 (.docx)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-green-500 rounded-full"></span>
            <span>Excel 파일 (.xlsx)</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-gray-500 rounded-full"></span>
            <span>텍스트 파일 (.txt)</span>
          </div>
        </div>
      </div>

      {/* 파일 거부 에러 */}
      {fileRejections.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-red-800 mb-2">
            파일 업로드 오류
          </h4>
          {fileRejections.map(({ file, errors }) => (
            <div key={file.name} className="text-sm text-red-700">
              <p className="font-medium">{file.name}</p>
              {errors.map((error) => (
                <p key={error.code} className="text-xs">
                  • {error.code === 'file-too-large' 
                    ? `파일 크기가 너무 큽니다 (최대 ${formatFileSize(maxFileSize)})`
                    : error.code === 'file-invalid-type'
                    ? '지원하지 않는 파일 형식입니다'
                    : error.message}
                </p>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default FileUpload;

