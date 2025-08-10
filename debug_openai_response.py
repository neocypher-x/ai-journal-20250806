#!/usr/bin/env python3
"""Debug script to examine OpenAI response structure."""

import asyncio
import os
from openai import AsyncOpenAI

async def test_openai_response():
    """Test a simple OpenAI call to see response structure."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return
    
    client = AsyncOpenAI(api_key=api_key)
    
    try:
        print("🔍 Testing simple OpenAI API call...")
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say 'Hello, this is a test response!'"}
            ],
            max_completion_tokens=50
        )
        
        print("✅ Response received")
        print(f"Response type: {type(response)}")
        print(f"Response object: {response}")
        print(f"Choices: {response.choices}")
        print(f"Choice 0: {response.choices[0]}")
        print(f"Message: {response.choices[0].message}")
        print(f"Content: '{response.choices[0].message.content}'")
        print(f"Content type: {type(response.choices[0].message.content)}")
        print(f"Finish reason: {response.choices[0].finish_reason}")
        
        # Test the specific issue
        content = response.choices[0].message.content
        print(f"Content is None: {content is None}")
        print(f"Content length: {len(content) if content else 'N/A'}")
        if content:
            stripped = content.strip()
            print(f"Stripped content: '{stripped}'")
            print(f"Stripped length: {len(stripped)}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_openai_response())