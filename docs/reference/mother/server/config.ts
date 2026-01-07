import dotenv from 'dotenv';
dotenv.config();

export const config = {
  port: process.env.PORT || 3000,
  apiKey: process.env.AI_GATEWAY_API_KEY || '',
  baseUrl: process.env.AI_GATEWAY_BASE_URL || 'https://ai.t8star.cn/v1',
  models: {
    analysis: {
      complex: 'gemini-3-pro-preview',
      fast: 'gemini-3-flash-preview',
    },
    image: {
      standard: 'nano-banana-2',
      highRes: 'nano-banana-2-2k',
      ultraRes: 'nano-banana-2-4k',
    },
    video: {
      standard: 'sora-2',
    }
  }
};
