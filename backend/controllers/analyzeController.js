import Analysis from "../models/Analysis.js";
import { extractSkills } from "../utils/skills.js";

export const analyze = async (req, res) => {
  try {
    const { resumeText, jdText } = req.body;

    const resumeSkills = extractSkills(resumeText);
    const jdSkills = extractSkills(jdText);

    const gap = jdSkills.filter((s) => !resumeSkills.includes(s));

    const path = gap.map((skill) => ({
      skill,
      status: "recommended",
    }));

    const result = await Analysis.create({
      userId: req.userId,
      resumeText,
      jdText,
      skills: { resumeSkills, jdSkills },
      gap,
      path,
    });

    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

export const getResult = async (req, res) => {
  try {
    const result = await Analysis.findById(req.params.id);
    if (!result) return res.status(404).json("Result not found");
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
