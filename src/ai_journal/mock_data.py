"""
Mock data generator for rapid frontend development.
Provides hardcoded responses that match the production API structure.
"""

from ai_journal.models import (
    JournalEntry,
    Perspective,
    Perspectives,
    Framework,
    AgreementItem,
    AgreementStance,
    TensionPoint,
    Prophecy,
    Reflection,
    ReflectionResponse,
)


def generate_mock_reflection(journal_text: str, enable_scout: bool = False) -> ReflectionResponse:
    """Generate a mock reflection response for frontend testing."""
    
    # Create mock journal entry
    journal_entry = JournalEntry(text=journal_text)
    
    # Create mock perspectives
    buddhist = Perspective(
        framework=Framework.BUDDHISM,
        other_framework_name=None,
        core_principle_invoked=(
            "The suffering (dukkha) you experience stems from attachment to approval and fear of disappointment. "
            "The path to freedom involves cultivating non-attachment through mindful awareness and compassionate boundaries."
        ),
        challenge_framing="Your people-pleasing is a form of spiritual bypassing—avoiding authentic presence out of fear.",
        practical_experiment=(
            "Before saying 'yes' to any request today, pause for three conscious breaths and ask: "
            "'Am I responding from clarity or from craving for approval?'"
        ),
        potential_trap=(
            "Don't mistake emotional numbness for non-attachment. True equanimity includes compassionate engagement."
        ),
        key_metaphor="Like water that flows around obstacles rather than fighting them, find the gentle path of wise refusal."
    )
    
    stoic = Perspective(
        framework=Framework.STOICISM,
        other_framework_name=None,
        core_principle_invoked=(
            "Apply the Dichotomy of Control: you cannot control others' requests or judgments, "
            "but you can control your responses and boundaries. Virtue requires choosing what serves the greater good."
        ),
        challenge_framing="Saying yes to everything is not virtue—it's surrendering your agency to external pressures.",
        practical_experiment=(
            "For the next week, before committing to any request, ask: 'Does this align with my duties and values, "
            "or am I acting from fear of others' opinions?'"
        ),
        potential_trap=(
            "Don't become rigidly selfish. True wisdom sometimes requires sacrifice for legitimate duties—"
            "just ensure you're choosing, not being chosen for."
        ),
        key_metaphor="Be like a fortress: strong walls protect what matters, but they also have gates for worthy visitors."
    )
    
    existentialist = Perspective(
        framework=Framework.EXISTENTIALISM,
        other_framework_name=None,
        core_principle_invoked=(
            "You are condemned to be free—every 'yes' or 'no' is a choice that defines who you become. "
            "Authenticity requires owning your decisions rather than deferring to others' expectations."
        ),
        challenge_framing="When you say yes to everything, you're living in bad faith—denying your freedom to choose.",
        practical_experiment=(
            "This week, make one decision that might disappoint someone but aligns with your authentic values. "
            "Notice the anxiety of freedom—and embrace it."
        ),
        potential_trap=(
            "Don't use authenticity as an excuse for selfishness. True freedom includes responsibility "
            "for how your choices affect others."
        ),
        key_metaphor="You are both the sculptor and the marble—every choice shapes the person you're becoming."
    )
    
    perspectives_list = [buddhist, stoic, existentialist]
    
    # Add mock scout perspective if enabled
    if enable_scout:
        scout = Perspective(
            framework=Framework.OTHER,
            other_framework_name="Attachment Theory",
            core_principle_invoked=(
                "Your people-pleasing patterns likely stem from anxious attachment styles developed in childhood. "
                "Secure relationships require the ability to say no without fear of abandonment."
            ),
            challenge_framing="You're using compliance as a strategy to maintain connection, but it creates resentment instead.",
            practical_experiment=(
                "Practice expressing a small disagreement with someone safe, focusing on maintaining connection "
                "while honoring your perspective."
            ),
            potential_trap=(
                "Don't swing to avoidant attachment. The goal is secure attachment—being able to connect "
                "authentically without losing yourself."
            ),
            key_metaphor="Like a tree that bends in the wind but stays rooted—flexibility without losing your ground."
        )
        perspectives_list.append(scout)
    
    perspectives = Perspectives(items=perspectives_list)
    
    # Create mock prophecy
    agreements = []
    if enable_scout:
        # More agreements with scout enabled
        agreements = [
            AgreementItem(
                framework_a=Framework.BUDDHISM,
                framework_b=Framework.STOICISM,
                stance=AgreementStance.AGREE,
                notes="Both emphasize the importance of internal freedom and not being controlled by external forces."
            ),
            AgreementItem(
                framework_a=Framework.BUDDHISM,
                framework_b=Framework.EXISTENTIALISM,
                stance=AgreementStance.NUANCED,
                notes="Both value authentic choice, but differ on whether there are universal principles to guide decisions."
            ),
            AgreementItem(
                framework_a=Framework.STOICISM,
                framework_b=Framework.EXISTENTIALISM,
                stance=AgreementStance.NUANCED,
                notes="Both emphasize personal responsibility, but Stoicism grounds this in natural law while Existentialism in radical freedom."
            ),
            AgreementItem(
                framework_a=Framework.BUDDHISM,
                framework_b=Framework.OTHER,
                stance=AgreementStance.AGREE,
                notes="Buddhist mindfulness and attachment theory both recognize how past conditioning shapes present behavior patterns."
            ),
        ]
    else:
        agreements = [
            AgreementItem(
                framework_a=Framework.BUDDHISM,
                framework_b=Framework.STOICISM,
                stance=AgreementStance.AGREE,
                notes="Both emphasize the importance of internal freedom and not being controlled by external forces."
            ),
            AgreementItem(
                framework_a=Framework.BUDDHISM,
                framework_b=Framework.EXISTENTIALISM,
                stance=AgreementStance.NUANCED,
                notes="Both value authentic choice, but differ on whether there are universal principles to guide decisions."
            ),
            AgreementItem(
                framework_a=Framework.STOICISM,
                framework_b=Framework.EXISTENTIALISM,
                stance=AgreementStance.NUANCED,
                notes="Both emphasize personal responsibility, but Stoicism grounds this in natural law while Existentialism in radical freedom."
            ),
        ]
    
    frameworks_in_tension = [Framework.BUDDHISM, Framework.STOICISM, Framework.EXISTENTIALISM]
    if enable_scout:
        frameworks_in_tension.append(Framework.OTHER)
    
    tensions = [
        TensionPoint(
            frameworks=frameworks_in_tension,
            explanation=(
                "The fundamental tension lies in the source of ethical guidance: "
                "Buddhism grounds ethics in the alleviation of suffering, "
                "Stoicism in natural law and virtue, "
                "Existentialism in authentic self-creation" +
                (", and Attachment Theory in psychological health and secure relationships." if enable_scout else ".") +
                " These different foundations can lead to conflicting advice in specific situations, "
                "especially around how much to prioritize others' needs versus personal authenticity."
            )
        )
    ]
    
    synthesis = (
        "**Integrated Wisdom: Conscious Boundary-Setting**\n\n"
        "The path forward integrates all perspectives through **conscious choice**:\n\n"
        "1. **Pause and Awareness** (Buddhist): Before responding to any request, take a moment to notice "
        "your motivations. Are you acting from clarity or from attachment to approval?\n\n"
        "2. **Values Assessment** (Stoic): Ask yourself what truly serves the greater good, including your "
        "own wellbeing and capacity to contribute meaningfully.\n\n"
        "3. **Authentic Response** (Existentialist): Choose your response based on who you want to become, "
        "not who others expect you to be.\n\n"
        + ("4. **Secure Connection** (Attachment): Practice saying no in ways that maintain relationship "
           "while honoring your needs—showing that boundaries can strengthen rather than threaten bonds.\n\n" if enable_scout else "") +
        "**Practical Framework**: When facing a request, use this sequence:\n"
        "- Breath (awareness)\n"
        "- Values check (alignment) \n"
        "- Authentic choice (freedom)\n"
        "- Compassionate communication (connection)\n\n"
        "This approach honors the wisdom of all traditions while remaining practically applicable."
    )
    
    what_is_lost = [
        "The sharp clarity that comes from fully committing to one philosophical tradition",
        "Buddhist: The radical insight that all suffering stems from attachment—this gets softened into 'healthy boundaries'",
        "Stoic: The fierce discipline of focusing only on what you control—becomes mixed with concern for others' feelings", 
        "Existentialist: The terrifying freedom of absolute choice—gets cushioned by frameworks and systems"
    ]
    
    if enable_scout:
        what_is_lost.append(
            "Attachment Theory: The deep therapeutic work of healing childhood wounds—becomes simplified into communication techniques"
        )
    
    prophecy = Prophecy(
        agreement_scorecard=agreements,
        tension_summary=tensions,
        synthesis=synthesis,
        what_is_lost_by_blending=what_is_lost
    )
    
    # Create reflection
    reflection = Reflection(
        journal_entry=journal_entry,
        perspectives=perspectives,
        prophecy=prophecy
    )
    
    return ReflectionResponse(reflection=reflection)