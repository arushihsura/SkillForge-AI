import mongoose from "mongoose";

const analysisSchema = new mongoose.Schema(
  {
    userId: String,
    resumeText: String,
    jdText: String,
    skills: Object,
    gap: Array,
    path: Array,
  },
  { timestamps: true }
);

export default mongoose.model("Analysis", analysisSchema);
