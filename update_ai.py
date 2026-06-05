import re

with open("gateway/internal/services/ai.go", "r") as f:
    content = f.read()

# Replace prompt generation to include Lat/Lon
old_prompt = """	prompt := `You are an expert ChatGPT Agricultural Assistant.
Analyze the uploaded crop image in incredible detail using a structured diagnostic approach.

Return ONLY a valid JSON object matching this EXACT structure:"""

new_prompt = """	locationStr := ""
	if req.Lat != 0 && req.Lon != 0 {
		locationStr = fmt.Sprintf(" The user is located at coordinates Lat: %f, Lon: %f. Factor in regional diseases and weather for this area into your agronomy context.", req.Lat, req.Lon)
	}

	prompt := `You are an expert ChatGPT Agricultural Assistant.
Analyze the uploaded crop image in incredible detail using a structured diagnostic approach.` + locationStr + `

Return ONLY a valid JSON object matching this EXACT structure:"""

content = content.replace(old_prompt, new_prompt)

with open("gateway/internal/services/ai.go", "w") as f:
    f.write(content)

print("Updated ai.go prompt")
