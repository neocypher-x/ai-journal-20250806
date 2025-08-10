import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFrameworkName(framework: string, otherName?: string | null): string {
  if (framework === "other" && otherName) {
    return otherName;
  }
  
  return framework.charAt(0).toUpperCase() + framework.slice(1);
}

export function getFrameworkColor(framework: string): string {
  const colors: Record<string, string> = {
    buddhism: "text-amber-700 bg-amber-50 border-amber-200",
    stoicism: "text-stone-700 bg-stone-50 border-stone-200", 
    existentialism: "text-indigo-700 bg-indigo-50 border-indigo-200",
    other: "text-slate-700 bg-slate-50 border-slate-200"
  };
  
  return colors[framework.toLowerCase()] || colors.other;
}