"""
Oracle meta-agent for cross-philosophical synthesis and analysis.
"""

from itertools import combinations
from typing import List
from openai import AsyncOpenAI

from ai_journal.models import Perspective, Perspectives, Prophecy, Framework, AgreementItem, TensionPoint, AgreementStance


class OracleAgent:
    """Oracle meta-agent that synthesizes perspectives from multiple philosophical frameworks."""
    
    def __init__(self, client: AsyncOpenAI, model: str = "gpt-4o-mini"):
        self.client = client
        self.model = model
    
    async def generate_prophecy(self, perspectives: Perspectives) -> Prophecy:
        """Generate cross-framework meta-analysis and synthesis."""
        
        # Generate agreement scorecard
        agreement_scorecard = await self._generate_agreement_scorecard(perspectives)
        
        # Generate tension summary
        tension_summary = await self._generate_tension_summary(perspectives)
        
        # Generate synthesis
        synthesis = await self._generate_synthesis(perspectives)
        
        # Generate what is lost by blending
        what_is_lost = await self._generate_what_is_lost(perspectives)
        
        return Prophecy(
            agreement_scorecard=agreement_scorecard,
            tension_summary=tension_summary,
            synthesis=synthesis,
            what_is_lost_by_blending=what_is_lost
        )
    
    async def _generate_agreement_scorecard(self, perspectives: Perspectives) -> List[AgreementItem]:
        """Generate pairwise agreement analysis between philosophical frameworks."""
        
        frameworks = [p.framework for p in perspectives.items]
        agreement_items = []
        
        # Generate all pairwise combinations
        for framework_a, framework_b in combinations(frameworks, 2):
            perspective_a = next(p for p in perspectives.items if p.framework == framework_a)
            perspective_b = next(p for p in perspectives.items if p.framework == framework_b)
            
            system_prompt = f"""You are an Oracle analyzing philosophical perspectives. Compare two perspectives and determine their agreement level.

Perspective A ({framework_a}):
- Core principle: {perspective_a.core_principle_invoked}
- Challenge: {perspective_a.challenge_framing}
- Experiment: {perspective_a.practical_experiment}
- Trap: {perspective_a.potential_trap}
- Metaphor: {perspective_a.key_metaphor}

Perspective B ({framework_b}):
- Core principle: {perspective_b.core_principle_invoked}
- Challenge: {perspective_b.challenge_framing}
- Experiment: {perspective_b.practical_experiment}
- Trap: {perspective_b.potential_trap}
- Metaphor: {perspective_b.key_metaphor}

Determine the agreement stance:
- AGREE: Frameworks fundamentally align in their approach and recommendations
- DIVERGE: Frameworks have fundamentally different or conflicting approaches
- NUANCED: Frameworks have some alignment but differ in important ways

Respond with just the stance (AGREE, DIVERGE, or NUANCED) and an optional brief note explaining the assessment."""
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}],
                max_completion_tokens=150,
            )
            
            result = response.choices[0].message.content.strip()
            lines = result.split('\n', 1)
            stance_str = lines[0].strip().upper()
            notes = lines[1].strip() if len(lines) > 1 else None
            
            try:
                stance = AgreementStance(stance_str.lower())
            except ValueError:
                stance = AgreementStance.NUANCED  # Default fallback
            
            agreement_items.append(AgreementItem(
                framework_a=framework_a,
                framework_b=framework_b,
                stance=stance,
                notes=notes
            ))
        
        return agreement_items
    
    async def _generate_tension_summary(self, perspectives: Perspectives) -> List[TensionPoint]:
        """Generate explanations of philosophical tensions and divergences."""
        
        perspectives_text = "\n\n".join([
            f"{p.framework} ({p.other_framework_name if p.framework == Framework.OTHER else p.framework.value}):\n"
            f"- Core principle: {p.core_principle_invoked}\n"
            f"- Challenge: {p.challenge_framing}\n"
            f"- Experiment: {p.practical_experiment}\n"
            f"- Trap: {p.potential_trap}\n"
            f"- Metaphor: {p.key_metaphor}"
            for p in perspectives.items
        ])
        
        system_prompt = """You are an Oracle identifying philosophical tensions. Analyze the given perspectives and identify key points where philosophical frameworks diverge in their fundamental assumptions, methods, or goals.

For each tension point, explain:
1. Which frameworks are involved in the tension
2. What core philosophical principles drive the disagreement
3. Why these differences matter practically

Focus on substantive philosophical differences, not surface-level variations. A good tension point reveals something important about the nature of each tradition."""
        
        user_prompt = f"""
Analyze these philosophical perspectives and identify 1-3 key tension points where frameworks fundamentally diverge:

{perspectives_text}

For each tension, specify which frameworks are involved and explain the philosophical basis of their disagreement.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=800
        )
        
        # Parse the response into tension points
        # This is a simplified parsing - in production, you might want structured output
        tension_text = response.choices[0].message.content.strip()
        
        # For now, create a single tension point with all frameworks
        # In production, you'd parse the response more carefully
        frameworks = [p.framework for p in perspectives.items]
        
        return [TensionPoint(
            frameworks=frameworks,
            explanation=tension_text
        )]
    
    async def _generate_synthesis(self, perspectives: Perspectives) -> str:
        """Generate unified synthesis respecting all perspectives."""
        
        perspectives_text = "\n\n".join([
            f"{p.framework} ({p.other_framework_name if p.framework == Framework.OTHER else p.framework.value}):\n"
            f"- Core principle: {p.core_principle_invoked}\n"
            f"- Challenge: {p.challenge_framing}\n"
            f"- Experiment: {p.practical_experiment}\n"
            f"- Trap: {p.potential_trap}\n"
            f"- Metaphor: {p.key_metaphor}"
            for p in perspectives.items
        ])
        
        system_prompt = """You are an Oracle creating philosophical synthesis. Your task is to weave together insights from different philosophical traditions into a unified approach that:

