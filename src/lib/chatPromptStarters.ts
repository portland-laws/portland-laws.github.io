import type { CorpusEntity, CorpusRelationship, CorpusSection } from './portlandCorpus';
import type { LogicProofSummary } from './portlandLogic';

export const DEFAULT_CHAT_PROMPTS = [
  'What does this section require?',
  'Who is affected by this section?',
  'What evidence supports this answer?',
  'What exceptions or conditions matter here?',
  'How does this section connect to related code provisions?',
  'What logic rule or theorem best describes this section?',
];

export function buildChatPromptStarters(
  section: CorpusSection,
  proof: LogicProofSummary | null,
  relatedEntities: CorpusEntity[],
  relatedRelationships: CorpusRelationship[],
) {
  const prompts: string[] = [];
  const identifier = section.bluebook_citation || section.official_cite || section.identifier;
  const sectionLabel = identifier || section.title;
  const topEntities = relatedEntities
    .filter((entity) => entity.id !== section.ipfs_cid)
    .slice(0, 4);
  const topRelationships = relatedRelationships.slice(0, 4);
  const actorEntity = topEntities.find((entity) => /actor|subject/i.test(entity.type));
  const obligationEntity = topEntities.find((entity) => /requirement|permit|license|notice|appeal|violation/i.test(entity.label));

  const addPrompt = (prompt: string) => {
    const normalized = prompt.trim();
    if (!normalized || prompts.includes(normalized)) {
      return;
    }
    prompts.push(normalized);
  };

  DEFAULT_CHAT_PROMPTS.forEach(addPrompt);
  addPrompt(`What does ${sectionLabel} require in plain language?`);
  addPrompt(`What deadlines, notice rules, or triggering conditions appear in ${sectionLabel}?`);
  addPrompt(`What exceptions, defenses, or carve-outs limit ${sectionLabel}?`);

  if (actorEntity) {
    addPrompt(`What duties does ${sectionLabel} impose on ${entityPromptLabel(actorEntity)}?`);
    addPrompt(`How would ${entityPromptLabel(actorEntity)} need to comply with ${sectionLabel}?`);
  }

  if (obligationEntity) {
    addPrompt(`How does ${sectionLabel} treat ${entityPromptLabel(obligationEntity)}?`);
  }

  topEntities.forEach((entity) => {
    addPrompt(`How is ${sectionLabel} connected to ${entityPromptLabel(entity)} in the knowledge graph?`);
  });

  topRelationships.forEach((relationship) => {
    addPrompt(
      `What evidence shows how ${formatGraphNodeLabel(relationship.source)} ${formatGraphTypeLabel(relationship.type).toLowerCase()} ${formatGraphNodeLabel(relationship.target)}?`,
    );
  });

  if (proof) {
    const normLabel = proof.norm_type !== 'unknown' ? proof.norm_type : 'rule';
    const operatorLabel = proof.norm_operator !== 'unknown' ? proof.norm_operator : 'logic';
    addPrompt(`What ${normLabel} does the theorem for ${sectionLabel} formalize?`);
    addPrompt(`Explain the ${operatorLabel}-based theorem for ${sectionLabel} in plain language.`);
    if (proof.deontic_temporal_fol) {
      addPrompt(`How does the temporal theorem for ${sectionLabel} map back to the code text?`);
    }
    if (proof.deontic_cognitive_event_calculus) {
      addPrompt(`What event sequence or enforcement logic is captured for ${sectionLabel}?`);
    }
    if (proof.zkp_verified) {
      addPrompt(`What proof-backed conclusions about ${sectionLabel} are certificate-verified?`);
    }
  }

  addPrompt(`Which related sections should I compare with ${sectionLabel}?`);
  addPrompt(`What facts from the knowledge graph would help interpret ${sectionLabel}?`);

  return prompts.slice(0, 14);
}

function entityPromptLabel(entity: CorpusEntity) {
  return entity.label?.trim() || formatGraphNodeLabel(entity.id);
}

function formatGraphTypeLabel(type: string) {
  const withoutTechnicalSuffix = type.replace(/_cid$/i, '');
  return withoutTechnicalSuffix
    .replace(/_/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .toLowerCase()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatGraphNodeLabel(nodeId: string) {
  if (nodeId.startsWith('bafk')) return 'This section';
  const [prefix, value] = nodeId.split(':');
  if (!value) return nodeId;
  if (prefix === 'portland_code_title') return `Title ${value}`;
  if (prefix === 'portland_code_chapter') return `Chapter ${value}`;
  if (prefix === 'portland_code_section') return `Section ${value.replace(/_/g, '.')}`;
  if (prefix === 'municipal_actor') return formatGraphValueLabel(value);
  if (prefix === 'municipal_subject') return formatGraphValueLabel(value);
  if (prefix === 'ordinance') return `Ordinance ${value}`;
  if (prefix === 'jurisdiction') return value;
  return formatGraphValueLabel(value);
}

function formatGraphValueLabel(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}