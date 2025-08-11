import { Perspectives } from '@/types/api';
import { formatFrameworkName, getFrameworkColor } from '@/lib/utils';
import { Lightbulb, AlertTriangle, Target, Quote } from 'lucide-react';

interface PerspectivesTableProps {
  perspectives: Perspectives;
}

export function PerspectivesTable({ perspectives }: PerspectivesTableProps) {
  return (
    <div className="w-full overflow-x-auto">
      <table className="w-full border-collapse min-w-[800px] overflow-hidden">
        <thead className="gradient-header">
          <tr>
            <th className="w-[180px] text-left align-top p-4 font-medium text-foreground sticky left-0 bg-gradient-to-r from-blue-50/60 to-cyan-50/70 backdrop-blur-sm">
              Aspect
            </th>
            {perspectives.items.map((perspective, index) => {
              const frameworkName = formatFrameworkName(perspective.framework, perspective.other_framework_name);
              const colorClass = getFrameworkColor(perspective.framework);
              
              return (
                <th key={index} className="text-left align-top p-4 min-w-[260px]">
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${colorClass}`}>
                    {frameworkName}
                  </div>
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {/* Core Principle Row */}
          <tr className="border-t border-border/20">
            <td className="p-4 align-top font-medium text-sm text-foreground sticky left-0 bg-gradient-to-r from-blue-50/40 to-cyan-50/50 backdrop-blur-sm">
              <div className="flex items-start space-x-2">
                <Lightbulb className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                <span>Core Principle</span>
              </div>
            </td>
            {perspectives.items.map((perspective, index) => (
              <td key={index} className="p-4 align-top text-sm text-muted-foreground leading-relaxed bg-gradient-to-br from-white/60 to-blue-50/40 backdrop-blur-sm">
                {perspective.core_principle_invoked}
              </td>
            ))}
          </tr>

          {/* Challenge Row */}
          <tr className="border-t border-border/20">
            <td className="p-4 align-top font-medium text-sm text-foreground sticky left-0 bg-gradient-to-r from-blue-50/40 to-cyan-50/50 backdrop-blur-sm">
              <div className="flex items-start space-x-2">
                <Target className="h-4 w-4 text-red-600 mt-0.5 flex-shrink-0" />
                <span>Challenge</span>
              </div>
            </td>
            {perspectives.items.map((perspective, index) => (
              <td key={index} className="p-4 align-top text-sm text-muted-foreground leading-relaxed font-medium bg-gradient-to-br from-white/60 to-green-50/40 backdrop-blur-sm">
                "{perspective.challenge_framing}"
              </td>
            ))}
          </tr>

          {/* Practical Experiment Row */}
          <tr className="border-t border-border/20">
            <td className="p-4 align-top font-medium text-sm text-foreground sticky left-0 bg-gradient-to-r from-blue-50/40 to-cyan-50/50 backdrop-blur-sm">
              <div className="flex items-start space-x-2">
                <div className="h-4 w-4 bg-blue-600 rounded-full mt-1 flex-shrink-0" />
                <span>Practical Experiment</span>
              </div>
            </td>
            {perspectives.items.map((perspective, index) => (
              <td key={index} className="p-4 align-top text-sm text-muted-foreground leading-relaxed bg-gradient-to-br from-white/60 to-cyan-50/40 backdrop-blur-sm">
                {perspective.practical_experiment}
              </td>
            ))}
          </tr>

          {/* Potential Trap Row */}
          <tr className="border-t border-border/20">
            <td className="p-4 align-top font-medium text-sm text-foreground sticky left-0 bg-gradient-to-r from-blue-50/40 to-cyan-50/50 backdrop-blur-sm">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-4 w-4 text-orange-600 mt-0.5 flex-shrink-0" />
                <span>Potential Trap</span>
              </div>
            </td>
            {perspectives.items.map((perspective, index) => (
              <td key={index} className="p-4 align-top text-sm text-muted-foreground leading-relaxed bg-gradient-to-br from-white/60 to-orange-50/40 backdrop-blur-sm">
                {perspective.potential_trap}
              </td>
            ))}
          </tr>

          {/* Key Metaphor Row */}
          <tr className="border-t border-border/20">
            <td className="p-4 align-top font-medium text-sm text-foreground sticky left-0 bg-gradient-to-r from-blue-50/40 to-cyan-50/50 backdrop-blur-sm">
              <div className="flex items-start space-x-2">
                <Quote className="h-4 w-4 text-purple-600 mt-0.5 flex-shrink-0" />
                <span>Key Metaphor</span>
              </div>
            </td>
            {perspectives.items.map((perspective, index) => (
              <td key={index} className="p-4 align-top text-sm text-muted-foreground leading-relaxed italic bg-gradient-to-br from-white/60 to-purple-50/40 backdrop-blur-sm">
                {perspective.key_metaphor}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}