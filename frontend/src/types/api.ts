export interface JournalEntry {
  text: string;
}

export interface ReflectionRequest {
  journal_entry: JournalEntry;
  enable_scout: boolean;
}

export interface Perspective {
  framework: string;
  other_framework_name: string | null;
  core_principle_invoked: string;
  challenge_framing: string;
  practical_experiment: string;
  potential_trap: string;
  key_metaphor: string;
}

export interface Perspectives {
  items: Perspective[];
}

export interface Agreement {
  framework_a: string;
  framework_b: string;
  stance: string;
  notes: string;
}

export interface Tension {
  frameworks: string[];
  explanation: string;
}

export interface Prophecy {
  agreement_scorecard: Agreement[];
  tension_summary: Tension[];
  synthesis: string;
  what_is_lost_by_blending: string[];
}

export interface Reflection {
  journal_entry: JournalEntry;
  perspectives: Perspectives;
  prophecy: Prophecy;
}

export interface ReflectionResponse {
  reflection: Reflection;
}