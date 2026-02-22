
import { GoogleGenAI } from "@google/genai";

const API_KEY = process.env.API_KEY;

export class GeminiService {
  private ai: GoogleGenAI;

  constructor() {
    this.ai = new GoogleGenAI({ apiKey: API_KEY || '' });
  }

  async generateExecutiveGreeting(userName: string = "User"): Promise<string> {
    if (!API_KEY) return "Good morning. I've synthesized your updates into three key focus areas.";
    
    try {
      const response = await this.ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Act as a highly efficient Chief of Staff. Generate a one-sentence morning greeting for ${userName} that sets a focused, executive tone. Mention that you have synthesized the noise into clear priorities. Keep it under 20 words.`,
      });
      return response.text?.trim() || "Good morning. I've synthesized your updates.";
    } catch (error) {
      console.error("Gemini Greeting Error:", error);
      return "Good morning. Your briefing is ready.";
    }
  }

  async generateCommitments(priorities: string[]): Promise<string[]> {
    if (!API_KEY) return ["I will track your priorities.", "I will monitor external signals."];

    try {
      const response = await this.ai.models.generateContent({
        model: 'gemini-3-flash-preview',
        contents: `Based on these confirmed priorities: ${priorities.join(', ')}, generate 3 specific commitments the AI assistant will take to support these goals today. Format as a JSON list of strings.`,
        config: {
          responseMimeType: "application/json"
        }
      });
      const data = JSON.parse(response.text || '[]');
      return Array.isArray(data) ? data : ["I will monitor these tasks.", "I will update you tomorrow."];
    } catch (error) {
      console.error("Gemini Commitments Error:", error);
      return ["Monitoring your core tasks.", "Preparing tomorrow's update."];
    }
  }
}

export const gemini = new GeminiService();
