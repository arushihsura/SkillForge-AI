import pdf from "pdf-parse";

export const extractText = async (fileBuffer) => {
  const data = await pdf(fileBuffer);
  return data.text;
};