1. Respects the wisdom of each tradition
2. Creates a coherent, actionable plan
3. Acknowledges where traditions complement each other
4. Doesn't force artificial agreement where real differences exist

The synthesis should be practical and implementable while maintaining philosophical depth. It should feel like a genuine integration, not just a list of separate recommendations."""
        
        user_prompt = f"""
Create a unified synthesis that integrates these philosophical perspectives:

{perspectives_text}

Provide a coherent approach or principle that draws from all perspectives while respecting their distinctiveness. Focus on how they can work together practically.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=1000,
        )
        
        return response.choices[0].message.content.strip()
    
    async def _generate_what_is_lost(self, perspectives: Perspectives) -> List[str]:
        """Generate explicit list of what philosophical richness is lost by blending."""
        
        perspectives_text = "\n\n".join([
            f"{p.framework} ({p.other_framework_name if p.framework == Framework.OTHER else p.framework.value}):\n"
            f"- Core principle: {p.core_principle_invoked}\n"
            f"- Challenge: {p.challenge_framing}\n"
            f"- Experiment: {p.practical_experiment}\n"
            f"- Trap: {p.potential_trap}\n"
            f"- Metaphor: {p.key_metaphor}"
            for p in perspectives.items
        ])
        
        system_prompt = """You are an Oracle identifying what is lost in philosophical synthesis. When different philosophical traditions are blended into a unified approach, some of their distinctive power and insight is inevitably diminished.

Identify specific aspects of each tradition that become softened, compromised, or lost when integrated with others. Be honest about the trade-offs. This isn't criticism of synthesis - it's acknowledgment that pure traditions have qualities that don't survive blending.

Examples of what might be lost:
- The radical edge of existential anxiety when combined with Stoic equanimity
- Buddhist non-attachment when paired with engaged action
- Stoic practical focus when mixed with contemplative approaches"""
        
        user_prompt = f"""
Given these philosophical perspectives, identify 2-4 specific things that are lost or diminished when they are blended into a synthesis:

{perspectives_text}

List specific qualities, emphases, or insights that become softened or compromised in the integration process.
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=600,
        )
        
        # Parse into list items
        result = response.choices[0].message.content.strip()
        lines = [line.strip() for line in result.split('\n') if line.strip()]
        
        # Clean up bullet points or numbered items
        cleaned_items = []
        for line in lines:
            line = line.lstrip('•-*1234567890. ')
            if line:
                cleaned_items.append(line)
        
        return cleaned_items[:4]  # Limit to 4 items