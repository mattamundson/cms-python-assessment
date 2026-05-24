import os
import json
from anthropic import Anthropic
from openai import OpenAI
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class JarvisBrain:
    def __init__(self, provider=None):
        self.provider = provider or "openai"
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_AI_API_KEY"))
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

    def reason(self, prompt, system_prompt="You are Jarvis, a helpful AI assistant."):
        """Simple reasoning with fallback."""
        providers = ["openai", "anthropic", "google"]
        if self.provider in providers:
            providers.remove(self.provider)
            providers.insert(0, self.provider)
        
        last_error = None
        for p in providers:
            try:
                if p == "openai":
                    return self._reason_openai(prompt, system_prompt)
                elif p == "anthropic":
                    return self._reason_anthropic(prompt, system_prompt)
                elif p == "google":
                    return self._reason_google(prompt, system_prompt)
            except Exception as e:
                print(f"[Brain] {p.upper()} failed: {e}")
                last_error = e
                continue
        raise Exception(f"All AI providers failed. Last error: {last_error}")

    def chat_with_tools(self, messages, tools):
        """Unified chat method with tool support and fallback."""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )
            return "openai", response.choices[0].message, response.usage
        except Exception as e:
            print(f"[Brain] OpenAI Tools failed: {e}")
            
        try:
            # Gemini-specific Tool configuration
            declarations = []
            for t in tools:
                if t['type'] == 'function':
                    f = t['function']
                    # Ensure parameters are in the format Gemini likes
                    params = f.get('parameters', {"type": "object", "properties": {}})
                    declarations.append(genai.types.FunctionDeclaration(
                        name=f['name'],
                        description=f['description'],
                        parameters=params
                    ))
            
            tool_obj = genai.types.Tool(function_declarations=declarations)
            
            system_instruction = next((m['content'] for m in messages if m['role'] == 'system'), "")
            model_with_tools = genai.GenerativeModel("gemini-2.5-flash", 
                                                    tools=[tool_obj],
                                                    system_instruction=system_instruction)
            
            # Send the conversation history
            # For Gemini, we'll convert the last user message + context
            history = []
            for m in messages[:-1]:
                if m['role'] == 'user':
                    history.append({"role": "user", "parts": [m['content']]})
                elif m['role'] == 'assistant':
                    history.append({"role": "model", "parts": [m['content'] or ""]})
                # Tool roles are tricky to convert in one go, skipping for simplicity in this turn

            chat = model_with_tools.start_chat(history=history)
            last_msg = messages[-1]['content']
            response = chat.send_message(last_msg)
            
            class MockMessage:
                def __init__(self, content, tool_calls=None):
                    self.content = content
                    self.tool_calls = tool_calls
                    self.role = "assistant"

            class MockToolCall:
                def __init__(self, name, args, call_id):
                    self.id = call_id
                    self.function = type('obj', (object,), {'name': name, 'arguments': json.dumps(args)})

            tool_calls = []
            content = None
            
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.function_call:
                        args = {k: v for k, v in part.function_call.args.items()}
                        tc = MockToolCall(part.function_call.name, args, f"gem-{part.function_call.name}")
                        tool_calls.append(tc)
                    elif part.text:
                        content = part.text

            return "google", MockMessage(content, tool_calls), type('obj', (object,), {'prompt_tokens': 0, 'completion_tokens': 0})
        except Exception as e:
            print(f"[Brain] Google Tools failed: {e}")
            
        raise Exception("Failed to chat with tools using any provider.")

    def _reason_anthropic(self, prompt, system_prompt):
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text, response.usage

    def _reason_openai(self, prompt, system_prompt):
        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content, response.usage

    def _reason_google(self, prompt, system_prompt):
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=system_prompt)
        response = model.generate_content(prompt)
        return response.text, type('obj', (object,), {'prompt_tokens': 0, 'completion_tokens': 0})
