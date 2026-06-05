package api

import (
	"encoding/json"
	"log"

	"github.com/gofiber/fiber/v2"
	"smarfa-gateway/internal/models"
	"smarfa-gateway/internal/services"
)

// Mock Auth Handlers to unblock frontend
func HandleLogin(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"status": "login successful",
		"user_id": 1,
	})
}

func HandleRegister(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"status": "user registered",
		"id": 1,
	})
}

// Stubs for legacy frontend UI screens
func HandleGetEmptyList(c *fiber.Ctx) error {
	return c.JSON([]interface{}{})
}

func HandleGetSummary(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"health_score": 95,
		"week_summary": fiber.Map{
			"avg_temp": 24.5, "min_temp": 20, "max_temp": 28,
			"avg_moisture": 65, "min_moisture": 60,
			"avg_height": 12, "readings_count": 42,
			"alerts_count": 0, "alerts_total": 0,
		},
	})
}

func HandlePumpStatus(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"is_running": false,
		"current": fiber.Map{"reason": "Manual", "duration": 0},
		"recent_logs": []interface{}{},
	})
}

func HandleAIStatus(c *fiber.Ctx) error {
	return c.JSON(fiber.Map{
		"ollama": true,
		"models": []string{"llama3.1:latest"},
	})
}

func HandleScanRequest(c *fiber.Ctx) error {
	var req models.ScanRequest

	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"success": false,
			"message": "Invalid JSON payload",
		})
	}

	if req.ImageBase64 == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"success": false,
			"message": "image_base64 is required",
		})
	}

	log.Println("Routing request directly to Ollama Vision Model (Qwen2.5)...")
	resp, err := services.CallOllamaDirectly(req)
	if err != nil {
		log.Printf("Ollama Error: %v", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"success": false,
			"message": "AI processing failed",
		})
	}

	var aiResponse models.AIResponse
	if err := json.Unmarshal(resp, &aiResponse); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"success": false,
			"message": "Failed to parse AI response",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    aiResponse,
	})
}

// HandleLegacyScanRequest forwards the raw AI response for the legacy HTML UI
func HandleLegacyScanRequest(c *fiber.Ctx) error {
	var req models.ScanRequest

	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"detail": "Invalid JSON payload",
		})
	}

	if req.ImageBase64 == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"detail": "image_base64 is required",
		})
	}

	log.Println("Routing legacy request directly to Ollama Vision Model (Qwen2.5)...")
	resp, err := services.CallOllamaDirectly(req)
	if err != nil {
		log.Printf("Ollama Error: %v", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"detail": "Native AI processing failed",
		})
	}

	// Return raw JSON byte array directly exactly as Ollama sent it
	c.Set("Content-Type", "application/json")
	return c.Send(resp)
}

// HandleDocumentScanRequest processes uploads of crop-related documents (labels, prescriptions)
func HandleDocumentScanRequest(c *fiber.Ctx) error {
	var req models.ScanRequest

	if err := c.BodyParser(&req); err != nil {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"success": false,
			"message": "Invalid JSON payload",
		})
	}

	if req.ImageBase64 == "" {
		return c.Status(fiber.StatusBadRequest).JSON(fiber.Map{
			"success": false,
			"message": "image_base64 is required",
		})
	}

	log.Println("Routing document extraction request to Ollama Vision Model...")
	resp, err := services.CallOllamaForDocument(req)
	if err != nil {
		log.Printf("Ollama Document Extraction Error: %v", err)
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"success": false,
			"message": "Document extraction failed",
		})
	}

	// Parse raw JSON to map
	var docData map[string]interface{}
	if err := json.Unmarshal(resp, &docData); err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"success": false,
			"message": "Failed to parse document extraction response",
		})
	}

	return c.JSON(fiber.Map{
		"success": true,
		"data":    docData,
	})
}

