import { GoogleGenerativeAI } from "@google/generative-ai";
import dotenv from "dotenv";

dotenv.config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || "");

export const generateInterviewQuestions = async (missingSkills, role) => {
  if (!process.env.GEMINI_API_KEY) {
    throw new Error("GEMINI_API_KEY is not configured.");
  }

  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

  const prompt = `
    You are an expert technical interviewer.
    The user is applying for the role of: ${role}.
    They have the following identified skill gaps: ${missingSkills.join(", ")}.
    
    Generate 15 critical interview questions (mix of technical and behavioral) that specifically target these gaps to help the user improve.
    Format the response as a valid JSON array of objects:
    [
      { "id": 1, "question": "...", "category": "Technical/Behavioral", "tip": "Why this is asked..." },
      ...
    ]
    Return ONLY the JSON.
  `;

  const result = await model.generateContent(prompt);
  const response = await result.response;
  const text = response.text();
  
  // Clean up potential markdown formatting
  const jsonMatch = text.match(/\[.*\]/s);
  if (jsonMatch) {
    return JSON.parse(jsonMatch[0]);
  }
  return JSON.parse(text);
};

export const chatWithGemini = async (history, message) => {
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

  const systemPrompt = `
    You are the SkillForge AI Career Coach, developed by Team ByteWorks (Arushi, Aarya, Hridaya, and Shivani) for the IISc Hackathon.
    
    PERSONALITY:
    - Extremely friendly, empathetic, and encouraging.
    - You act as a mentor, not just a bot.
    - If the user sounds overwhelmed, stressed, or anxious (detected through their tone), prioritize their mental well-being. Offer motivational words, suggest taking a break, and remind them that upskilling is a marathon, not a sprint.
    - Use phrases like "I'm here for you," "Take a deep breath," or "You've got this, ByteWorker!"
    
    CAPABILITIES:
    - Provide career advice and roadmap guidance.
    - If asked for "practice questions" or "interview help" for a specific skill, generate 3-5 high-quality questions immediately.
    - Explain complex ML concepts (like SHAP or Bayesian inference) in simple, "ELI5" terms.
    
    TONE DETECTION:
    - If the user uses words like "stressed", "tired", "quit", "too much", "failing", or "overwhelmed", shift to a MOTIVATIONAL & SUPPORTIVE mode.
  `;

  const chat = model.startChat({
    history: [
      { role: "user", parts: [{ text: systemPrompt }] },
      { role: "model", parts: [{ text: "Understood. I am the ByteWorks Career Coach, ready to motivate and guide our users with empathy and expertise." }] },
      ...history.map(h => ({
        role: h.role === "user" ? "user" : "model",
        parts: [{ text: h.content }],
      }))
    ],
    generationConfig: {
      maxOutputTokens: 800,
    },
  });

  const result = await chat.sendMessage(message);
  const response = await result.response;
  return response.text();
};
