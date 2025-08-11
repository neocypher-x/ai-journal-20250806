import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Sparkles } from "lucide-react";
import { ReflectionRequest } from "@/types/api";

interface JournalFormProps {
  onSubmit: (request: ReflectionRequest) => Promise<void>;
  isLoading: boolean;
}

export function JournalForm({ onSubmit, isLoading }: JournalFormProps) {
  const [text, setText] = useState("");
  const [enableScout, setEnableScout] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    await onSubmit({
      journal_entry: { text: text.trim() },
      enable_scout: enableScout,
    });
  };

  const wordCount = text
    .trim()
    .split(/\s+/)
    .filter((word) => word.length > 0).length;
  const isValidLength = wordCount >= 1 && wordCount <= 1000;

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="gradient-card border border-border/50 rounded-lg shadow-lg overflow-hidden">
        <div className="p-8">
          <div className="mb-6">
            <h1 className="text-3xl font-light text-foreground mb-2 text-balance">
              Philosophical Journal
            </h1>
            <p className="text-muted-foreground text-balance leading-relaxed">
              Share your thoughts, struggles, or reflections. Receive insights
              from Buddhist, Stoic, and Existentialist perspectives to
              illuminate new paths forward.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-3">
              <label
                htmlFor="journal-text"
                className="block text-sm font-medium text-foreground"
              >
                Your Journal Entry
              </label>
              <Textarea
                id="journal-text"
                placeholder="I keep saying yes to work I don't want to do..."
                value={text}
                onChange={(e) => setText(e.target.value)}
                className="min-h-[200px] text-base leading-relaxed resize-none border-border/60 focus:border-border transition-colors duration-200"
                disabled={isLoading}
              />
              <div className="flex items-center justify-between text-sm">
                <span
                  className={`transition-colors duration-200 ${
                    isValidLength
                      ? "text-muted-foreground"
                      : wordCount < 1
                      ? "text-amber-600"
                      : "text-red-600"
                  }`}
                >
                  {wordCount} words{" "}
                  {!isValidLength && wordCount > 0 && (
                    <span className="ml-1">
                      {wordCount < 1 ? `(minimum 1)` : `(maximum 1000)`}
                    </span>
                  )}
                </span>
                {isValidLength && (
                  <span className="text-emerald-600 text-xs font-medium">
                    Ready for reflection
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="enable-scout"
                checked={enableScout}
                onChange={(e) => setEnableScout(e.target.checked)}
                className="rounded border-border/60 text-primary focus:ring-primary/20 focus:ring-2 transition-colors duration-200"
                disabled={isLoading}
              />
              <label
                htmlFor="enable-scout"
                className="text-sm text-foreground select-none"
              >
                Enable Philosophy Scout
                <span className="block text-muted-foreground text-xs mt-1">
                  Discover additional philosophical schools that might offer
                  relevant insights
                </span>
              </label>
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                disabled={!isValidLength || isLoading}
                size="lg"
                className="w-full sm:w-auto min-w-[160px] font-medium transition-all duration-200 hover:shadow-md"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Reflecting...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Get Reflection
                  </>
                )}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
