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
        core_principle_invoked="Craving (tanha) and aversion drive the pattern of saying yes to tasks you don't want, and through dependent origination this leads to ongoing suffering (dukkha). The Buddhist path offers a corrective: cultivate right intention, right effort, right speech, and right action to respond with truthful, compassionate boundaries that reduce suffering.",
        challenge_framing="Generosity without boundaries isn't virtue—it's fear wearing a halo.",
        practical_experiment="Pause for three mindful breaths before replying to any new work request today, then respond with a clear boundary (e.g., 'I can take this on starting next week' or 'I can help in X other way').",
        potential_trap="Mindfulness can be misused as resignation or cynicism; the Middle Way requires wise engagement—avoid both avoidance of duties and forcing yourself beyond your limits.",
        key_metaphor="Mind like a garden: prune craving with mindful intention so the fruits of work can truly ripen."
    )
    
    stoic = Perspective(
        framework=Framework.STOICISM,
        other_framework_name=None,
        core_principle_invoked="The Dichotomy of Control applies here: you cannot control others' demands, only your own assent and actions. Virtue demands aligning choices with duty, distinguishing what is a true good from mere preference.",
        challenge_framing="Saying yes to every request is not generosity; it's surrendering your agency to external demands and drifting away from virtue.",
        practical_experiment="Action: For the next 24 hours, before committing to a new task, pause for 60 seconds to reflect and then use a boundary script: 'I appreciate the offer; I can't take this on right now. If it's important, we can revisit in 24 hours after I review my priorities.' Apply it at least once today.",
        potential_trap="Used improperly, boundary-setting can become rigidity or avoidance of responsibility. Ensure you still act courageously and justly when help is truly needed, and that you aren't shrinking from duties out of fear of conflict.",
        key_metaphor="Let your assent be a gate, not a revolving door."
    )
    
    existentialist = Perspective(
        framework=Framework.EXISTENTIALISM,
        other_framework_name=None,
        core_principle_invoked="Existence precedes essence: you are free to create meaning, and with that freedom comes responsibility for every choice. Saying yes to what you don't want is often bad faith—you are authoring your life, or surrendering it to someone else.",
        challenge_framing="If you keep saying yes to what you don't want, you're authoring a life you didn't choose; reclaim your freedom by naming the cost of each acquiescence.",
        practical_experiment="Today, decline one non-essential task you routinely agree to, with a brief, honest note explaining your boundary or proposing a concrete alternative time, then journal how it felt before and after.",
        potential_trap="Misuse your freedom as impulsive neglect of duties; boundaries that punish others or sever all accountability can backfire—authentic living requires honesty about both your desires and responsibilities.",
        key_metaphor="Freedom is the chisel; your life is marble you carve into meaning."
    )
    
    neoadlerian = Perspective(
        framework=Framework.NEOADLERIANISM,
        other_framework_name=None,
        core_principle_invoked="Task separation reveals you're taking responsibility for others' disappointment. The courage to be disliked means accepting that saying no may upset people, but their feelings about your boundaries are their task, not yours.",
        challenge_framing="You lack the courage to be disliked—you're prioritizing others' approval over your own authentic contribution.",
        practical_experiment="Practice separating your task (deciding what work to take on) from their task (their feelings about your decision). Say no to one request today with a clear explanation but without over-apologizing or managing their reaction.",
        potential_trap="Using task separation to justify callousness or avoid genuine community feeling. The goal is healthy interdependence, not isolation.",
        key_metaphor="A gardener tends their own plot, not the neighbor's reaction to the fence."
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
            stance=AgreementStance.NUANCED,
            notes="Both systems advocate prudent boundary-setting and avoiding unbounded conformity to external demands: Buddhism emphasizes reducing suffering via mindful intention (craving/aversion) and the Middle Way, while Stoicism emphasizes the Dichotomy of Control and virtuous assent. Their differences are metaphysical and normative rather than practical conflict, yielding a nuanced alignment."
        ),
        AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.EXISTENTIALISM,
            stance=AgreementStance.NUANCED,
            notes="Both challenge unreflective conformity and favor authentic boundary-setting. Buddhism grounds ethics in compassion and suffering relief; existentialism centers on radical freedom and meaning-making. They align on the value of deliberate response to choice, but differ in ultimate aims and metaphysical commitments, making the agreement nuanced."
        ),
        AgreementItem(
            framework_a=Framework.EXISTENTIALISM,
            framework_b=Framework.STOICISM,
            stance=AgreementStance.NUANCED,
            notes="Both foreground personal responsibility and control of one's responses. Stoicism emphasizes virtue, duty, and acceptance of a rational order; existentialism emphasizes freedom and meaning creation. They align in practical ethics of boundaries but diverge in metaphysical foundations and endpoints, yielding a nuanced agreement."
        ),
        AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.NEOADLERIANISM,
            stance=AgreementStance.AGREE,
            notes="Both emphasize releasing attachment to others' opinions and reactions. Buddhism through non-attachment and compassion, NeoAdlerianism through task separation and the courage to be disliked."
        ),
        AgreementItem(
            framework_a=Framework.EXISTENTIALISM,
            framework_b=Framework.NEOADLERIANISM,
            stance=AgreementStance.AGREE,
            notes="Both champion individual courage against social pressure and authentic self-expression. Existentialism through radical freedom and responsibility, NeoAdlerianism through individual psychology and task separation."
        ),
        AgreementItem(
            framework_a=Framework.STOICISM,
            framework_b=Framework.NEOADLERIANISM,
            stance=AgreementStance.NUANCED,
            notes="Both emphasize personal responsibility and focusing on what you can control. Stoicism grounds this in virtue ethics and rational duty, while NeoAdlerianism focuses on individual purpose and social contribution. They differ in their approach to community obligations."
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
    
    tension_explanation = """Below are 4 substantive tension points where the four core frameworks diverge in their foundational assumptions, methods, or goals. For each, I spell out the frameworks involved, the core philosophical principles driving the disagreement, and why the differences matter in practical terms.

Tension Point 1: The status and purpose of boundary-setting in moral life (Buddhism vs. Stoicism vs. Existentialism vs. NeoAdlerianism)

- Frameworks involved:
  - Buddhism
  - Stoicism
  - Existentialism
  - NeoAdlerianism

- Core principles driving the disagreement:
  - Buddhism: Boundaries arise from recognizing craving (tanha) and its role in sustaining suffering. The ethical aim is to minimize suffering through right intention, right effort, right speech, and right action; compassionate boundaries are virtuous insofar as they reduce dukkha and align with the Middle Way.
  - Stoicism: Boundaries are an application of the Dichotomy of Control. You cannot control others' demands; you can control your assent and actions. Virtue requires aligning responses with duty and reason, not bending to every external pressure. Boundaries are a rational management of what is genuinely within your power.
  - Existentialism: Boundaries are acts of authentic self-authorship. Existence precedes essence, so you author meaning through choices. Saying yes to things you don't want is often bad faith unless you deliberately choose the boundary as a free, responsible act. Boundaries are about conscious creation of a life you acknowledge as yours.
  - NeoAdlerianism: Boundaries are applications of task separation—clarifying what is your task versus others' tasks. The courage to be disliked means accepting that your boundaries may disappoint others, but managing their feelings about your choices is their task, not yours. Boundaries serve individual purpose and social contribution.

- Why these differences matter practically:
  - They lead to different justifications for the same practical move (declining a request). Buddhism would justify a boundary as a means to reduce suffering and cultivate right action; Stoicism would justify it as safeguarding virtue and rational freedom within the realm of control; Existentialism would justify it as an authentic assertion of personal meaning, even if uncomfortable for others.
  - The risk profiles differ: Buddhism worries about becoming driven by fear or resentment masked as generosity; Stoicism worries about becoming rigid or cowardly in the face of real duties; Existentialism worries about acting in bad faith if boundaries are chosen reflexively or to avoid responsibility; NeoAdlerianism worries about using task separation to justify callousness or abandoning genuine community feeling.
  - In practice, this translates into how you phrase a decline (compassionate and non-harming vs. firm and duty-centered vs. honest about authorship and costs vs. clear task separation) and how you calibrate the boundary's breadth (limiting burnout vs. preserving relational trust vs. maintaining existential integrity vs. enabling authentic social contribution).

Tension Point 2: Freedom and agency under different metaphysical pictures (Buddhism vs. Stoicism vs. Existentialism)

- Frameworks involved:
  - Buddhism
  - Stoicism
  - Existentialism

- Core principles driving the disagreement:
  - Buddhism: Freedom is freedom from craving and ignorance within a causal, interdependent fabric (pratitya-samutpada). Personal agency exists but is conditioned; liberation involves transforming mental causes (skilful intentions) and attenuating attachment.
  - Stoicism: Freedom is internal sovereignty within the constraints of a rational universe. You may not control external events; you can and should control your assent to impressions and your virtuous response. Freedom is about aligning with nature and reason, not about absolute libertarian autonomy.
  - Existentialism: Freedom is radical and absolute in the sense that individuals always have the power to choose and to project meaning. With this comes responsibility and anxiety (anguish) because choices carve the course of a life, regardless of conditioning.

- Why these differences matter practically:
  - They shape how you experience pressure from demands. Buddhism emphasizes transforming relations to craving so you respond with less reactivity; Stoicism emphasizes disciplined interior governance so you neither panic nor capitulate but act in accord with virtue; Existentialism emphasizes owning the cost of choices and continuing to choose despite anxiety.
  - They influence attitudes toward determinism, responsibility, and resilience. If you lean Buddhist, you might center cultivation of intention to soften reactive responses; if you lean Stoic, you might center a calm, principled veto of non-essential commitments; if you lean Existentialist, you might emphasize transparent commitment to a chosen path even when it entails conflict or cost.
  - In group dynamics or workplaces, these differences can produce distinct negotiation styles: compassionate boundary-setting with awareness of craving (Buddhism), calm principled refusals with attention to duties (Stoicism), or explicit, self-authored boundaries that state a chosen meaning (Existentialism).

Tension Point 3: Universality of virtue vs. authenticity and meaning-making (Buddhism vs. Stoicism vs. Existentialism)

- Frameworks involved:
  - Buddhism
  - Stoicism
  - Existentialism

- Core principles driving the disagreement:
  - Buddhism: There are universal ethical guidelines aimed at reducing suffering—things like non-harm, truthful speech, compassionate action, and the cultivation of right intention. These are not mere preferences but part of a cultivated path toward awakening.
  - Stoicism: There are universal virtues (e.g., wisdom, justice, courage, temperance) aligned with rational nature. Virtue is sufficient for eudaimonia; external goods or opinions don't determine virtue.
  - Existentialism: There are no pre-given universal norms that determine meaning. Ethics are contingent on individual choices and authenticity. What matters is that you own your decisions and create meaning through them, even if that means redefining or resisting external norms.

- Why these differences matter practically:
  - Decision-making under conflict or ambiguity: Buddhism offers a universal ethical framework to adjudicate actions for the sake of reducing suffering; Stoicism offers a universal, rational basis to assess whether a response upholds virtue despite external pressure; Existentialism offers a framework where boundaries and duties are chosen rather than dictated, emphasizing personal responsibility and authenticity.
  - The style of justification and accountability differs. A Buddhist justification might appeal to compassion and the elimination of craving; a Stoic justification might appeal to rational duty and social harmony; an existentialist justification might appeal to personal integrity and disclosure of costs.
  - In real terms, this affects how you validate your boundary decisions: are they morally compelled by universal precepts, by rational virtue and social role, or by a personally authored life project?

Concluding note
- These tensions are not simply debates about good manners or self-care. They reveal deep divergences about what counts as the good life, what freedom consists in, and what grounds normative guidance. The Buddhist framework grounds ethics in the alleviation of suffering within interdependent causality; Stoicism grounds ethics in rational nature and virtue as the path to a tranquil, right-living life; Existentialism grounds ethics in radical freedom and personal responsibility to author meaning. Understanding these tensions can illuminate why a given boundary is defended in different ways and why each tradition offers unique tools for navigating demanding work, while also exposing potential blind spots (e.g., over-identification with boundaries, fear masquerading as detachment, or reckless self-authorship without accountability).

If you'd like, I can map these tensions onto your specific experiments (three mindful breaths, boundary phrasing, the "gate" metaphor) and show how each framework would justify, critique, or modify those practices."""

    if enable_scout:
        tension_explanation += "\n\nWith the addition of Attachment Theory, we see further tensions around whether emotional regulation should prioritize individual virtue (Stoic), interdependent compassion (Buddhist), authentic self-expression (Existentialist), or secure relational bonding (Attachment Theory)."

    tensions = [
        TensionPoint(
            frameworks=frameworks_in_tension,
            explanation=tension_explanation
        )
    ]
    
    synthesis = """A unified, practical synthesis: Boundaries that honor craving, duty, and freedom

Core idea
Treat boundary-setting as a single, holistic practice that blends Buddhist mindful discernment, Stoic freedom from what you cannot control, and existential responsibility for the life you choose to live. Boundaries are not walls or excuses; they are compassionate, courageous, and authentic actions that reduce suffering, protect agency, and shape meaning.

Three integrated principles (one sentence each)
- Buddhist: Pause craving and reactivity, orient toward truthful, compassionate action, and practice the Middle Way to avoid both over-taxing yourself and neglecting duties.
- Stoic: Focus on what you can control—your assent and your actions—using clear boundaries to preserve virtue and responsibility.
- Existentialist: You author your life with every choice; saying yes to what you don't want is a negation of freedom—truthful boundaries reclaim meaning and agency.

Integrated practice framework (one workflow, three traditions in harmony)
1) Pause and clear craving (Buddhist core)
- When a new task request comes in, pause for three mindful breaths.
- Observe urges: "I want to say yes because of fear, guilt, or desire to please."

2) Check control and duty (Stoic core)
- Ask these quick questions:
  - Is this fully within my control to fulfill well?
  - Is this a true good or only a preference or convenience?
  - What is my real duty in this moment (compassionate care, not burning out, alignment with commitments)?
- If the answer is "not now" or "not this way," proceed to boundary communication.

3) Name meaning and responsibility (Existentialist core)
- Remember: existence precedes essence. You are choosing how to shape your life, not passively acquiescing to every demand.
- State the boundary in a way that preserves meaning: you are crafting a life you can live with integrity, including the costs.

4) Respond with compassionate clarity (integrated action)
- Deliver a boundary that is honest, specific, and constructive. You may accept with conditions or decline with alternatives.
- Use a boundary script that aligns with your situation (see templates below).

5) Reflect and refine (all three traditions together)
- After acting, journal or note:
  - How did the boundary reduce suffering or protect your integrity?
  - Was the act aligned with virtue (courage, temperance, justice) and authenticity?
  - How did it feel to exercise freedom and responsibility?

Practical boundary scripts (ready-to-use templates)
- If you can take it on later:
  - "I can take this on starting next week. If it's important, we can revisit after I review my priorities."
- If you can help in another way:
  - "I can help in X alternative way or with Y task at Z time."
- If you must decline:
  - "I appreciate the offer. I can't take this on right now due to current commitments. If it's urgent, let's set a check-in in 24 hours to reassess."
- If it's urgent but you're near capacity:
  - "I want to give this proper attention. I can't start today, but I can begin with a small, defined portion at [time], then reassess."
- If you need to protect your own limits:
  - "I'm prioritizing [core duty or well-being] today. I'll be happy to discuss this after [date/time]."

Three integrated metaphors to keep in view
- Garden (Buddhist): Prune craving with mindful intention so the fruits of work can ripen.
- Gate (Stoic): Let your assent be a gate, not a revolving door—guard access to your time and energy.
- Marble and chisel (Existentialist): You carve a life of meaning through deliberate, responsible shaping of choices.

Common traps and safeguards (and how this synthesis handles them)
- Mindfulness turned into resignation: Use mindful action (pause, reflect, decide) to engage rather than withdraw; choose boundary timing and content that serve constructive outcomes.
- Boundaries as rigidity: Combine with compassionate duty; if help is truly needed, act bravely and appropriately, not out of fear of conflict.
- Over-assertion or refusal of all demands: Always test whether the situation calls for courage, just action, or a strategic decline. When in doubt, seek a temporary boundary (delay, partial commitment) rather than a full withdrawal.
- Boundary punishment or punishment avoidance: Boundaries are tools for meaningful action, not weapons. Communicate intent to preserve relationships and shared goals.

A compact implementation plan (21 days to habit)
- Week 1: Practice the three-breath pause before any new task request. Start with one or two requests per day.
- Week 2: Add the 60-second Stoic reflection (control, duty, true good vs preference) before committing.
- Week 3: Use an existential framing: name the boundary, explain the personal meaning, and propose a concrete alternative or timeframe.
- Daily habit check: Record a brief note: what boundary you set, what you said, and how it felt. Note any impact on well-being and relationships.
- Week 4+: Review patterns. Adjust scripts to fit your context. If you notice recurring requests, consider system changes (e.g., setting specific office hours, delegating routine tasks).

Alignment map: how the traditions complement each other
- Buddhism provides a compassionate, mindful foundation to recognize craving and to act with intention (the Middle Way).
- Stoicism provides a precise, controllable framework for decision-making and the virtue-based standard for action.
- Existentialism grounds the practice in personal freedom and responsibility, ensuring boundaries are chosen and meaningful rather than imposed or robotic.

How this synthesis respects differences
- It respects Buddhist emphasis on reducing suffering through mindful action and the Middle Way, while translating it into practical boundary-setting that does not become resignation.
- It respects Stoic insistence on the Dichotomy of Control by making the boundary a tool to govern one's assent and actions, not others' demands.
- It respects existentialist insistence on freedom and authenticity by making each boundary a conscious, value-driven choice that shapes one's life narrative.

A concise one-page guide you can carry
- Before replying to any new task: three mindful breaths -> observe craving.
- Quick check (control, duty, true good): is it mine to fulfill now? If yes, proceed with a boundary-refined approach; if no, consider alternatives or a delay.
- Boundary script: choose one of the templates above; add a brief rationale if helpful for the other party.
- After-action reflection: 1-minute write-up on alignment with virtue, freedom, and meaning.

This unified approach gives you a practical, honest, and learnable way to say yes or no in ways that reduce suffering, preserve agency, and foster a meaningful life. If you want, I can tailor the scripts to specific contexts (team, client, family) and provide a printable daily checklist."""

    if enable_scout:
        synthesis += "\n\nWith Attachment Theory integrated: Also consider how your boundary-setting affects your attachment security and relationships. Practice boundaries that maintain connection while honoring your authentic needs."

    what_is_lost = [
        "Here are 4 specific aspects that tend to be softened or diminished when Buddhism, Stoicism, and Existentialism are blended into a single synthesis:",
        "1) Existential self-authorship and meaning-making",
        "What's lost: The urgent sense that you are the author of your own life, and that meaning must be actively created through choices you fully own (existentialism).",
        "Why it softens in synthesis: boundary-setting and acceptance (Buddhist and Stoic tones) can shift focus from radical personal creation to managing duties, duties-bound boundaries, or accepted path. The edgy impulse to redefine meaning through bold, costly choices may be dulled.",
        "2) Buddhist liberation and the radical nature of non-attachment",
        "What's lost: The transformative goal of liberation (nirvana) that goes beyond practical boundary management to fundamentally transform one's relationship to suffering and craving.",
        "3) Stoic rational discipline and virtue as the sole good",
        "What's lost: The uncompromising focus on virtue as the only true good, with external circumstances being genuinely indifferent rather than balanced with other concerns.",
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