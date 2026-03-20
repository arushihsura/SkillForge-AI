import express from "express";
import { analyze } from "../controllers/analyzeController.js";
import { auth } from "../utils/auth.js";

const router = express.Router();

router.post("/", auth, analyze);

export default router;
