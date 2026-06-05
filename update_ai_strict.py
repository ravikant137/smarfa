import re

with open("gateway/internal/services/ai.go", "r") as f:
    content = f.read()

old_prompt = """Analyze the uploaded crop image in incredible detail using a structured diagnostic approach.` + locationStr + `

Return ONLY a valid JSON object matching this EXACT structure:"""

new_prompt = """Analyze the uploaded crop image in incredible detail using a structured diagnostic approach.` + locationStr + `

CRITICAL INSTRUCTION: You MUST correctly identify the core crop type with 100% precision. Do NOT confuse wheat with rice. Look closely at the grain, leaf structure, and stem. If you are unsure, default to 'Unknown Crop' rather than guessing incorrectly.

Return ONLY a valid JSON object matching this EXACT structure:"""

content = content.replace(old_prompt, new_prompt)

with open("gateway/internal/services/ai.go", "w") as f:
    f.write(content)

print("Updated prompt strictness in ai.go")
