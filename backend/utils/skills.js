const SKILLS = ["python", "sql", "machine learning", "react"];

export const extractSkills = (text) => {
  return SKILLS.filter((skill) => text.toLowerCase().includes(skill));
};
