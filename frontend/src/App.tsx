import { useState } from 'react';
import { JournalForm } from './components/JournalForm';
import { ReflectionDisplay } from './components/ReflectionDisplay';
import { generateReflection, ApiError } from './lib/api';
import { ReflectionRequest, ReflectionResponse } from './types/api';
import { AlertTriangle } from 'lucide-react';

export default function App() {
  const [reflection, setReflection] = useState<ReflectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mockMode, setMockMode] = useState(() => {
    // Check URL params or localStorage for dev mode
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('mock') === 'true' || localStorage.getItem('ai-journal-mock') === 'true';
  });

  const handleSubmit = async (request: ReflectionRequest) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await generateReflection(request, mockMode);
      setReflection(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Failed to generate reflection: ${err.message}`);
      } else {
        setError('An unexpected error occurred. Please try again.');
      }
      console.error('Error generating reflection:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMockMode = () => {
    const newMockMode = !mockMode;
    setMockMode(newMockMode);
    localStorage.setItem('ai-journal-mock', newMockMode.toString());
    // Update URL without reload
    const url = new URL(window.location.href);
    if (newMockMode) {
      url.searchParams.set('mock', 'true');
    } else {
      url.searchParams.delete('mock');
    }
    window.history.replaceState({}, '', url.toString());
  };

  const handleNewReflection = () => {
    setReflection(null);
    setError(null);
  };

  return (
    <div className="min-h-screen gradient-vivid">
      <div className="container mx-auto px-4 py-8">
        {/* Developer Mode Toggle */}
        <div className="fixed top-4 right-4 z-50">
          <button
            onClick={toggleMockMode}
            className={`px-3 py-1 text-xs font-mono rounded-full transition-colors ${
              mockMode 
                ? 'bg-amber-100 text-amber-800 border border-amber-300' 
                : 'bg-gray-100 text-gray-600 border border-gray-300'
            }`}
            title={mockMode ? 'Using mock data' : 'Using real AI'}
          >
            {mockMode ? '🎭 MOCK' : '🤖 LIVE'}
          </button>
        </div>

        {error && (
          <div className="w-full max-w-4xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {!reflection ? (
          <JournalForm onSubmit={handleSubmit} isLoading={isLoading} />
        ) : (
          <ReflectionDisplay 
            reflection={reflection.reflection} 
            onNewReflection={handleNewReflection}
          />
        )}
      </div>
    </div>
  );
}