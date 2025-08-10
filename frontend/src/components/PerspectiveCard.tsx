import { Perspective } from '@/types/api';
import { formatFrameworkName, getFrameworkColor } from '@/lib/utils';
import { Separator } from '@/components/ui/separator';
import { Lightbulb, AlertTriangle, Target, Quote } from 'lucide-react';

interface PerspectiveCardProps {
  perspective: Perspective;
}

export function PerspectiveCard({ perspective }: PerspectiveCardProps) {
  const frameworkName = formatFrameworkName(perspective.framework, perspective.other_framework_name);
  const colorClass = getFrameworkColor(perspective.framework);

  return (
    <div className="gradient-card border border-border/40 rounded-lg shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden">
      <div className="p-6">
        <div className="mb-4">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${colorClass}`}>
            {frameworkName}
          </div>
        </div>

        <div className="space-y-5">
          <div>
            <div className="flex items-start space-x-2 mb-2">
              <Lightbulb className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
              <h4 className="text-sm font-medium text-foreground">Core Principle</h4>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed pl-6">
              {perspective.core_principle_invoked}
            </p>
          </div>

          <Separator />

          <div>
            <div className="flex items-start space-x-2 mb-2">
              <Target className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
              <h4 className="text-sm font-medium text-foreground">Challenge</h4>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed pl-6 font-medium">
              "{perspective.challenge_framing}"
            </p>
          </div>

          <div>
            <div className="flex items-start space-x-2 mb-2">
              <div className="h-4 w-4 bg-blue-600 rounded-full mt-1 flex-shrink-0" />
              <h4 className="text-sm font-medium text-foreground">Practical Experiment</h4>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed pl-6">
              {perspective.practical_experiment}
            </p>
          </div>

          <div>
            <div className="flex items-start space-x-2 mb-2">
              <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
              <h4 className="text-sm font-medium text-foreground">Potential Trap</h4>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed pl-6">
              {perspective.potential_trap}
            </p>
          </div>

          <Separator />

          <div>
            <div className="flex items-start space-x-2 mb-2">
              <Quote className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
              <h4 className="text-sm font-medium text-foreground">Key Metaphor</h4>
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed pl-6 italic">
              {perspective.key_metaphor}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}