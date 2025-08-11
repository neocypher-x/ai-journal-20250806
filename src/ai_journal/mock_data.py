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
    
    # Base perspectives - always include these four
    buddhist = Perspective(
        framework=Framework.BUDDHISM,
        other_framework_name=None,
        core_principle_invoked="From a Buddhist view, this pattern arises from craving (the desire to please) and aversion (fear of discomfort). By applying Right Intention and mindful effort as part of the Eightfold Path, you can align your commitments with true priorities and reduce dukkha.",
        challenge_framing="Your calendar is a mirror of your mind: saying yes to everything is saying no to your own peace.",
        practical_experiment="Decline one nonessential request today with a brief, compassionate explanation and offer an alternative timeline.",
        potential_trap="Watch for rigidity or avoidance masquerading as wisdom: boundary-setting should be compassionate and wise, not a weapon or a bypass for responsibility.",
        key_metaphor="Chop wood, carry water—mindful work in service of clarity, not compulsion."
    )
    
    stoic = Perspective(
        framework=Framework.STOICISM,
        other_framework_name=None,
        core_principle_invoked="The Dichotomy of Control—you can govern your own assent and choices, but not others' demands or outcomes. Since virtue is the only true good, align your 'yes' with actions that honor your rational nature and decline what does not.",
        challenge_framing="Your 'yes' may be a fear-driven habit; reframe by asking: what would a wise person consent to in this moment?",
        practical_experiment="In the next 24 hours, pause before any non-essential request and respond with a brief, courteous boundaries script: 'I can't take this on today due to other commitments. If it's important, we can revisit after we prioritize current duties, or I can suggest someone else who can help.'",
        potential_trap="Risk of rigidity or shirking necessary duties. Use discernment to ensure boundary-setting serves justice, temperance, and the common good, not mere self-denial or avoidance.",
        key_metaphor="The inner citadel gates—let only virtue pass; keep the rest outside."
    )
    
    existentialist = Perspective(
        framework=Framework.EXISTENTIALISM,
        other_framework_name=None,
        core_principle_invoked="Existence precedes essence: you create meaning through your choices, not by fulfilling a predefined role. Your radical freedom carries responsibility: saying yes to work you don't want is a small act of bad faith that forfeits your authenticity.",
        challenge_framing="Saying no to what you don't want is not denial; it's the first explicit act of self-ownership.",
        practical_experiment="Today, pick one task you routinely say yes to but hate, and send a concise boundary statement to the person who assigns it, requesting a change in scope or deadline or a renegotiation of responsibilities.",
        potential_trap="Boundaries must be grounded in care and awareness of consequences; avoid using authenticity as an excuse to shirk obligations or to punish others; ensure your actions consider the impact on colleagues and the system.",
        key_metaphor="Bad faith signs other people's names on your to-do list; authenticity signs your own."
    )
    
    neoadlerian = Perspective(
        framework=Framework.NEOADLERIANISM,
        other_framework_name=None,
        core_principle_invoked="You are responsible for your own tasks and responses; behavior is teleological and aimed at a meaningful, socially constructive goal. By separating your tasks from others' and aligning actions with a clear purpose, you create room to contribute while preserving your own energy and growth.",
        challenge_framing="Every unwanted yes is a quiet no to your own life. The real question is: what is mine to own, and what am I willing to let go of for a meaningful purpose?",
        practical_experiment="Within the next 24 hours, decline one non-essential request using a brief boundary script: 'I can't take that on right now due to my current commitments; can we revisit later or could it be delegated?' Then note how this affects your sense of control and the other person's response.",
        potential_trap="Setting boundaries can be misused as coldness or avoidance of collaboration. Be sure to accompany your boundaries with empathy, clear communication, and a willingness to contribute where your tasks truly lie and where you can offer meaningful social value.",
        key_metaphor="Every yes you give plants someone else's flag on your time."
    )
    
    perspectives_list = [buddhist, stoic, existentialist, neoadlerian]
    
    # Add mock scout perspective if enabled
    if enable_scout:
        scout = Perspective(
            framework=Framework.OTHER,
            other_framework_name="Attachment Theory",
            core_principle_invoked="Your people-pleasing patterns likely stem from anxious attachment styles developed in childhood. Secure relationships require the ability to say no without fear of abandonment.",
            challenge_framing="You're using compliance as a strategy to maintain connection, but it creates resentment instead.",
            practical_experiment="Practice expressing a small disagreement with someone safe, focusing on maintaining connection while honoring your perspective.",
            potential_trap="Don't swing to avoidant attachment. The goal is secure attachment—being able to connect authentically without losing yourself.",
            key_metaphor="Like a tree that bends in the wind but stays rooted—flexibility without losing your ground."
        )
        perspectives_list.append(scout)
    
    perspectives = Perspectives(items=perspectives_list)
    
    # Create mock prophecy - base agreements
    agreements = [
        AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.STOICISM,
            stance=AgreementStance.AGREE,
            notes="Both advocate mindful boundary-setting to reduce unnecessary commitments and suffering, and to align actions with higher priorities/virtues. Differences lie in ultimate aims (dukkha/nirvana vs virtue/nature) rather than in practical stance toward boundaries."
        ),
        AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.EXISTENTIALISM,
            stance=AgreementStance.NUANCED,
            notes="Both prize intentional choice and personal responsibility, but Buddhism emphasizes reducing craving and compassionate harmony (end of suffering) while existentialism centers on authentic meaning-making and self-authored essence. Boundary-setting can align, yet their ultimate teloi differ."
        ),
        AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.NEOADLERIANISM,
            stance=AgreementStance.AGREE,
            notes="Both stress personal responsibility for one's time and actions and advocate boundaries to protect meaningful priorities. Buddhism adds compassion and interdependence; Neoadlerianism emphasizes practical meaning and social contribution—these complement rather than conflict."
        ),
        AgreementItem(
            framework_a=Framework.EXISTENTIALISM,
            framework_b=Framework.STOICISM,
            stance=AgreementStance.NUANCED,
            notes="Shared focus on responsible action and boundaries, but Stoicism prioritizes rational virtue and control over internal assent; existentialism foregrounds radical freedom and self-authored meaning. The methods and grounds for boundary-setting diverge, though practical guidance often overlaps."
        ),
        AgreementItem(
            framework_a=Framework.NEOADLERIANISM,
            framework_b=Framework.STOICISM,
            stance=AgreementStance.AGREE,
            notes="Both advocate disciplined boundary-setting and focusing on tasks aligned with virtue (Stoic rational nature) or meaningful social contribution (Neoadlerianism). Their frameworks differ in metaphysical grounding but align in practical guidance on time and responsibilities."
        ),
        AgreementItem(
            framework_a=Framework.EXISTENTIALISM,
            framework_b=Framework.NEOADLERIANISM,
            stance=AgreementStance.NUANCED,
            notes="Both emphasize deliberate choice and responsibility, but existentialism centers on personal authenticity and freedom; neoadlerianism emphasizes purposeful, socially constructive goals. Boundaries can support both, yet tensions arise where personal desires clash with externally defined meaningful tasks."
        ),
    ]
    
    # Add scout agreements if enabled
    if enable_scout:
        agreements.append(
            AgreementItem(
                framework_a=Framework.BUDDHISM,
                framework_b=Framework.OTHER,
                stance=AgreementStance.AGREE,
                notes="Buddhist mindfulness and attachment theory both recognize how past conditioning shapes present behavior patterns and the importance of compassionate self-awareness."
            )
        )
        agreements.append(
            AgreementItem(
                framework_a=Framework.STOICISM,
                framework_b=Framework.OTHER,
                stance=AgreementStance.NUANCED,
                notes="Both value emotional regulation and healthy relationships, though Stoicism emphasizes rational virtue while Attachment Theory focuses on secure bonding patterns."
            )
        )
    
    frameworks_in_tension = [Framework.BUDDHISM, Framework.STOICISM, Framework.EXISTENTIALISM, Framework.NEOADLERIANISM]
    if enable_scout:
        frameworks_in_tension.append(Framework.OTHER)
    
    tension_explanation = """Here are 3 substantive tension points where the frameworks diverge in their basic assumptions, methods, or aims. For each point, I name the frameworks involved, summarize the core philosophical disagreement, and note why it matters in practice.

Tension Point 1: What justifies saying no to a nonessential request
- Frameworks involved
  - Buddhism
  - Stoicism
  - Existentialism
  - Neoadlerianism
- Core principles driving the disagreement
  - Buddhism: Boundaries arise from right intention and reducing dukkha. Saying no can be a compassionate act if it prevents craving, harm, or distraction from true priorities; the alignment is with mindfulness and interdependent well-being.
  - Stoicism: Boundaries are justified by the dichotomy of control and by virtue. A decision to decline should serve rational self-governance and do not-just because it's irrational or out of line with moral duty.
  - Existentialism: Boundaries are acts of authenticity. Declining is legitimate when it affirms self-ownership and responsibility, resisting "bad faith" by not living as someone else's expectation.
  - Neoadlerianism: Boundaries are justified when they preserve energy for meaningful, socially constructive purposes. Declining should be guided by a teleology of personal responsibility and social value, tempered by empathy and collaboration.
- Why this matters practically
  - Explains why different people might choose different reasons (compassion, virtue, authenticity, usefulness) for the same decline.
  - Affects how you phrase the refusal (tone and rationale), who you involve, and what you offer as alternatives.
  - Determines whether boundary-setting is framed as self-care, moral duty, personal integrity, or service to a larger purpose.

Tension Point 2: The end goal of boundary-setting—inner state vs. virtue vs authenticity vs meaning
- Frameworks involved
  - Buddhism
  - Stoicism
  - Existentialism
  - Neoadlerianism
- Core principles driving the disagreement
  - Buddhism: The ultimate goal is reducing suffering (dukkha) and cultivating wise, compassionate action. Boundaries serve the path to clarity and liberation from craving.
  - Stoicism: The end is virtue (the only true good). Boundaries should cultivate rational agency and align actions with the good, independent of external approval or outcomes.
  - Existentialism: The end is authentic self-authorship and meaning chosen by the individual. Boundaries express responsibility for one's own existence and projects.
  - Neoadlerianism: The end is meaningful contribution within a social teleology. Boundaries should protect time for actions that have clear social value and purpose.
- Why this matters practically
  - When values clash (peace vs virtue, authenticity vs usefulness), you must choose which ends to prioritize in a given situation.
  - This shapes daily decisions about workload, who to help, and how to communicate refusals (e.g., a boundary that preserves inner peace vs one that sustains virtue or social contribution).
  - It affects long-term identity: are you defining yourself by inner serenity, by virtuous conduct, by self-authored projects, or by service to others?

Tension Point 3: The status of control and responsibility—internal sovereignty vs external constraints
- Frameworks involved
  - Buddhism
  - Stoicism
  - Existentialism
  - Neoadlerianism
- Core principles driving the disagreement
  - Buddhism: Reality is interdependent; while you can train intentions, you are embedded in a web of causes and conditions. Boundaries are mindful responses within that web, aiming to reduce suffering for all involved.
  - Stoicism: You control assent and choices, but not outcomes or others' demands. The ideal is to align with nature and virtue, accepting what you cannot influence.
  - Existentialism: You own your freedom and responsibility for choosing how to respond to constraints. Even within social systems, you are always making a self-authored choice.
  - Neoadlerianism: You own your own tasks and responses, balancing personal autonomy with social responsibility. Boundaries protect meaningful action rather than simply retreating from others.
- Why this matters practically
  - Influences how you assess accountability: Are you responsible primarily for your inner state, for virtuous action, for authentic self-definition, or for advancing a socially meaningful project?
  - Affects interpersonal dynamics: If you lean toward interdependence (Buddhism), you may factor others' well-being into decisions; if you lean toward strict autonomy (Stoicism/Existentialism), you may distance yourself; Neoadlerianism emphasizes coordinating boundaries with collaborative goals.
  - Determines risk of rigidity vs. flexibility: Misreading the degree of influence you have can lead to excessive avoidance (rigidity) or overcommitment (compromise of virtue, authenticity, or meaning).

How to use these tensions constructively
- Recognize that each framework answers different fundamental questions: What makes boundary-setting virtuous? What is the highest good to pursue? What counts as genuine freedom? What is your responsibility to others?
- When in doubt, articulate your decision in terms of the value you're prioritizing (e.g., "I'm declining to protect my time for a project that serves X" rather than simply "I don't feel like it") and be explicit about the lens you're using (compassion, virtue, authenticity, or social meaning).
- Be mindful of the traps each tradition warns against (rigidity, avoidance, bad faith, or coldness). Strive for boundary-setting that is humane, reasoned, and coherent with your overarching commitments."""

    if enable_scout:
        tension_explanation += "\n\nWith the addition of Attachment Theory, we see further tensions around whether emotional regulation should prioritize individual virtue (Stoic), interdependent compassion (Buddhist), authentic self-expression (Existentialist), or secure relational bonding (Attachment Theory)."

    tensions = [
        TensionPoint(
            frameworks=frameworks_in_tension,
            explanation=tension_explanation
        )
    ]
    
    synthesis = """Unified synthesis: Boundaries that serve meaning, virtue, authenticity, and compassionate contribution

Core idea
Create a practical practice that honors what each tradition teaches:
- Buddhism: reduce dukkha by cutting craving/aversion, aligning intentions with true priorities, and acting mindfully.
- Stoicism: govern your own assent and choices; virtue is the only true good; say yes only to what your rational nature would approve.
- Existentialism: existence precedes essence; you own the meaning of your actions, so declining or renegotiating should reinforce authentic self-ownership.
- Neoadlerianism: you are responsible for your own tasks and energy; clarify what is yours to own, and preserve room to contribute with intention and social value.

The unified principle
Boundaries are not barriers to care; they are deliberate, compassionate actions that make your meaningful contributions possible. They emerge from clear intention, rational discernment, authentic ownership, and purposeful responsibility.

Practical framework: The 5-step Boundary Cycle
1) Pause with intention (mindful clarity)
- Take a brief breath and ask: What is my initial impulse—craving to please or fear of conflict? What would a wise, virtuous, authentic choice be in this moment?
- Ask three questions:
  - What is mine to own here? (Dichotomy of Control)
  - Which value or priority does this request touch (e.g., care, duty, growth, justice)?
  - Will saying yes today advance my meaningful purpose without compromising other commitments?

2) Translate intention into a boundary (clear, compassionate communication)
- Use a concise boundary script that incorporates the traditions:
  - Acknowledge the request with care.
  - State the boundary with personal responsibility.
  - Offer a constructive alternative (revisit later, delegate, or propose an adjusted scope).
- Example script (one you can adapt):
  "Thank you for thinking of me. I can't take this on today due to my current commitments. If it's important, we can revisit after I've prioritized my duties, or I can suggest someone else who can help. I'm aiming to stay aligned with what I'm able to responsibly take on right now."

3) Act with virtue and ownership (behavior aligned with purpose)
- Decline or renegotiate, but remain helpful where you can. If you offer alternatives, do so with clarity about your capacity and the value you can still contribute.
- Remember: the boundary is a choice that serves your rational good and the good of the system you're part of (colleagues, projects, clients).

4) Reflect and adjust (learn how it lands)
- After the interaction, note what felt true, what caused friction, and how the other person responded.
- Journal or quick notes: Did the boundary preserve energy for meaningful work? Did it create a workable next step?

5) Revisit and refine (iterate toward integrative practice)
- At regular intervals (daily quick check, weekly review), assess whether boundaries need clarifying, rebalancing, or softening/strengthening in light of changing priorities.

Experiment templates (practical, doable)
- 24-hour nonessential request decline
  - Script: "I can't take this on today due to my current commitments. If it's important, we can revisit after I've prioritized my duties, or I can suggest someone else who can help."
  - Action: Use it once for any nonessential request; observe how it affects workload, mood, and the other person's response.
- Daily one-boundary practice
  - Choose one incoming request you're tempted to say yes to but don't want to. Apply the script, and note the outcome: sense of control, balance, and relationship impact.
- Weekly meaning-and-responsibility review
  - Review all commitments; distinguish what is truly yours to own, what can be delegated, and what should be renegotiated in service of meaningful goals.

Boundaries in practice: language that honors each tradition
- Buddhist emphasis on intention and compassion:
  - "I decline to take this on today to maintain mindful focus and reduce suffering for myself and others. If possible, I can help by offering a later time or an alternative solution."
- Stoic emphasis on control and virtue:
  - "I can't take this on today due to other commitments. If it's important, we can revisit after I've prioritized my duties, or I can suggest someone else who can help."
- Existentialist emphasis on authenticity and responsibility:
  - "I'm choosing to decline to preserve my own integrity and the authentic commitments I've chosen. I'm open to renegotiating scope or responsibilities if that respects both our aims."
- Neoadlerian emphasis on task ownership and meaningful contribution:
  - "What's mine to own here? I can't take this on now, but we can revisit later or delegate to someone whose current tasks align with our shared goals."

Common traps and guardrails
- Rigidity masquerading as wisdom
  - Guard against using boundaries to evade responsibility; ensure there is still care for others and the system.
- Boundary-setting as coldness
  - Pair boundaries with warmth, empathy, and a willingness to contribute where your work truly lies.
- Bad faith or inauthentic reasons
  - Ensure the boundary serves genuine priorities, not just a personal preference to avoid discomfort.
- Over-scheduling or under-communicating
  - Balance is key: boundaries should preserve energy for meaningful tasks and clear expectations with others.

A single, coherent synthesis you can live by
- Core principle distilled: Boundaries are mindful, compassionate instruments that preserve your capacity to act with virtue, authenticity, and purposeful contribution.
- The practical practice: Pause, discern, communicate clearly, act with ownership, reflect, and refine.
- The result: You reduce unnecessary commitments, stay true to your values, honor your duties, and create space to contribute where you can make the most impact.

A short, integrative metaphor
- The inner citadel gates stay open for what matters; every boundary is a carefully weighed gate you close to protect the garden of your meaningful work. Chop wood, carry water—mindful, purposeful labor that keeps your life clear and your commitments trustworthy.

If you'd like, I can tailor this into a one-page personal protocol for you (including your top values, typical boundary scripts customized to your context, and a 7-day experiment plan)."""

    if enable_scout:
        synthesis += "\n\nWith Attachment Theory integrated: Also consider how your boundary-setting affects your attachment security and relationships. Practice boundaries that maintain connection while honoring your authentic needs."

    what_is_lost = [
        "Here are 2–4 specific aspects from each tradition that tend to be softened, diluted, or lost when that tradition is blended into a broader synthesis:",
        "Buddhism",
        "Root-illness diagnosis softened: The central claim that dukkha arises from craving and aversion (and that practice aims to uproot these roots) can be reduced to surface-level boundary management, missing the deeper analysis of craving as the engine of suffering.",
        "Non-attachment to outcomes diluted: Right intention and the discipline of not clinging to results may become pragmatic \"get this handled\" behavior, diminishing the transformative aim of letting go of the fruits of action."
    ]

    if enable_scout:
        what_is_lost.append("4) Attachment Theory's focus on relational healing and secure bonding patterns gets simplified into communication techniques rather than deep therapeutic work.")
    
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