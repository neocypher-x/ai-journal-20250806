import { Reflection } from '@/types/api';
import { PerspectivesTable } from './PerspectivesTable';
import { ProphecySection } from './ProphecySection';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { RotateCcw, BookOpen } from 'lucide-react';

interface ReflectionDisplayProps {
  reflection: Reflection;
  onNewReflection: () => void;
}

export function ReflectionDisplay({ reflection, onNewReflection }: ReflectionDisplayProps) {
  return (
    <div className="w-full space-y-8 animate-fade-in">
      <div className="w-full max-w-4xl mx-auto">
        <div className="gradient-card border border-border/40 rounded-lg shadow-sm overflow-hidden">
          <div className="p-8">
            <div className="mb-6">
              <h2 className="text-2xl font-light text-foreground mb-2">Your Journal Entry</h2>
            </div>
            <div className="prose prose-lg max-w-none">
              <blockquote className="border-l-4 border-primary/20 pl-6 italic text-muted-foreground leading-relaxed">
                {reflection.journal_entry.text}
              </blockquote>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full max-w-7xl mx-auto">
        <div className="mb-8">
          <h2 className="text-2xl font-light text-foreground mb-2 text-center">Philosophical Perspectives</h2>
          <p className="text-muted-foreground text-center">
            Wisdom from different traditions to illuminate your reflection
          </p>
        </div>
        
        <div className="gradient-card border border-border/40 rounded-lg shadow-sm overflow-hidden">
          <PerspectivesTable perspectives={reflection.perspectives} />
        </div>
      </div>

      <div className="w-full">
        <ProphecySection prophecy={reflection.prophecy} />
      </div>

      <div className="w-full max-w-4xl mx-auto">
        <Separator className="my-8" />
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button
            onClick={onNewReflection}
            variant="outline"
            size="lg"
            className="min-w-[180px] font-medium transition-all duration-200"
          >
            <RotateCcw className="mr-2 h-4 w-4" />
            New Reflection
          </Button>
          <div className="flex items-center text-sm text-muted-foreground">
            <BookOpen className="mr-2 h-4 w-4" />
            <span>Reflect on your insights and explore new thoughts</span>
          </div>
        </div>
      </div>
    </div>
  );
}