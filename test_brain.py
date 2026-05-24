from brain import JarvisBrain
import os

print("Testing OpenAI...")
try:
    brain_oa = JarvisBrain(provider="openai")
    print(brain_oa.reason("Hello"))
except Exception as e:
    print(f"OpenAI Failed: {e}")

print("\nTesting Anthropic...")
try:
    brain_ant = JarvisBrain(provider="anthropic")
    print(brain_ant.reason("Hello"))
except Exception as e:
    print(f"Anthropic Failed: {e}")
