import Result from "../models/Result.js";

export const getResult = async (req, res) => {
  try {
    const result = await Result.findById(req.params.id);
    if (!result) return res.status(404).json({ error: "Result not found" });
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
