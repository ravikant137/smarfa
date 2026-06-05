package main

import (
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"smarfa-gateway/internal/api"
	"smarfa-gateway/internal/middleware"
	"smarfa-gateway/internal/services"
)

func main() {
	// Initialize Redis connection
	services.InitRedis()

	// Initialize Fiber App
	app := fiber.New(fiber.Config{
		BodyLimit: 50 * 1024 * 1024, // 50MB file limit
		ErrorHandler: func(c *fiber.Ctx, err error) error {
			code := fiber.StatusInternalServerError
			if e, ok := err.(*fiber.Error); ok {
				code = e.Code
			}
			return c.Status(code).JSON(fiber.Map{
				"success": false,
				"message": err.Error(),
			})
		},
	})

	// Global Middleware
	app.Use(recover.New())
	app.Use(logger.New())
	app.Use(cors.New())
	app.Use(middleware.RateLimiter())

	// API Routes
	// Auth
	app.Post("/login", api.HandleLogin)
	app.Post("/register", api.HandleRegister)

	// Dashboard stubs (Supports BOTH Expo App and Legacy HTML Web App)
	app.Get("/summary", api.HandleGetSummary)
	app.Get("/reports/overview", api.HandleGetSummary)
	app.Get("/alerts", api.HandleGetEmptyList)
	app.Get("/alerts/by_type/:category", api.HandleGetEmptyList)
	app.Get("/scan_history", api.HandleGetEmptyList)
	
	// Pump stubs
	app.Get("/pump/status/:id", api.HandlePumpStatus)
	app.Post("/pump/start", api.HandlePumpStatus)
	app.Post("/pump/stop", api.HandlePumpStatus)
	app.Post("/pump/toggle/:id", api.HandlePumpStatus)
	
	// AI / UI stubs
	app.Get("/ai_status", api.HandleAIStatus)
	app.Get("/crop_lifecycle/:crop", api.HandleGetEmptyList)

	// API Group (Matches Vercel frontend paths exactly)
	apiGroup := app.Group("/api")
	apiGroup.Post("/login", api.HandleLogin)
	apiGroup.Post("/register", api.HandleRegister)
	apiGroup.Get("/summary", api.HandleGetSummary)
	apiGroup.Get("/reports/overview", api.HandleGetSummary)
	apiGroup.Get("/alerts", api.HandleGetEmptyList)
	apiGroup.Get("/scan_history", api.HandleGetEmptyList)

	// Fallback for cached browsers and legacy UI
	app.Post("/analyze_crop", api.HandleLegacyScanRequest)

	// Serve the exact original Web UI for the browser!
	app.Static("/", "../web")

	v1 := app.Group("/api/v1")
	
	// Health check
	v1.Get("/health", func(c *fiber.Ctx) error {
		return c.JSON(fiber.Map{"status": "ok", "service": "smarfa-gateway"})
	})

	// Auth (for mobile)
	v1.Post("/login", api.HandleLogin)
	v1.Post("/register", api.HandleRegister)

	// Scan endpoints
	v1.Post("/scan", api.HandleScanRequest)
	v1.Post("/scan_document", api.HandleDocumentScanRequest)

	// Start server on port 8000
	log.Println("Go API Gateway running on port 8000")
	if err := app.Listen(":8000"); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
