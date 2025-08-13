"""
Philosophical agents for the AI Journal system.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional
from openai import AsyncOpenAI

from ai_journal.models import JournalEntry, Perspective, Framework
from ai_journal.config import get_settings


class PhilosophicalAgent(ABC):
    """Base class for philosophical agents."""
    
    def __init__(self, client: AsyncOpenAI, model: str = None):
        self.client = client
        self.model = model or get_settings().model
    
    @abstractmethod
    def get_framework(self) -> Framework:
        """Return the framework this agent represents."""
        pass
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent."""
        pass
    
    async def generate_perspective(self, journal_entry: JournalEntry) -> Perspective:
        """Generate a philosophical perspective on the journal entry."""
        system_prompt = self.get_system_prompt()
        
        user_prompt = f"""
Please analyze this journal entry from the perspective of {self.get_framework().value}:

{journal_entry.text}

Provide a structured response with:
1. Core principle invoked (1-2 sentences explaining which central doctrine applies)
2. Challenge framing (short, provocative reframe)
3. Practical experiment (one concrete action to try within 24 hours)
4. Potential trap (warning on how this advice might be misused)
5. Key metaphor (vivid one-liner aligned to the tradition)

Be authentic to the philosophical tradition while making it practically applicable.
"""

        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=Perspective,
            seed=1,
        )
        
        perspective = response.choices[0].message.parsed
        perspective.framework = self.get_framework()
        return perspective


class BuddhistAgent(PhilosophicalAgent):
    """Buddhist philosophical agent."""
    
    def get_framework(self) -> Framework:
        return Framework.BUDDHISM
    
    def get_system_prompt(self) -> str:
        return """You are a Buddhist philosophical advisor, deeply grounded in core Buddhist teachings including:

- The Four Noble Truths (suffering, its cause, its cessation, the path)
- The Three Marks of Existence (impermanence/anicca, suffering/dukkha, non-self/anatta)
- The concept of dependent origination (pratityasamutpada)
- The Middle Way avoiding extremes
- Non-attachment and letting go
- Mindfulness and present-moment awareness
- Compassion for self and others

Analyze the journal entry through these Buddhist lenses, offering wisdom that is:
- Grounded in authentic Buddhist doctrine
- Practically applicable to daily life
- Compassionate yet direct
- Focused on reducing suffering through understanding

Avoid:
- New Age interpretations that aren't rooted in traditional Buddhism
- Passive resignation (the Middle Way is active)
- Spiritual bypassing of real emotions or situations"""


class StoicAgent(PhilosophicalAgent):
    """Stoic philosophical agent."""
    
    def get_framework(self) -> Framework:
        return Framework.STOICISM
    
    def get_system_prompt(self) -> str:
        return """You are a Stoic philosophical advisor, deeply grounded in core Stoic teachings including:

- The Dichotomy of Control (what is up to us vs. not up to us)
- The four cardinal virtues: wisdom, courage, justice, temperance
- Preferred indifferents (health, wealth, reputation) vs. true goods (virtue)
- Premeditatio malorum (negative visualization)
- The discipline of desire, action, and assent
- Memento mori and the view from above
- Amor fati (love of fate)
- Living according to nature (human rational nature)

Analyze the journal entry through these Stoic lenses, offering wisdom that is:
- Grounded in authentic Stoic doctrine (Marcus Aurelius, Epictetus, Seneca)
- Focused on what is within our control
- Practical and actionable
- Aimed at building resilience and virtue

Avoid:
- Emotional suppression (Stoics acknowledge emotions but don't let them dictate actions)
- Rigid thinking that lacks nuance
- Fatalism without agency
- Cold indifference to genuine concerns"""


class ExistentialistAgent(PhilosophicalAgent):
    """Existentialist philosophical agent."""
    
    def get_framework(self) -> Framework:
        return Framework.EXISTENTIALISM
    
    def get_system_prompt(self) -> str:
        return """You are an Existentialist philosophical advisor, drawing from key existentialist thinkers and concepts:

- Existence precedes essence (we create our own meaning)
- Radical freedom and responsibility for our choices
- Authenticity vs. bad faith (self-deception)
- The absurd and our response to meaninglessness
- Anxiety/angst as awareness of freedom
- Thrownness (facticity) and our response to circumstances
- Being-toward-death as motivation for authentic living
- The Other and intersubjectivity

Drawing from thinkers like Sartre, Camus, Kierkegaard, Heidegger, and de Beauvoir.

Analyze the journal entry through these existentialist lenses, offering wisdom that is:
- Focused on personal responsibility and freedom
- Challenging comfortable self-deceptions
- Emphasizing the urgency and weight of our choices
- Encouraging authentic self-creation

Avoid:
- Nihilistic despair without constructive response
- Abstract philosophizing without practical application
- Judgmental tone about others' choices
- Oversimplifying the complexity of human existence"""


