package models

type ScanRequest struct {
	ImageBase64 string `json:"image_base64"`
	CropHint    string `json:"crop_hint,omitempty"`
}

type AIResponse struct {
	Success          bool     `json:"success"`
	CropDetected     string   `json:"crop_detected"`
	Disease          string   `json:"disease"`
	Severity         string   `json:"severity"`
	Confidence       float64  `json:"confidence"`
	HealthAssessment string   `json:"health_assessment"`
	Issues           []Issue  `json:"issues"`
	Recommendations  []string `json:"recommendations"`
	GrowthNeeds      string   `json:"growth_needs"`
}

type Issue struct {
	Name        string `json:"name"`
	Description string `json:"description"`
}
