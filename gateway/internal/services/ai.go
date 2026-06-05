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

	ollamaURL := "http://localhost:11434/api/generate"
	prompt := `You are an agricultural plant disease expert.

Analyze the uploaded crop image carefully.

Return ONLY a valid JSON object matching this structure exactly:
{
  "crop_detected": "Crop name",
  "disease": "Disease name (or 'Healthy')",
  "confidence": 95.0,
  "severity": "healthy", "warning", or "critical",
  "health_assessment": "Symptoms observed. If uncertain, say uncertain. Do not hallucinate.",
  "recommendations": [
    "Recommended pesticide: ...",
    "Organic treatment: ...",
    "Prevention methods: ..."
  ]
}`

	if req.CropHint != "" {
		prompt += fmt.Sprintf("\nHint: The farmer suspects this is a %s crop.", req.CropHint)
	}

	modelName := os.Getenv("OLLAMA_MODEL")
	if modelName == "" {
		modelName = "qwen2.5vl:7b" // Default to the Vision model
	}

	payload := map[string]interface{}{
		"model":  modelName,
		"prompt": prompt,
		"images": []string{base64Str},
		"format": "json",
		"stream": false,
		"options": map[string]interface{}{
			"temperature": 0.2, // Low temp for more factual crop analysis
		},
	}
	
	payloadBytes, _ := json.Marshal(payload)
	httpReq, _ := http.NewRequest("POST", ollamaURL, bytes.NewBuffer(payloadBytes))
	httpReq.Header.Set("Content-Type", "application/json")
	
	client := &http.Client{Timeout: 300 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		log.Printf("Ollama HTTP Error: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	bodyBytes, _ := ioutil.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		log.Printf("Ollama API Error (Status %d): %s", resp.StatusCode, string(bodyBytes))
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

	var ollamaResp struct {
		Response string `json:"response"`
	}
	json.Unmarshal(bodyBytes, &ollamaResp)

	var aiData struct {
		CropDetected     string  `json:"crop_detected"`
		IsHealthy        bool    `json:"is_healthy"`
		Disease          string  `json:"disease"`
		Severity         string  `json:"severity"`
		Confidence       float64 `json:"confidence"`
		HealthAssessment string  `json:"health_assessment"`
	}

	aiData.CropDetected = "Unknown Crop"
	aiData.Severity = "warning"
	aiData.Confidence = 75.0
	aiData.HealthAssessment = "Unable to fully analyze the image. Please try again."
	_ = json.Unmarshal([]byte(ollamaResp.Response), &aiData)

	finalResp := map[string]interface{}{
		"crop_detected":     aiData.CropDetected,
		"health_assessment": aiData.HealthAssessment,
		"severity":          aiData.Severity,
		"ai_confidence":     aiData.Confidence,
		"success":           true,
	}

	return json.Marshal(finalResp)
}

// CallOllamaForDocument calls the local Ollama instance to extract text and analyze a crop document (e.g. fertilizer label).
func CallOllamaForDocument(req models.ScanRequest) ([]byte, error) {
	base64Str := req.ImageBase64
	if idx := strings.Index(base64Str, ","); idx != -1 {
		base64Str = base64Str[idx+1:]
	}

	ollamaURL := "http://localhost:11434/api/generate"
	prompt := `You are an expert agricultural assistant. Analyze the uploaded image of a document (e.g., pesticide label, fertilizer bag, prescription, or soil report).
Extract the key information and return ONLY a valid JSON object matching this exact structure:
{
  "document_type": "Type of document (e.g. Fertilizer Label)",
  "extracted_text": "A brief summary of the main text/instructions found on the label",
  "warnings": "Any safety warnings or precautions",
  "usage_instructions": "How to use the product, dosage, timing, etc.",
  "active_ingredients": "List of active ingredients"
}`

	modelName := os.Getenv("OLLAMA_MODEL")
	if modelName == "" {
		modelName = "qwen2.5vl:7b" // Default to the Vision model
	}

	payload := map[string]interface{}{
		"model":  modelName,
		"prompt": prompt,
		"images": []string{base64Str},
		"format": "json",
		"stream": false,
		"options": map[string]interface{}{
			"temperature": 0.1, // Very low temp for OCR/Extraction
		},
	}
	
	payloadBytes, _ := json.Marshal(payload)
	httpReq, _ := http.NewRequest("POST", ollamaURL, bytes.NewBuffer(payloadBytes))
	httpReq.Header.Set("Content-Type", "application/json")
	
	client := &http.Client{Timeout: 300 * time.Second}
	resp, err := client.Do(httpReq)
	if err != nil {
		log.Printf("Ollama HTTP Error: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	bodyBytes, _ := ioutil.ReadAll(resp.Body)
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("Ollama API Error: %s", string(bodyBytes))
	}

	var ollamaResp struct {
		Response string `json:"response"`
	}
	json.Unmarshal(bodyBytes, &ollamaResp)

	return []byte(ollamaResp.Response), nil
}
