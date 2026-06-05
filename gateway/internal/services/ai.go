package services

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
	"smarfa-gateway/internal/models"
)

var Rdb *redis.Client
var ctx = context.Background()

func InitRedis() {
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "localhost:6379"
	}
	Rdb = redis.NewClient(&redis.Options{
		Addr: redisAddr,
	})
	if err := Rdb.Ping(ctx).Err(); err != nil {
		log.Printf("Warning: Redis not connected (%v). Falling back to synchronous HTTP only.", err)
	} else {
		log.Println("Connected to Redis successfully")
	}
}

// CallPythonAIService sends the payload directly to the internal Python FastAPI microservice.
func CallPythonAIService(req models.ScanRequest) ([]byte, error) {
	aiURL := os.Getenv("AI_SERVICE_URL")
	if aiURL == "" {
		aiURL = "http://localhost:8001/analyze_crop"
	}

	payload, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}

	httpReq, err := http.NewRequest("POST", aiURL, bytes.NewBuffer(payload))
	if err != nil {
		return nil, err
	}
	httpReq.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("AI Service returned status %d", resp.StatusCode)
	}

	return ioutil.ReadAll(resp.Body)
}

// CallOllamaDirectly calls the local Ollama instance directly using the Qwen Vision model.
func CallOllamaDirectly(req models.ScanRequest) ([]byte, error) {
	// Strip the "data:image/jpeg;base64," prefix if it exists
	base64Str := req.ImageBase64
	if idx := strings.Index(base64Str, ","); idx != -1 {
		base64Str = base64Str[idx+1:]
	}

	// Check for OpenAI API key
	openAIKey := os.Getenv("OPENAI_API_KEY")
	if openAIKey == "" {
		return nil, fmt.Errorf("OPENAI_API_KEY is missing")
	}

	modelName := "gpt-4o"

	openAIURL := "https://api.openai.com/v1/chat/completions"
	
	locationStr := ""
	if req.Lat != 0 && req.Lon != 0 {
		locationStr = fmt.Sprintf(" The user is located at coordinates Lat: %f, Lon: %f. Factor in regional diseases and weather for this area into your agronomy context.", req.Lat, req.Lon)
	}

	prompt := `You are an expert Plant & Agricultural AI Assistant with deep knowledge of crops, fruits, flowers, and ornamental plants.
Analyze the uploaded plant image in incredible detail using a structured diagnostic approach.` + locationStr + `

CRITICAL INSTRUCTIONS:
1. You MUST identify the exact plant type — whether it is a CROP (wheat, rice, corn), a FRUIT plant (mango, papaya, strawberry, watermelon), a FLOWER/ORNAMENTAL plant (rose, marigold, jasmine, sunflower, hibiscus), or any other plant.
2. Do NOT confuse plant types. Look closely at leaf shape, flower colour, stem structure, fruit presence, and growth form.
3. Identify diseases, pests, and nutrient deficiencies specific to that plant type.
4. If the image shows a flower plant, provide flower-specific disease and care advice.
5. If the image shows a fruit plant, provide fruit-specific disease, ripening, and harvest advice.
6. If you are unsure of the species, state the most probable genus. Only use 'Unknown Plant' as a last resort.

Return ONLY a valid JSON object. Fill each field based on the actual image — do NOT copy example values literally:
{
  "crop_detected": "Common Name (Scientific Name)",
  "plant_type": "one of: crop | fruit | flower | ornamental | herb | vegetable",
  "severity": "one of: healthy | warning | critical",
  "ai_confidence": 0.0,
  "health_assessment": "2-sentence summary of overall plant health.",
  "structured": {
    "final_crop": "Common plant name only",
    "plant_category": "Crop / Fruit / Flower / Ornamental / Herb / Vegetable",
    "disease": {
      "name": "Disease name or 'No disease detected'",
      "confidence": "High / Medium / Low",
      "cause": "Fungal / Bacterial / Viral / Pest / Nutrient Deficiency / Physiological",
      "severity": "Low / Medium / High / Critical"
    },
    "safety_check": {
      "verified": true,
      "chemical": "Active ingredient name only",
      "safety_class": "Organic / Synthetic / Restricted",
      "eco_status": "e.g. Safe for bees",
      "compliance_details": "Pre-harvest interval or local notes."
    },
    "treatment": {
      "organic": "Organic treatment steps.",
      "chemical": "ONLY THE INGREDIENT NAME — 1 to 3 words max, e.g. Tricyclazole or Copper Oxychloride or Neem Oil. NO sentences. NO dosage here.",
      "dosage": "Mixing ratio only, e.g. 0.6g per Liter of water.",
      "prevention": "Cultural prevention steps.",
      "irrigation_adjustment": "Increase / Decrease / Maintain.",
      "soil_correction": "Fertilizer or pH fix needed.",
      "flower_care": "Pruning or bloom tips if flower plant, else omit.",
      "fruit_care": "Ripening or harvest tips if fruit plant, else omit."
    },
    "product": {
      "commercial_name": "Most common Indian brand name for this treatment, e.g. Beam 75 WP or Dithane M-45",
      "active_ingredient": "Pure ingredient keyword only, e.g. Tricyclazole",
      "amazon_search_term": "Exact search term to find this product on Amazon India",
      "alternatives": ["Alternative Indian Brand 1", "Alternative Indian Brand 2"]
    },
    "agent_logs": {
      "pathology_agent": "Visual symptoms observed.",
      "agronomy_agent": "Environmental factors.",
      "safety_agent": "Safety precautions."
    }
  }
}`

	payload := map[string]interface{}{
		"model": modelName,
		"messages": []map[string]interface{}{
			{
				"role": "user",
				"content": []map[string]interface{}{
					{"type": "text", "text": prompt},
					{"type": "image_url", "image_url": map[string]string{"url": "data:image/jpeg;base64," + base64Str}},
				},
			},
		},
		"response_format": map[string]string{"type": "json_object"},
		"temperature":     0.2,
	}
	
	payloadBytes, _ := json.Marshal(payload)
	httpReq, _ := http.NewRequest("POST", openAIURL, bytes.NewBuffer(payloadBytes))
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+openAIKey)
	
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		log.Printf("OpenAI HTTP Error: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	bodyBytes, _ := ioutil.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		log.Printf("OpenAI API Error (Status %d): %s", resp.StatusCode, string(bodyBytes))
		var aiData struct {
			CropDetected     string  `json:"crop_detected"`
			IsHealthy        bool    `json:"is_healthy"`
			Disease          string  `json:"disease"`
			Severity         string  `json:"severity"`
			Confidence       float64 `json:"confidence"`
			HealthAssessment string  `json:"health_assessment"`
		}
		aiData.CropDetected = "Error"
		aiData.Severity = "critical"
		aiData.Confidence = 0.0
		aiData.HealthAssessment = fmt.Sprintf("AI Model Error: %s", string(bodyBytes))
		
		finalResp := map[string]interface{}{
			"crop_detected":     aiData.CropDetected,
			"health_assessment": aiData.HealthAssessment,
			"severity":          aiData.Severity,
			"ai_confidence":     aiData.Confidence,
			"success":           true,
		}
		return json.Marshal(finalResp)
	}

	var openAIResp struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	json.Unmarshal(bodyBytes, &openAIResp)
	
	if len(openAIResp.Choices) == 0 {
		return nil, fmt.Errorf("No text returned from OpenAI")
	}
	
	responseText := openAIResp.Choices[0].Message.Content

	var finalResp map[string]interface{}
	
	err = json.Unmarshal([]byte(responseText), &finalResp)
	if err != nil {
		finalResp = map[string]interface{}{
			"crop_detected":     "Unknown Crop",
			"severity":          "warning",
			"ai_confidence":     75.0,
			"health_assessment": "AI responded, but the output could not be parsed. Please try again.",
			"success":           true,
		}
	} else {
		finalResp["success"] = true
	}

	return json.Marshal(finalResp)
}

