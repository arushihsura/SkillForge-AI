import express from "express";
import { getResult } from "../controllers/analyzeController.js";

const router = express.Router();

router.get("/:id", getResult);

export default router;
