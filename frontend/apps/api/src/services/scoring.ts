import { TurnScoreSchema } from "@debate/contracts";

export const scoreTurn = (content: string) => {
  const lengthScore = Math.min(100, Math.max(40, Math.round(content.length / 10)));
  const civility = content.toLowerCase().includes("idiot") ? 40 : 75;
  const relevance = Math.min(100, 60 + Math.round(content.length / 50));
  const base = Math.min(100, lengthScore + 10);
  return TurnScoreSchema.parse({
    clarity: Math.min(100, base),
    logic: Math.min(100, base - 5),
    evidence: Math.min(100, base - 10),
    rebuttal: Math.min(100, base - 8),
    civility,
    relevance
  });
};

export const aggregateScores = (scores: Array<ReturnType<typeof scoreTurn>>) => {
  if (scores.length === 0) {
    return scoreTurn("");
  }
  const sums = scores.reduce(
    (acc, score) => {
      acc.clarity += score.clarity;
      acc.logic += score.logic;
      acc.evidence += score.evidence;
      acc.rebuttal += score.rebuttal;
      acc.civility += score.civility;
      acc.relevance += score.relevance;
      return acc;
    },
    { clarity: 0, logic: 0, evidence: 0, rebuttal: 0, civility: 0, relevance: 0 }
  );

  const average = {
    clarity: Math.round(sums.clarity / scores.length),
    logic: Math.round(sums.logic / scores.length),
    evidence: Math.round(sums.evidence / scores.length),
    rebuttal: Math.round(sums.rebuttal / scores.length),
    civility: Math.round(sums.civility / scores.length),
    relevance: Math.round(sums.relevance / scores.length)
  };

  return TurnScoreSchema.parse(average);
};
