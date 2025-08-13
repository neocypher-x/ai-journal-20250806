"""
Excavation engine for interactive hypothesis testing.
"""

import logging
import math
import re
from typing import List, Tuple, Optional, Dict, Any
from uuid import UUID
from openai import AsyncOpenAI

from ai_journal.config import Settings
from ai_journal.models import (
    JournalEntry, CruxHypothesis, Probe, ProbeTurn, ExcavationState,
    ExcavationResult, ConfirmedCrux, SecondaryTheme, ExcavationSummary,
    DiscardedHypothesisLogItem
)

logger = logging.getLogger(__name__)


class ExcavationEngine:
    """
    Handles the interactive excavation loop for hypothesis testing.
    """
    
    def __init__(self, openai_client: AsyncOpenAI, settings: Settings):
        self.client = openai_client
        self.settings = settings
    
    async def seed_hypotheses(self, journal_entry: JournalEntry) -> List[CruxHypothesis]:
        """
        Extract 2-4 concise candidate hypotheses from the journal entry.
        """
        logger.info("Seeding initial hypotheses from journal entry")
        
        prompt = f"""
        Analyze this journal entry and identify 2-4 concise candidate root issues (crux hypotheses).
        Focus on salience cues like goals/obstacles, affect intensity, and recurring themes.
        
        Each hypothesis should be:
        - 1-2 sentences max
        - A potential root psychological or emotional issue
        - Distinct from the others
        - Testable through questions
        
        Journal Entry:
        {journal_entry.text}
        
        Format your response as a numbered list:
        1. [hypothesis]
        2. [hypothesis]
        ...
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=800
            )
            
            content = response.choices[0].message.content or ""
            hypotheses = self._parse_hypotheses(content)
            
            logger.info(f"Generated {len(hypotheses)} initial hypotheses")
            return hypotheses
            
        except Exception as e:
            logger.error(f"Failed to seed hypotheses: {e}")
            # Fallback to basic parsing if AI fails
            return self._fallback_hypotheses(journal_entry)
    
    def _parse_hypotheses(self, content: str) -> List[CruxHypothesis]:
        """Parse hypotheses from AI response."""
        hypotheses = []
        lines = content.strip().split('\n')
        
        for line in lines:
            # Match numbered list items
            match = re.match(r'^\d+\.\s*(.+)$', line.strip())
            if match:
                text = match.group(1).strip()
                if text and len(text) <= 400:
                    hypothesis = CruxHypothesis(
                        text=text,
                        confidence=0.4 + (len(hypotheses) * 0.02),  # slight variation
                        confirmations=0,
                        status="active"
                    )
                    hypotheses.append(hypothesis)
        
        # Ensure we have at least 2 hypotheses
        if len(hypotheses) < 2:
            hypotheses.extend(self._fallback_hypotheses_items(max_count=4-len(hypotheses)))
        
        return hypotheses[:4]  # Cap at max_hypotheses
    
    def _fallback_hypotheses(self, journal_entry: JournalEntry) -> List[CruxHypothesis]:
        """Generate fallback hypotheses if AI fails."""
        return self._fallback_hypotheses_items()
    
    def _fallback_hypotheses_items(self, max_count: int = 2) -> List[CruxHypothesis]:
        """Basic fallback hypothesis items."""
        fallbacks = [
            "There may be an underlying fear or anxiety driving the situation",
            "This could relate to unmet expectations or goals",
            "There might be a pattern of avoidance or resistance at play",
            "This situation may reflect deeper values or identity conflicts"
        ]
        
        hypotheses = []
        for i, text in enumerate(fallbacks[:max_count]):
            hypothesis = CruxHypothesis(
                text=text,
                confidence=0.35 + (i * 0.05),
                confirmations=0,
                status="active"
            )
            hypotheses.append(hypothesis)
        
        return hypotheses
    
    async def plan_next_probe(self, state: ExcavationState) -> Probe:
        """
        Generate a contrastive question that maximally distinguishes hypotheses.
        """
        logger.info("Planning next probe")
        
        active_hypotheses = [h for h in state.hypotheses if h.status == "active"]
        if not active_hypotheses:
            raise ValueError("No active hypotheses to probe")
        
        # Sort by confidence and take top 2 for contrast
        sorted_hyp = sorted(active_hypotheses, key=lambda h: h.confidence, reverse=True)
        targets = sorted_hyp[:2] if len(sorted_hyp) >= 2 else sorted_hyp[:1]
        
        # Build context from previous probes
        previous_questions = [turn.probe.question for turn in state.probes_log]
        
        prompt = f"""
        Generate a contrastive Socratic question to distinguish between these hypotheses about the journal entry.
        
        Journal Entry (excerpt): {state.journal_entry.text[:300]}...
        
        Target Hypotheses:
        {chr(10).join(f"- {h.text}" for h in targets)}
        
        Previous Questions Asked:
        {chr(10).join(f"- {q}" for q in previous_questions[-3:]) if previous_questions else "None"}
        
        Create a question that:
        - Helps distinguish between these specific hypotheses
        - Is Socratic (probing, not leading)
        - Avoids repeating previous questions
        - Elicits specific evidence or reflection
        
        Question:
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=2000
            )
            
            question = (response.choices[0].message.content or "").strip()
            if not question:
                question = self._fallback_question(targets, state)
            
            probe = Probe(
                question=question,
                targets=[h.hypothesis_id for h in targets]
            )
            
            logger.info(f"Generated probe targeting {len(targets)} hypotheses")
            return probe
            
        except Exception as e:
            logger.error(f"Failed to generate probe: {e}")
            return Probe(
                question=self._fallback_question(targets, state),
                targets=[h.hypothesis_id for h in targets]
            )
    
    def _fallback_question(self, targets: List[CruxHypothesis], state: ExcavationState) -> str:
        """Generate a fallback question if AI fails."""
        previous_questions = [turn.probe.question for turn in state.probes_log]
        
        # Different fallback questions to avoid repetition
        fallback_options = [
            "Can you tell me more about what specifically makes this situation difficult for you?",
            "What emotions or feelings come up most strongly when you think about this?",
            "When did you first notice this pattern or issue starting?",
            "What would happen if you tried to change this situation?",
            "How do you think others might view this situation differently than you do?",
            "What aspects of this feel most urgent or pressing to address?"
        ]
        
        # Find first option not already used
        for option in fallback_options:
            if option not in previous_questions:
                return option
        
        # If all used, return a generic one with variation
        return f"What other aspects of this situation feel important to explore?"
    
    async def update_beliefs(self, state: ExcavationState, user_reply: str) -> List[CruxHypothesis]:
        """
        Update hypothesis confidence scores based on user's reply.
        """
        logger.info("Updating beliefs based on user reply")
        
        if not state.last_probe:
            raise ValueError("No probe to analyze reply against")
        
        active_hypotheses = [h for h in state.hypotheses if h.status == "active"]
        
        prompt = f"""
        Analyze this user reply in the context of the probe question and hypotheses.
        Score each hypothesis from 0.0 to 1.0 based on how well the reply supports it.
        
        Probe Question: {state.last_probe.question}
        
        User Reply: {user_reply}
        
        Hypotheses to score:
        {chr(10).join(f"{i+1}. {h.text} (current confidence: {h.confidence:.2f})" for i, h in enumerate(active_hypotheses))}
        
        For each hypothesis, provide:
        - New confidence score (0.0-1.0)
        - Whether this reply provides strong confirmation (+1 confirmation)
        - Brief reasoning
        
        Format:
        1. Score: 0.XX, Confirmation: Yes/No, Reason: [brief]
        2. Score: 0.XX, Confirmation: Yes/No, Reason: [brief]
        ...
        """
        
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=5000
            )
            
            content = response.choices[0].message.content or ""
            updated_hypotheses = self._parse_belief_updates(content, active_hypotheses, user_reply)
            
            logger.info(f"Updated beliefs for {len(updated_hypotheses)} hypotheses")
            return updated_hypotheses
            
        except Exception as e:
            logger.error(f"Failed to update beliefs: {e}")
            return self._fallback_belief_update(active_hypotheses, user_reply)
    
    def _parse_belief_updates(self, content: str, hypotheses: List[CruxHypothesis], user_reply: str) -> List[CruxHypothesis]:
        """Parse belief updates from AI response."""
        lines = content.strip().split('\n')
        updated = []
        
        for i, hypothesis in enumerate(hypotheses):
            # Create copy for update
            new_hyp = hypothesis.model_copy()
            
            # Look for corresponding line
            pattern = rf"^{i+1}\.\s*Score:\s*([\d.]+).*Confirmation:\s*(Yes|No)"
            for line in lines:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        new_confidence = float(match.group(1))
                        new_confidence = max(0.0, min(1.0, new_confidence))  # clamp
                        new_hyp.confidence = new_confidence
                        
                        if match.group(2).lower() == 'yes':
                            new_hyp.confirmations += 1
                        
                        # Check if should be discarded (very low confidence for multiple turns)
                        if new_confidence < 0.15 and new_hyp.confirmations == 0:
                            new_hyp.status = "discarded"
                            new_hyp.discard_reason = "Low confidence after user feedback"
                        
                    except ValueError:
                        pass  # Keep original values
                    break
            
            updated.append(new_hyp)
        
        return updated
    
    def _fallback_belief_update(self, hypotheses: List[CruxHypothesis], user_reply: str) -> List[CruxHypothesis]:
        """Simple fallback belief update."""
        # Basic sentiment analysis on reply length and keywords
        reply_lower = user_reply.lower()
        positive_keywords = ['yes', 'exactly', 'definitely', 'absolutely', 'that\'s right']
        negative_keywords = ['no', 'not really', 'disagree', 'wrong', 'not quite']
        
        has_positive = any(kw in reply_lower for kw in positive_keywords)
        has_negative = any(kw in reply_lower for kw in negative_keywords)
        
        updated = []
        for hyp in hypotheses:
            new_hyp = hyp.model_copy()
            
            if has_positive and not has_negative:
                new_hyp.confidence = min(1.0, hyp.confidence + 0.15)
                new_hyp.confirmations += 1
            elif has_negative and not has_positive:
                new_hyp.confidence = max(0.0, hyp.confidence - 0.15)
            else:
                # Neutral - slight adjustment based on reply length
                if len(user_reply.split()) > 20:  # detailed reply
                    new_hyp.confidence = min(1.0, hyp.confidence + 0.05)
            
            updated.append(new_hyp)
        
        return updated
    
    def check_exit_conditions(self, hypotheses: List[CruxHypothesis], budget_used: int) -> Optional[Tuple[str, ExcavationResult]]:
        """
        Check if any exit conditions are met and return result if so.
        """
        active_hypotheses = [h for h in hypotheses if h.status == "active"]
        
        if not active_hypotheses:
            # All hypotheses discarded - this shouldn't happen but handle gracefully
            logger.warning("All hypotheses discarded - using fallback")
            return self._create_fallback_result(hypotheses, "budget")
        
        # Sort by confidence
        sorted_hyp = sorted(active_hypotheses, key=lambda h: h.confidence, reverse=True)
        top_hyp = sorted_hyp[0]
        
        # Check threshold condition
        confidence_gap = (top_hyp.confidence - sorted_hyp[1].confidence) if len(sorted_hyp) > 1 else 1.0
        
        exit_flags = {
            "passed_threshold": top_hyp.confidence >= self.settings.tau_high and confidence_gap >= self.settings.delta_gap,
            "passed_confirmations": top_hyp.confirmations >= self.settings.n_confirmations,
            "budget_exhausted": budget_used >= self.settings.k_budget
        }
        
        # Determine exit condition
        if exit_flags["passed_threshold"]:
            logger.info(f"Exit condition met: threshold (confidence={top_hyp.confidence:.2f}, gap={confidence_gap:.2f})")
            return ("threshold", self._create_result(hypotheses, "threshold"))
        elif exit_flags["passed_confirmations"]:
            logger.info(f"Exit condition met: confirmations ({top_hyp.confirmations} >= {self.settings.n_confirmations})")
            return ("confirmations", self._create_result(hypotheses, "confirmations"))
        elif exit_flags["budget_exhausted"]:
            logger.info(f"Exit condition met: budget exhausted ({budget_used} >= {self.settings.k_budget})")
            return ("budget", self._create_result(hypotheses, "budget"))
        
        return None
    
    def _create_result(self, hypotheses: List[CruxHypothesis], exit_reason: str) -> ExcavationResult:
        """Create excavation result from final state."""
        active_hypotheses = [h for h in hypotheses if h.status == "active"]
        discarded_hypotheses = [h for h in hypotheses if h.status == "discarded"]
        
        if not active_hypotheses:
            return self._create_fallback_result(hypotheses, exit_reason)
        
        # Top hypothesis becomes confirmed crux
        sorted_active = sorted(active_hypotheses, key=lambda h: h.confidence, reverse=True)
        top_hyp = sorted_active[0]
        
        confirmed_crux = ConfirmedCrux(
            hypothesis_id=top_hyp.hypothesis_id,
            text=top_hyp.text,
            confidence=top_hyp.confidence
        )
        
        # Others with confirmations become secondary themes
        secondary_themes = []
        for hyp in sorted_active[1:]:
            if hyp.confirmations >= 1:
                theme = SecondaryTheme(
                    hypothesis_id=hyp.hypothesis_id,
                    text=hyp.text,
                    confirmations=hyp.confirmations,
                    confidence=hyp.confidence
                )
                secondary_themes.append(theme)
        
        # Build discarded log
        discarded_log = [
            DiscardedHypothesisLogItem(
                hypothesis_id=hyp.hypothesis_id,
                text=hyp.text,
                reason=hyp.discard_reason or "Low confidence"
            )
            for hyp in discarded_hypotheses
        ]
        
        reasoning_trail = self._build_reasoning_trail(confirmed_crux, secondary_themes, discarded_log, exit_reason)
        
        excavation_summary = ExcavationSummary(
            exit_reason=exit_reason,
            reasoning_trail=reasoning_trail,
            discarded_log=discarded_log
        )
        
        return ExcavationResult(
            confirmed_crux=confirmed_crux,
            secondary_themes=secondary_themes,
            excavation_summary=excavation_summary
        )
    
    def _create_fallback_result(self, hypotheses: List[CruxHypothesis], exit_reason: str) -> ExcavationResult:
        """Create fallback result when no active hypotheses remain."""
        # Use the hypothesis with highest confidence overall
        if hypotheses:
            best_hyp = max(hypotheses, key=lambda h: h.confidence)
        else:
            # Ultimate fallback
            best_hyp = CruxHypothesis(
                text="The situation involves complex emotions that need further exploration",
                confidence=0.5,
                confirmations=0,
                status="active"
            )
        
        confirmed_crux = ConfirmedCrux(
            hypothesis_id=best_hyp.hypothesis_id,
            text=best_hyp.text,
            confidence=best_hyp.confidence
        )
        
        reasoning_trail = f"Excavation ended due to {exit_reason}. Selected most plausible hypothesis from available options."
        
        excavation_summary = ExcavationSummary(
            exit_reason=exit_reason,
            reasoning_trail=reasoning_trail,
            discarded_log=[]
        )
        
        return ExcavationResult(
            confirmed_crux=confirmed_crux,
            secondary_themes=[],
            excavation_summary=excavation_summary
        )
    
    def _build_reasoning_trail(self, crux: ConfirmedCrux, themes: List[SecondaryTheme], 
                             discarded: List[DiscardedHypothesisLogItem], exit_reason: str) -> str:
        """Build a narrative reasoning trail."""
        trail = f"Selected '{crux.text}' as the confirmed crux (confidence: {crux.confidence:.2f}) "
        trail += f"based on {exit_reason} exit condition. "
        
        if themes:
            trail += f"Identified {len(themes)} secondary themes with partial confirmation. "
        
        if discarded:
            trail += f"Discarded {len(discarded)} hypotheses due to insufficient evidence."
        
        return trail