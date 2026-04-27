import { clientEmbeddingWorkerService } from './clientEmbeddingWorkerService';
import { GraphRagEvidence, SearchResult, buildGraphRagEvidence } from './portlandCorpus';
import {
  buildLogicEvidenceForSearchResults,
  type LogicEvidenceItem,
} from './portlandLogic';

export interface GraphRagAnswer {
  question: string;
  answer: string;
  evidence: GraphRagEvidence;
  logicEvidence: LogicEvidenceItem[];
  usedLocalModel: boolean;
  warning?: string;
}

export async function answerWithGraphRag(question: string): Promise<GraphRagAnswer> {
  const trimmedQuestion = question.trim();
  if (!trimmedQuestion) {
    throw new Error('Question is required');
  }

  let queryEmbedding: Float32Array | undefined;
  try {
    queryEmbedding = await clientEmbeddingWorkerService.generateEmbedding(trimmedQuestion);
  } catch (error) {
    console.warn('GraphRAG embedding unavailable, retrieving with keyword search only', error);
  }

  const evidence = await buildGraphRagEvidence(trimmedQuestion, queryEmbedding, 5);
  const logicEvidence = await buildLogicEvidenceForSearchResults(evidence.sections);
  if (evidence.sections.length === 0) {
    return {
      question: trimmedQuestion,
      answer:
        'I could not find a relevant Portland City Code section in the local corpus for that question.',
      evidence,
      logicEvidence,
      usedLocalModel: false,
      warning: 'No supporting evidence was retrieved.',
    };
  }

  const prompt = buildGraphRagPrompt(trimmedQuestion, evidence.sections, logicEvidence);

  try {
    if (shouldSkipLocalModelForBrowserTest()) {
      return {
        question: trimmedQuestion,
        answer: buildEvidenceSummary(evidence.sections),
        evidence,
        logicEvidence,
        usedLocalModel: false,
        warning: 'Answered from retrieved evidence without local model generation.',
      };
    }

    const { clientLLMWorkerService } = await import('./clientLLMWorkerService');
    const rawAnswer = await clientLLMWorkerService.generateText(prompt, 220);
    const candidateAnswer = cleanModelAnswer(rawAnswer);
    const answer = isGroundedAnswer(candidateAnswer)
      ? candidateAnswer
      : buildEvidenceSummary(evidence.sections);
    return {
      question: trimmedQuestion,
      answer,
      evidence,
      logicEvidence,
      usedLocalModel: answer === candidateAnswer,
      warning:
        answer === candidateAnswer
          ? undefined
          : 'Local model output did not include required citations, so the app returned a cited evidence summary.',
    };
  } catch (error) {
    console.warn('Local GraphRAG generation failed, using evidence summary', error);
    return {
      question: trimmedQuestion,
      answer: buildEvidenceSummary(evidence.sections),
      evidence,
      logicEvidence,
      usedLocalModel: false,
      warning:
        error instanceof Error
          ? `Local model unavailable: ${error.message}`
          : 'Local model unavailable.',
    };
  }
}

function shouldSkipLocalModelForBrowserTest() {
  if (typeof window === 'undefined') {
    return false;
  }
  return window.localStorage.getItem('PORTLAND_DISABLE_LOCAL_LLM') === 'true';
}

function buildGraphRagPrompt(question: string, sections: SearchResult[], logicEvidence: LogicEvidenceItem[]) {
  const logicByCid = new Map(logicEvidence.map((item) => [item.ipfs_cid, item]));
  const evidence = sections
    .map((result, index) => {
      const section = result.section;
      const citation = result.citation || section.identifier;
      const logic = logicByCid.get(result.ipfs_cid);
      const logicBlock = logic
        ? `
Generated logic metadata:
- Norm: ${logic.normType} (${logic.normOperator})
- Temporal scope: ${logic.temporalScope}
- Parse status: ${logic.parseStatus}
- Certificate: ${logic.certificateStatus}
- Caveat: ${logic.caveats[0] || 'Machine-generated candidate formalization.'}`
        : '\nGenerated logic metadata: unavailable for this evidence item.';
      return `[${index + 1}] ${citation}
Title: ${section.title}
Source: ${section.source_url}
Excerpt: ${cleanCorpusExcerpt(result.snippet || section.text.slice(0, 700))}${logicBlock}`;
    })
    .join('\n\n');

  return `You answer simple questions about the Portland City Code using only the evidence below.
This is legal information, not legal advice.
Generated logic metadata is machine-created support material, not the official law text.
If the evidence does not answer the question, say that the local corpus evidence is insufficient.
Keep the answer concise.
Every factual sentence must cite at least one evidence number like [1] or [2].

Question: ${question}

Evidence:
${evidence}

Answer:`;
}

function cleanModelAnswer(answer: string) {
  return answer
    .replace(/<\|[^>]+?\|>/g, '')
    .replace(/^answer:\s*/i, '')
    .trim();
}

function isGroundedAnswer(answer: string) {
  if (!answer || answer.length < 24) {
    return false;
  }
  return /\[[1-5]\]/.test(answer);
}

function buildEvidenceSummary(sections: SearchResult[]) {
  const topSections = sections.slice(0, 3);
  const lead = topSections
    .map((result, index) => {
      const section = result.section;
      return `[${index + 1}] ${result.citation}: ${section.title}. ${cleanCorpusExcerpt(result.snippet)}`;
    })
    .join('\n\n');

  return `The strongest local corpus matches are:\n\n${lead}\n\nReview the cited Portland City Code sections before relying on this information.`;
}

function cleanCorpusExcerpt(excerpt: string) {
  return excerpt
    .replace(/\s+/g, ' ')
    .replace(/(^|\.\.\.|\s)Label:\s*City code section\s*/gi, '$1')
    .replace(/(^|\.\.\.|\s)Label:\s*/gi, '$1')
    .trim();
}
