"""
Deterministic response composer for merging agent outputs.
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from collections import Counter

from .models import (
    IngestResult, AgentInsight, PromptItem, ReflectResponse, 
    AgentCallResult, ProcessingContext, PhilosophySource
)
from .config import settings


class ResponseComposer:
    """Deterministic composer for merging agent outputs into final response."""
    
    def __init__(self):
        self.logger = logging.getLogger("ai_journal.composer")
    
    def compose(self, context: ProcessingContext) -> ReflectResponse:
        """Compose final response from agent results."""
        
        if not context.ingest_result:
            raise ValueError("Cannot compose response without ingest result")
        
        # Extract successful agent results
        successful_results = [
            result for result in context.agent_results 
            if result.success and result.result
        ]
        
        if not successful_results:
            raise ValueError("No successful agent results to compose")
        
        # Collect all prompt suggestions with metadata
        all_prompts = self._collect_prompts(successful_results)
        
        # Deduplicate prompts
        unique_prompts = self._deduplicate_prompts(all_prompts)
        
        # Prioritize and balance prompts
        final_prompts = self._prioritize_prompts(
            unique_prompts, 
            context.ingest_result.themes,
            context.ingest_result.mood
        )
        
        # Generate advice
        advice = self._generate_advice(
            successful_results, 
            context.ingest_result,
            context.request.question
        )
        
        # Calculate dedupe rate for metrics
        dedupe_rate = 1.0 - (len(unique_prompts) / len(all_prompts)) if all_prompts else 0.0
        
        self.logger.info(
            f"Composer results: {len(all_prompts)} -> {len(unique_prompts)} -> "
            f"{len(final_prompts)} prompts (dedupe_rate: {dedupe_rate:.2f})"
        )
        
        return ReflectResponse(
            summary=context.ingest_result.summary,
            themes=context.ingest_result.themes,
            mood=context.ingest_result.mood,
            prompts=final_prompts,
            advice=advice,
            warnings=context.warnings if context.warnings else None,
            trace_id=context.trace_id
        )
    
    def _collect_prompts(self, agent_results: List[AgentCallResult]) -> List[Tuple[str, PhilosophySource, str]]:
        """Collect all prompt suggestions with their sources."""
        all_prompts = []
        
        source_mapping = {
            'buddhist_coach': 'buddhist',
            'stoic_coach': 'stoic', 
            'existential_coach': 'existential'
        }
        
        for result in agent_results:
            if result.agent_name not in source_mapping:
                continue
                
            source = source_mapping[result.agent_name]
            agent_data = result.result
            
            if 'prompt_suggestions' not in agent_data:
                continue
            
            # Get insights for generating rationales
            insights = agent_data.get('insights', [])
            
            for i, prompt in enumerate(agent_data['prompt_suggestions']):
                # Generate rationale from corresponding insight or create generic one
                if i < len(insights):
                    rationale = insights[i][:200]  # Truncate if too long
                else:
                    rationale = f"Relevant to {source} principles and current state"
                
                all_prompts.append((prompt, source, rationale))
        
        return all_prompts
    
    def _deduplicate_prompts(self, prompts: List[Tuple[str, PhilosophySource, str]]) -> List[Tuple[str, PhilosophySource, str]]:
        """Remove duplicate prompts using Jaccard similarity."""
        if not prompts:
            return []
        
        unique_prompts = []
        seen_tokens = []
        
        for prompt_text, source, rationale in prompts:
            # Normalize prompt text
            normalized = self._normalize_text(prompt_text)
            tokens = set(normalized.split())
            
            # Check against existing prompts
            is_duplicate = False
            for existing_tokens in seen_tokens:
                similarity = self._jaccard_similarity(tokens, existing_tokens)
                if similarity >= 0.7:  # 70% similarity threshold
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_prompts.append((prompt_text, source, rationale))
                seen_tokens.append(tokens)
            else:
                self.logger.debug(f"Removed duplicate prompt: {prompt_text[:50]}...")
        
        return unique_prompts
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation except spaces
        text = re.sub(r'[^\w\s]', '', text)
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity between two token sets."""
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _prioritize_prompts(self, prompts: List[Tuple[str, PhilosophySource, str]], 
                           themes: List[str], mood: str) -> List[PromptItem]:
        """Prioritize and balance prompts based on relevance and diversity."""
        
        if not prompts:
            return []
        
        # Score each prompt
        scored_prompts = []
        theme_words = set(word.lower() for theme in themes for word in theme.split())
        
        for prompt_text, source, rationale in prompts:
            score = self._calculate_prompt_score(prompt_text, theme_words, mood)
            scored_prompts.append((score, prompt_text, source, rationale))
        
        # Sort by score (descending)
        scored_prompts.sort(reverse=True, key=lambda x: x[0])
        
        # Apply diversity constraints and limits
        final_prompts = []
        source_counts = Counter()
        
        for score, prompt_text, source, rationale in scored_prompts:
            # Enforce max 2 prompts per source
            if source_counts[source] >= 2:
                continue
            
            # Enforce global max prompts limit
            if len(final_prompts) >= settings.MAX_PROMPTS:
                break
            
            final_prompts.append(PromptItem(
                text=prompt_text.strip(),
                source=source,
                rationale=rationale.strip()
            ))
            source_counts[source] += 1
        
        # Ensure we have at least one prompt if any were provided
        if not final_prompts and prompts:
            # Take the highest scored prompt regardless of constraints
            _, prompt_text, source, rationale = scored_prompts[0]
            final_prompts.append(PromptItem(
                text=prompt_text.strip(),
                source=source,
                rationale=rationale.strip()
            ))
        
        return final_prompts
    
    def _calculate_prompt_score(self, prompt: str, theme_words: Set[str], mood: str) -> float:
        """Calculate relevance score for a prompt."""
        score = 0.0
        prompt_lower = prompt.lower()
        prompt_words = set(prompt_lower.split())
        
        # Theme overlap bonus (primary factor)
        theme_overlap = len(prompt_words.intersection(theme_words))
        score += theme_overlap * 2.0
        
        # Mood alignment bonus
        mood_keywords = {
            'stressed': ['stress', 'pressure', 'overwhelm', 'calm', 'peace'],
            'tense': ['tension', 'anxiety', 'relax', 'breathe'],
            'sad': ['sadness', 'grief', 'comfort', 'healing'],
            'angry': ['anger', 'frustration', 'patience', 'forgiveness'],
            'energized': ['energy', 'motivation', 'action', 'momentum'],
            'calm': ['peace', 'tranquility', 'mindfulness', 'presence'],
            'mixed': ['balance', 'complexity', 'nuance', 'integration']
        }
        
        if mood in mood_keywords:
            mood_overlap = len(prompt_words.intersection(set(mood_keywords[mood])))
            score += mood_overlap * 1.0
        
        # Actionability bonus (starts with action words)
        action_words = [
            'consider', 'reflect', 'ask', 'examine', 'explore', 'practice',
            'try', 'notice', 'observe', 'think', 'contemplate', 'meditate',
            'write', 'journal', 'identify', 'focus', 'breathe', 'accept'
        ]
        
        first_word = prompt_lower.split()[0] if prompt_lower.split() else ''
        if first_word in action_words:
            score += 1.0
        
        # Length penalty for very long prompts (prefer concise)
        if len(prompt) > 200:
            score -= 0.5
        
        return score
    
    def _generate_advice(self, agent_results: List[AgentCallResult], 
                        ingest_result: IngestResult, question: str = None) -> str:
        """Generate concrete advice from agent insights."""
        
        # Collect all insights
        all_insights = []
        for result in agent_results:
            if 'insights' in result.result:
                all_insights.extend(result.result['insights'])
        
        if not all_insights:
            return "Take time to reflect on your journal entry and consider what it reveals about your current state and aspirations."
        
        # Start with question response if provided
        advice_parts = []
        
        if question:
            # Try to find insights that seem to address the question
            question_words = set(question.lower().split())
            relevant_insights = []
            
            for insight in all_insights:
                insight_words = set(insight.lower().split())
                overlap = len(question_words.intersection(insight_words))
                if overlap > 0:
                    relevant_insights.append((overlap, insight))
            
            if relevant_insights:
                relevant_insights.sort(reverse=True, key=lambda x: x[0])
                advice_parts.append(f"Regarding your question: {relevant_insights[0][1]}")
        
        # Add 1-2 key insights
        selected_insights = all_insights[:2] if len(all_insights) >= 2 else all_insights
        for insight in selected_insights:
            if len(advice_parts) < 2:  # Limit to keep under word count
                advice_parts.append(insight)
        
        # Add a concrete action step
        concrete_actions = [
            "Set aside 10 minutes today to sit quietly and reflect on these insights.",
            "Write down three specific actions you could take based on these reflections.",
            "Practice mindful breathing when you notice the emotions described in your journal.",
            "Consider discussing these thoughts with someone you trust.",
            "Take a short walk while contemplating these themes."
        ]
        
        # Choose action based on mood
        mood_actions = {
            'stressed': "Practice a brief breathing exercise to center yourself before reflecting further.",
            'tense': "Try gentle stretching or movement while considering these insights.", 
            'sad': "Be gentle with yourself as you process these reflections.",
            'angry': "Take several deep breaths before engaging with these thoughts.",
            'energized': "Channel this energy into concrete action steps based on your reflections.",
            'calm': "Use this peaceful state to deeply contemplate these insights.",
            'mixed': "Take time to sit with the complexity of your current experience."
        }
        
        if ingest_result.mood in mood_actions:
            advice_parts.append(mood_actions[ingest_result.mood])
        else:
            advice_parts.append(concrete_actions[0])  # Default action
        
        # Join and ensure we stay within word limit (~120 words)
        advice = " ".join(advice_parts)
        
        # Truncate if too long (rough word count)
        words = advice.split()
        if len(words) > 120:
            advice = " ".join(words[:120]) + "..."
        
        return advice