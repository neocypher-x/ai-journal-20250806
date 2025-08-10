import { Prophecy } from '@/types/api';
import { formatFrameworkName } from '@/lib/utils';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Scale, Zap, Lightbulb, Minus } from 'lucide-react';

interface ProphecySectionProps {
  prophecy: Prophecy;
}

function getStanceColor(stance: string): string {
  switch (stance.toLowerCase()) {
    case 'agree':
      return 'text-emerald-700 bg-emerald-50 border-emerald-200';
    case 'disagree':
      return 'text-red-700 bg-red-50 border-red-200';
    case 'nuanced':
      return 'text-amber-700 bg-amber-50 border-amber-200';
    default:
      return 'text-slate-700 bg-slate-50 border-slate-200';
  }
}

export function ProphecySection({ prophecy }: ProphecySectionProps) {
  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="gradient-card border border-border/40 rounded-lg shadow-sm overflow-hidden">
        <div className="p-8">
          <div className="mb-6">
            <h2 className="text-2xl font-light text-foreground mb-2">Oracle's Prophecy</h2>
            <p className="text-muted-foreground">
              Cross-philosophical analysis revealing agreements, tensions, and synthesis
            </p>
          </div>

          <Accordion type="multiple" defaultValue={["synthesis"]} className="w-full">
            <AccordionItem value="synthesis">
              <AccordionTrigger className="text-left hover:no-underline">
                <div className="flex items-center space-x-2">
                  <Lightbulb className="h-4 w-4 text-purple-600" />
                  <span className="font-medium">Synthesis</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="pt-2">
                  <div className="prose prose-sm max-w-none text-muted-foreground leading-relaxed">
                    {prophecy.synthesis.split('\n\n').map((paragraph, index) => (
                      <p key={index} className="mb-4 last:mb-0">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="agreements">
              <AccordionTrigger className="text-left hover:no-underline">
                <div className="flex items-center space-x-2">
                  <Scale className="h-4 w-4 text-blue-600" />
                  <span className="font-medium">Agreement Scorecard</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="pt-2 space-y-4">
                  {prophecy.agreement_scorecard.map((agreement, index) => (
                    <div key={index} className="border border-border/30 rounded-md p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="text-sm font-medium text-foreground">
                          {formatFrameworkName(agreement.framework_a)} & {formatFrameworkName(agreement.framework_b)}
                        </div>
                        <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getStanceColor(agreement.stance)}`}>
                          {agreement.stance.toUpperCase()}
                        </div>
                      </div>
                      {agreement.notes && (
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          {agreement.notes}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            <AccordionItem value="tensions">
              <AccordionTrigger className="text-left hover:no-underline">
                <div className="flex items-center space-x-2">
                  <Zap className="h-4 w-4 text-orange-600" />
                  <span className="font-medium">Tension Analysis</span>
                </div>
              </AccordionTrigger>
              <AccordionContent>
                <div className="pt-2 space-y-4">
                  {prophecy.tension_summary.map((tension, index) => (
                    <div key={index} className="border border-border/30 rounded-md p-4">
                      <div className="mb-3">
                        <div className="flex items-center space-x-2 mb-2">
                          <span className="text-sm font-medium text-foreground">Frameworks:</span>
                          <div className="flex flex-wrap gap-1">
                            {tension.frameworks.map((framework, fIndex) => (
                              <span key={fIndex} className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded">
                                {formatFrameworkName(framework)}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                      <div className="prose prose-sm max-w-none text-muted-foreground leading-relaxed">
                        {tension.explanation.split('\n\n').map((paragraph, pIndex) => (
                          <p key={pIndex} className="mb-3 last:mb-0">
                            {paragraph}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </AccordionContent>
            </AccordionItem>

            {prophecy.what_is_lost_by_blending && prophecy.what_is_lost_by_blending.length > 0 && (
              <AccordionItem value="lost">
                <AccordionTrigger className="text-left hover:no-underline">
                  <div className="flex items-center space-x-2">
                    <Minus className="h-4 w-4 text-red-600" />
                    <span className="font-medium">What Is Lost by Blending</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="pt-2">
                    <div className="prose prose-sm max-w-none text-muted-foreground leading-relaxed">
                      {prophecy.what_is_lost_by_blending.map((item, index) => (
                        <p key={index} className="mb-3 last:mb-0">
                          {item}
                        </p>
                      ))}
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            )}
          </Accordion>
        </div>
      </div>
    </div>
  );
}