# Stable Diffusion Setup Guide

## Overview
The ML Learning Assistant supports image generation using both:
1. **Smart Diagrams (Default)** - Built-in educational diagrams with auto-detection
2. **Stable Diffusion** - High-quality photorealistic AI-generated images

## Currently Active
**Smart Diagrams** is the default and doesn't require any API keys. It works perfectly for educational content and ML concepts.

## Enabling Stable Diffusion (Optional)

### Step 1: Get HuggingFace Token
1. Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
2. Sign up or log in (free account)
3. Click "New token"
4. Set name: `ml-learning-assistant`
5. Select type: **Read**
6. Create and copy the token

### Step 2: Configure Environment
1. Open `.env` file in your project root
2. Find this line:
   ```
   HF_TOKEN=your-huggingface-token-here
   ```
3. Replace with your actual token:
   ```
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxx
   ```
4. Save the file

### Step 3: Restart Server
```powershell
# Stop current server
Stop-Process -Name python -Force

# Start server again
Set-Location 'C:\Users\HomePC\Documents\IIC_hackthon\ML_LEARNING_ASSISTANT'
.\venv\Scripts\python.exe app.py
```

### Step 4: Use in Application
1. Open the Image Visualization page
2. In the "Image Style" dropdown, select **"Stable Diffusion (Requires API Key)"**
3. Enter your ML concept and generate

## How It Works

### Smart Diagrams (Default)
- **Auto-detects** diagram type from concept:
  - Neural Networks
  - Decision Trees
  - Flowcharts
  - Architecture Diagrams
  - Concept Maps
- **No API key required**
- **Fast generation** (instant)
- **Educational focused** (clean, clear visualizations)
- **Multiple variations** - Generate 3 different versions with unique styles

### Stable Diffusion
- **Photorealistic** AI-generated images
- **Requires HuggingFace token**
- **Slower** (10-30 seconds)
- **Creative rendering** (artistic interpretation)
- **Uses HuggingFace API** (free tier available)

## Automatic Fallback

If Stable Diffusion fails or token is invalid:
- ✅ System automatically falls back to **Smart Diagrams**
- ✅ User still gets an image result
- ✅ No error shown to end user
- ✅ Seamless experience

## Troubleshooting

### "HF_TOKEN not set or is placeholder"
**Solution**: 
1. Check `.env` file has your real token
2. Restart the server
3. HuggingFace tokens start with `hf_`

### "Authentication failed (401)"
**Solution**: 
1. Your token might be invalid or expired
2. Generate a new token from HuggingFace
3. Update `.env` file
4. Restart server

### "Model is loading (503)"
**Solution**: 
1. HuggingFace models take time to load on first use
2. Wait 1-2 minutes for the model to initialize
3. Try again - subsequent requests are faster

### "Rate limited (429)"
**Solution**: 
1. You've sent too many requests
2. Wait a few minutes before trying again
3. HuggingFace free tier has rate limits

## Comparison Table

| Feature | Smart Diagrams | Stable Diffusion |
|---------|---|---|
| Setup Required | ❌ No | ✅ Yes |
| API Usage | Local PIL | HuggingFace API |
| Speed | Instant | 10-30 sec |
| Style | Educational | Photorealistic |
| Cost | Free | Free (rate limited) |
| Reliability | High | Depends on API |
| Best For | ML Concepts | Creative Visuals |

## API Endpoint Details

### Generate Single Image
```bash
POST /api/generate-image
Content-Type: application/json

{
  "concept": "convolutional neural networks",
  "diagram_type": "Technical",
  "backend": "stable_diffusion"  // or "placeholder"
}

Response:
{
  "success": true,
  "image_url": "/uploads/images/diagram_*.png",
  "backend_used": "stable_diffusion",
  "generated_at": "2026-02-06T14:00:40.123456"
}
```

### Generate Multiple Images
```bash
POST /api/generate-images-multiple
Content-Type: application/json

{
  "concept": "machine learning models",
  "count": 3
}

Response:
{
  "success": true,
  "images": [
    { "image_url": "...", "diagram_type": "Conceptual" },
    { "image_url": "...", "diagram_type": "Technical" },
    { "image_url": "...", "diagram_type": "Flowchart" }
  ]
}
```

## Performance Tips

1. **Use Smart Diagrams for learning** - Faster, clearer for educational purposes
2. **Use Stable Diffusion for presentations** - More creative, impressive visuals
3. **Cache results** - Don't regenerate the same images repeatedly
4. **Batch requests** - Generate multiple at once instead of one-by-one
5. **Off-peak hours** - Stable Diffusion is faster during off-peak HuggingFace usage

## Security Notes

- `HF_TOKEN` is private, never commit to git
- `.env` file is already in `.gitignore`
- Token is used only for HuggingFace API communication
- No data is stored or logged by the application

## Support

For issues or questions:
1. Check this guide first
2. Review server logs for error messages
3. Try fallback to Smart Diagrams
4. Verify HuggingFace token is valid at https://huggingface.co/settings/tokens