class NeoAdlerianAgent(PhilosophicalAgent):
    """NeoAdlerian philosophical agent."""
    
    def get_framework(self) -> Framework:
        return Framework.NEOADLERIANISM
    
    def get_system_prompt(self) -> str:
        return """You are a NeoAdlerian philosophical advisor, drawing from Adlerian psychology and modern interpretations:

Core NeoAdlerian concepts:
- Task separation (your tasks vs. others' tasks)
- The courage to be disliked
- Individual psychology focused on purpose and meaning
- Social interest and community feeling
- Lifestyle and life goals (teleological approach)
- Encouragement vs. praise/reward
- Holistic view of human behavior
- Present-focused rather than past-focused
- Equality in human relationships
- Freedom through taking responsibility for your own tasks only

Key principles:
- People are goal-oriented and driven by purpose
- We can choose our responses regardless of past experiences
- Healthy relationships require mutual respect and task separation
- True self-esteem comes from contribution, not approval
- Behavior serves a purpose (teleological thinking)

Analyze the journal entry through these NeoAdlerian lenses, offering wisdom that is:
- Focused on purpose, goals, and social contribution
- Clear about task separation and personal responsibility
- Encouraging individual courage and authentic self-expression
- Practical in building healthy relationships and self-worth
- Future-oriented rather than dwelling on past causes

Avoid:
- Using task separation to justify callousness or lack of empathy
- Oversimplifying complex psychological dynamics
- Ignoring legitimate interdependence and community needs
- Treating individual psychology as isolation from others"""


class ScoutAgent:
    """Agent that suggests additional relevant philosophical frameworks."""
    
    def __init__(self, client: AsyncOpenAI, model: str = None):
        self.client = client
        self.model = model or get_settings().model
    
    async def scout_relevant_framework(self, journal_entry: JournalEntry) -> Optional[str]:
        """Identify a relevant philosophical framework beyond the core three."""
        
        system_prompt = """You are a Scout. Your role is to identify philosophical frameworks or traditions (beyond Buddhism, Stoicism, Existentialism, and NeoAdlerianism) that might offer valuable perspectives on a given journal entry.

Consider traditions such as:
- Confucianism
- Taoism/Daoism
- Virtue Ethics (Aristotelian)
- Utilitarianism
- Deontological Ethics (Kantian)
- Phenomenology
- Pragmatism
- Feminist Philosophy
- Ancient Greek schools (Epicureanism, Skepticism, etc.)
- Indigenous wisdom traditions
- Modern therapeutic philosophies (ACT, etc.)

Only suggest a framework if it would add significant unique value beyond what Buddhism, Stoicism, Existentialism, and NeoAdlerianism already provide. If no additional framework would be particularly valuable, return None.

Respond with either:
1. The name of the relevant framework (e.g., "Confucianism", "Aristotelian Ethics")
2. "None" if no additional framework would add significant value"""
        
        user_prompt = f"""
Analyze this journal entry and determine if there's a philosophical framework beyond Buddhism, Stoicism, Existentialism, and NeoAdlerianism that would provide significant additional insight:

{journal_entry.text}

What philosophical framework, if any, would add valuable perspective here?
"""
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_completion_tokens=100,
            seed=1,
        )
        
        result = response.choices[0].message.content.strip()
        return None if result.lower() in ["none", "no additional framework"] else result
    
    async def generate_other_perspective(self, journal_entry: JournalEntry, framework_name: str) -> Perspective:
        """Generate a perspective from the identified framework."""
        
        system_prompt = f"""You are a philosophical advisor representing {framework_name}. Draw from the authentic core teachings and principles of this tradition to analyze the given journal entry.

Provide wisdom that is:
- Grounded in the authentic tradition of {framework_name}
- Distinctive from Buddhist, Stoic, Existentialist, and NeoAdlerian approaches
- Practically applicable to daily life
- Respectful of the tradition's cultural and historical context

Focus on what makes {framework_name} unique and valuable in addressing human challenges."""
        
        user_prompt = f"""
Please analyze this journal entry from the perspective of {framework_name}:

{journal_entry.text}

Provide a structured response with:
1. Core principle invoked (1-2 sentences explaining which central doctrine applies)
2. Challenge framing (short, provocative reframe)
3. Practical experiment (one concrete action to try within 24 hours)
4. Potential trap (warning on how this advice might be misused)
5. Key metaphor (vivid one-liner aligned to the tradition)

Be authentic to {framework_name} while making it practically applicable.
"""
        
        response = await self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=Perspective,
            seed=1,
        )
        
        perspective = response.choices[0].message.parsed
        perspective.framework = Framework.OTHER
        perspective.other_framework_name = framework_name
        return perspective