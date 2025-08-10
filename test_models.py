#!/usr/bin/env python3
"""Test script to validate the updated models work correctly."""

from ai_journal.models import (
    Framework, AgreementStance, JournalEntry, Perspective, 
    Perspectives, AgreementItem, TensionPoint, Prophecy, 
    Reflection, ReflectionRequest, ReflectionResponse
)

def test_basic_models():
    # Test JournalEntry
    journal_entry = JournalEntry(text="I keep saying yes to work I don't want to do...")
    print(f"✓ JournalEntry created: {journal_entry.text[:50]}...")
    
    # Test Perspective with core framework
    buddhist_perspective = Perspective(
        framework=Framework.BUDDHISM,
        core_principle_invoked="This reflects attachment and craving causing suffering.",
        challenge_framing="You're clinging to approval.",
        practical_experiment="Practice saying 'let me get back to you' once today.",
        potential_trap="Confusing non-attachment with passivity.",
        key_metaphor="Like leaves floating by on a stream."
    )
    print(f"✓ Buddhist perspective created: {buddhist_perspective.framework}")
    
    # Test Perspective with OTHER framework
    other_perspective = Perspective(
        framework=Framework.OTHER,
        other_framework_name="Confucianism",
        core_principle_invoked="Harmony through fulfilling social roles and relationships.",
        challenge_framing="You may be neglecting your duties to relationships.",
        practical_experiment="Consider your obligations to family and community.",
        potential_trap="Rigid adherence to roles without flexibility.",
        key_metaphor="Like a tree rooted in fertile soil."
    )
    print(f"✓ Other framework perspective created: {other_perspective.other_framework_name}")
    
    # Test Perspectives collection
    perspectives = Perspectives(items=[buddhist_perspective, other_perspective])
    print(f"✓ Perspectives collection created with {len(perspectives.items)} items")
    
    # Test AgreementItem
    agreement = AgreementItem(
        framework_a=Framework.BUDDHISM,
        framework_b=Framework.STOICISM,
        stance=AgreementStance.NUANCED,
        notes="Both reduce reactivity; differ on metaphysics."
    )
    print(f"✓ AgreementItem created: {agreement.stance}")
    
    # Test TensionPoint
    tension = TensionPoint(
        frameworks=[Framework.BUDDHISM, Framework.EXISTENTIALISM],
        explanation="Non-self vs. authorship of meaning creates fundamental tension."
    )
    print(f"✓ TensionPoint created with {len(tension.frameworks)} frameworks")
    
    # Test Prophecy
    prophecy = Prophecy(
        agreement_scorecard=[agreement],
        tension_summary=[tension],
        synthesis="Practice present-moment awareness while taking responsibility for choices.",
        what_is_lost_by_blending=[
            "Existential urgency may be softened.",
            "Buddhist deconstruction may feel abstract without action."
        ]
    )
    print(f"✓ Prophecy created with {len(prophecy.what_is_lost_by_blending)} loss items")
    
    # Test complete Reflection
    reflection = Reflection(
        journal_entry=journal_entry,
        perspectives=perspectives,
        prophecy=prophecy
    )
    print(f"✓ Complete Reflection created")
    
    # Test API models
    request = ReflectionRequest(
        journal_entry=journal_entry,
        enable_scout=True
    )
    print(f"✓ ReflectionRequest created: enable_scout={request.enable_scout}")
    
    response = ReflectionResponse(reflection=reflection)
    print(f"✓ ReflectionResponse created")
    
    print("\n✅ All model tests passed!")

if __name__ == "__main__":
    test_basic_models()