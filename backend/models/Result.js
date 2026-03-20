/**
 * backend/models/Result.js
 * ========================
 * Mongoose schema that matches the ML engine's output exactly.
 * Drop this into backend/models/Result.js
 */

import mongoose from "mongoose";
const { Schema } = mongoose;

// ── Sub-schemas ──────────────────────────────────────────────────────────────

const SkillConfSchema = new Schema(
  { skill: String, confidence: Number },
  { _id: false }
);

const MissingSkillSchema = new Schema(
  { skill: String, priority: String, reason: String, implicit: Boolean },
  { _id: false }
);

const ResourceSchema = new Schema(
  { title: String, url: String, type: String },
  { _id: false }
);

const LearningStepSchema = new Schema(
  {
    week:           Number,
    skill:          String,
    priority:       String,
    estimatedHours: Number,
    resources:      [ResourceSchema],
    isPrerequisite: Boolean,
  },
  { _id: false }
);

const WeeklyForecastSchema = new Schema(
  { week: Number, readinessPct: Number },
  { _id: false }
);

const ReadinessSchema = new Schema(
  {
    currentReadinessPct:   Number,
    projectedReadinessPct: Number,
    weeklyForecast:        [WeeklyForecastSchema],
    weeksTo80Pct:          Number,
  },
  { _id: false }
);

const KpisSchema = new Schema(
  {
    totalSkillsRequired:   Number,
    alreadyHave:           Number,
    softMatches:           Number,
    criticalGaps:          Number,
    implicitGaps:          Number,
    estimatedWeeksToReady: Number,
    estimatedTotalHours:   Number,
  },
  { _id: false }
);

// ── Main schema ──────────────────────────────────────────────────────────────

const ResultSchema = new Schema(
  {
    requestId:    { type: String, index: true },
    resumeText:   { type: String, required: true },
    jobDescription: { type: String, required: true },

    resumeSkills:  [SkillConfSchema],
    jobSkills:     [String],
    matchedSkills: [SkillConfSchema],
    softMatches:   [SkillConfSchema],
    missingSkills: [MissingSkillSchema],

    skillGapScore: Number,
    readiness:     ReadinessSchema,
    learningPath:  [LearningStepSchema],
    kpis:          KpisSchema,
    reasoningTrace: [String],
    shapValues:    { type: Map, of: Number }, // Added for SHAP explainability
  },
  {
    timestamps: true,   // adds createdAt + updatedAt automatically
    versionKey: false,
  }
);

// Index for history queries: user-facing "my past analyses" sorted by date
ResultSchema.index({ createdAt: -1 });

const Result = mongoose.models.Result || mongoose.model("Result", ResultSchema);
export default Result;