// CallOllamaForDocument calls the local Ollama instance to extract text and analyze a crop document (e.g. fertilizer label).
func CallOllamaForDocument(req models.ScanRequest) ([]byte, error) {
	base64Str := req.ImageBase64
	if idx := strings.Index(base64Str, ","); idx != -1 {
		base64Str = base64Str[idx+1:]
	}

	openAIKey := os.Getenv("OPENAI_API_KEY")
	if openAIKey == "" {
		return nil, fmt.Errorf("OPENAI_API_KEY is missing")
	}

	modelName := "gpt-4o"
	openAIURL := "https://api.openai.com/v1/chat/completions"
	
	prompt := `You are an expert agricultural assistant. Analyze the uploaded image of a document (e.g., pesticide label, fertilizer bag, prescription, or soil report).
Extract the key information and return ONLY a valid JSON object matching this exact structure:
{
  "document_type": "Type of document (e.g. Fertilizer Label)",
  "extracted_text": "A brief summary of the main text/instructions found on the label",
  "warnings": "Any safety warnings or precautions",
  "usage_instructions": "How to use the product, dosage, timing, etc.",
  "active_ingredients": "List of active ingredients"
}`

	payload := map[string]interface{}{
		"model": modelName,
		"messages": []map[string]interface{}{
			{
				"role": "user",
				"content": []map[string]interface{}{
					{"type": "text", "text": prompt},
					{"type": "image_url", "image_url": map[string]string{"url": "data:image/jpeg;base64," + base64Str}},
				},
			},
		},
		"response_format": map[string]string{"type": "json_object"},
		"temperature":     0.1,
	}
	
	payloadBytes, _ := json.Marshal(payload)
	httpReq, _ := http.NewRequest("POST", openAIURL, bytes.NewBuffer(payloadBytes))
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+openAIKey)
	
	client := &http.Client{Timeout: 60 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		log.Printf("OpenAI HTTP Error: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	bodyBytes, _ := ioutil.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("OpenAI API Error: %s", string(bodyBytes))
	}

	var openAIResp struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	json.Unmarshal(bodyBytes, &openAIResp)

	if len(openAIResp.Choices) == 0 {
		return nil, fmt.Errorf("No text returned from OpenAI")
	}

	return []byte(openAIResp.Choices[0].Message.Content), nil
}
