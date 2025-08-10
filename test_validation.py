#!/usr/bin/env python3
"""Test script to validate model validation rules work correctly."""

from pydantic import ValidationError
from ai_journal.models import (
    Framework, JournalEntry, Perspective, AgreementItem, AgreementStance
)

def test_validation_rules():
    print("Testing validation rules...\n")
    
    # Test 1: OTHER framework requires other_framework_name
    try:
        invalid_perspective = Perspective(
            framework=Framework.OTHER,
            # Missing other_framework_name!
            core_principle_invoked="Some principle",
            challenge_framing="Some challenge",
            practical_experiment="Some experiment", 
            potential_trap="Some trap",
            key_metaphor="Some metaphor"
        )
        print("❌ Should have failed: OTHER framework without other_framework_name")
    except ValidationError as e:
        print("✓ Correctly rejected OTHER framework without other_framework_name")
        print(f"  Error: {e.errors()[0]['msg']}")
    
    # Test 2: OTHER framework with other_framework_name should work
    try:
        valid_perspective = Perspective(
            framework=Framework.OTHER,
            other_framework_name="Confucianism",
            core_principle_invoked="Some principle",
            challenge_framing="Some challenge", 
            practical_experiment="Some experiment",
            potential_trap="Some trap",
            key_metaphor="Some metaphor"
        )
        print("✓ Correctly accepted OTHER framework with other_framework_name")
    except ValidationError:
        print("❌ Should have accepted OTHER framework with other_framework_name")
    
    # Test 3: AgreementItem with same frameworks should fail
    try:
        invalid_agreement = AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.BUDDHISM,  # Same as framework_a!
            stance=AgreementStance.AGREE
        )
        print("❌ Should have failed: Same frameworks in AgreementItem")
    except ValidationError as e:
        print("✓ Correctly rejected same frameworks in AgreementItem")
        print(f"  Error: {e.errors()[0]['msg']}")
    
    # Test 4: AgreementItem with different frameworks should work
    try:
        valid_agreement = AgreementItem(
            framework_a=Framework.BUDDHISM,
            framework_b=Framework.STOICISM,
            stance=AgreementStance.NUANCED
        )
        print("✓ Correctly accepted different frameworks in AgreementItem")
    except ValidationError:
        print("❌ Should have accepted different frameworks in AgreementItem")
    
    # Test 5: Empty journal entry should fail
    try:
        invalid_journal = JournalEntry(text="")
        print("❌ Should have failed: Empty journal entry text")
    except ValidationError as e:
        print("✓ Correctly rejected empty journal entry text")
        print(f"  Error: {e.errors()[0]['msg']}")
    
    print("\n✅ All validation tests passed!")

if __name__ == "__main__":
    test_validation_rules()