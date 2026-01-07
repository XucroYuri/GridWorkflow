import { Router } from 'express';
import { createOpenAIClient, handleOpenAIError } from '../services/openai';
import { config } from '../config';

const router = Router();

// POST /api/ai/analyze
router.post('/analyze', async (req, res, next) => {
  console.log(`[AI] Analyze Request - Model: ${req.body.model}, Key Provided: ${!!req.headers['x-user-gemini-key']}`);
  try {
    const { prompt, model, systemInstruction, responseFormat } = req.body;
    const userKey = req.headers['x-user-gemini-key'] as string | undefined;

    let openai;
    try {
        openai = createOpenAIClient(userKey);
    } catch (e: any) {
        if (e.message === 'MISSING_API_KEY') {
            res.status(401).json({ error: { message: 'API Key not configured on server', code: 'missing_api_key' } });
            return;
        }
        throw e;
    }

    const messages: any[] = [];
    if (systemInstruction) {
      messages.push({ role: 'system', content: systemInstruction });
    }
    messages.push({ role: 'user', content: prompt });

    try {
      console.log(`[AI] Calling OpenAI API... BaseURL: ${config.baseUrl}`);
      const completion = await openai.chat.completions.create({
        model: model || config.models.analysis.complex,
        messages,
        response_format: responseFormat === 'json' ? { type: 'json_object' } : undefined,
      });
      console.log('[AI] Success');
      res.json(completion.choices[0].message.content);
    } catch (apiError: any) {
        console.error('[AI] API Error:', apiError);
        // Enhanced error handling to forward upstream details
        if (apiError.response) {
            const status = apiError.status || 500;
            const data = apiError.response.data || apiError.error || {};
            res.status(status).json({ 
                error: {
                    message: data.error?.message || apiError.message,
                    code: data.error?.code,
                    details: data
                } 
            });
            return;
        }
        res.status(500).json({ error: { message: apiError.message || 'Unknown Server Error', details: apiError } });
    }
  } catch (error) {
    console.error('[AI] Route Error:', error);
    next(error);
  }
});

// POST /api/ai/generate-image
router.post('/generate-image', async (req, res, next) => {
  console.log(`[AI] Image Gen Request - Model: ${req.body.model}, Size: ${req.body.image_size}, AR: ${req.body.aspect_ratio}`);
  try {
    const { prompt, model, image_size, aspect_ratio } = req.body;
    const userKey = req.headers['x-user-gemini-key'] as string | undefined;
    
    // We use direct fetch for Nano-banana specific endpoint /v1/images/edits
    const apiKey = userKey || config.apiKey;
    const baseUrl = config.baseUrl; // e.g. https://ai.t8star.cn/v1

    // Construct FormData
    const formData = new FormData();
    formData.append('model', model || 'nano-banana-2');
    formData.append('prompt', prompt);
    formData.append('response_format', 'url'); // Spec says url or b64_json
    
    if (aspect_ratio) formData.append('aspect_ratio', aspect_ratio);
    if (image_size) formData.append('image_size', image_size);
    
    // Handle Image Input (Reference/Control)
    // If frontend sends 'image' (base64) in body, use it. Otherwise fallback to empty PNG.
    if (req.body.image) {
        try {
            // Expecting base64 string: "data:image/png;base64,..." or just base64
            const base64Data = req.body.image.replace(/^data:image\/\w+;base64,/, "");
            const buffer = Buffer.from(base64Data, 'base64');
            const blob = new Blob([buffer], { type: 'image/png' });
            formData.append('image', blob, 'reference.png');
            console.log('[AI] Attached reference image from request');
        } catch (e) {
            console.warn('[AI] Failed to process input image, falling back to empty.', e);
            const emptyPng = new Uint8Array([
              137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
              0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 196, 137, 0,
              0, 0, 10, 73, 68, 65, 84, 120, 156, 99, 96, 0, 0, 0, 2, 0,
              1, 244, 113, 100, 251, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130
            ]);
            const blob = new Blob([emptyPng], { type: 'image/png' });
            formData.append('image', blob, 'empty.png');
        }
    } else {
        // Spec requires image field. Even if "not carrying reference map", OpenAI Edits endpoint usually demands a file.
        // We create a minimal 1x1 transparent PNG blob to satisfy the multipart requirement.
        const emptyPng = new Uint8Array([
          137, 80, 78, 71, 13, 10, 26, 10, 0, 0, 0, 13, 73, 72, 68, 82,
          0, 0, 0, 1, 0, 0, 0, 1, 8, 6, 0, 0, 0, 31, 21, 196, 137, 0,
          0, 0, 10, 73, 68, 65, 84, 120, 156, 99, 96, 0, 0, 0, 2, 0,
          1, 244, 113, 100, 251, 0, 0, 0, 0, 73, 69, 78, 68, 174, 66, 96, 130
        ]);
        const blob = new Blob([emptyPng], { type: 'image/png' });
        formData.append('image', blob, 'empty.png');
    }

    try {
        const response = await fetch(`${baseUrl}/images/edits`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                // Do NOT set Content-Type header manually for FormData, fetch handles boundary
            },
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            let errorJson;
            try { errorJson = JSON.parse(errorText); } catch(e) {}
            
            console.error('[AI] Image Gen API Error:', response.status, errorText);
            res.status(response.status).json({
                error: {
                    message: errorJson?.error?.message || errorText,
                    code: errorJson?.error?.code || 'upstream_error',
                    details: errorJson
                }
            });
            return;
        }

        const data = await response.json();
        res.json(data.data || data); // Standardize response
    } catch (apiError: any) {
        console.error('[AI] Image Gen Network Error:', apiError);
        res.status(500).json({ error: { message: apiError.message || 'Network Error', details: apiError } });
    }
  } catch (error) {
    next(error);
  }
});

export default router;
