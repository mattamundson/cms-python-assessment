import os
from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class JarvisBrain:
    def __init__(self, provider="openai"):
        self.provider = provider
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def reason(self, prompt, system_prompt="You are Jarvis, a helpful AI assistant."):
        if self.provider == "anthropic":
            return self._reason_anthropic(prompt, system_prompt)
        else:
            return self._reason_openai(prompt, system_prompt)

    def reason_with_tools(self, prompt, tools, system_prompt="You are Jarvis, a helpful AI assistant."):
        if self.provider == "openai":
            return self._reason_openai_tools(prompt, tools, system_prompt)
        else:
            # Fallback to normal reason if not supported or not implemented
            return self.reason(prompt, system_prompt)

    def _reason_anthropic(self, prompt, system_prompt):
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def _reason_openai(self, prompt, system_prompt):
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def _reason_openai_tools(self, prompt, tools, system_prompt):
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        return response.choices[0].message

if __name__ == "__main__":
    brain = JarvisBrain(provider="openai")
    print("Testing Brain (OpenAI)...")
    print(brain.reason("Hello Jarvis, give me a 1-sentence status update."))
