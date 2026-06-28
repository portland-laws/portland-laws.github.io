import { buildChatPromptStarters, DEFAULT_CHAT_PROMPTS } from './chatPromptStarters';
import type { CorpusEntity, CorpusRelationship, CorpusSection } from './portlandCorpus';
import type { LogicProofSummary } from './portlandLogic';

function makeSection(overrides: Partial<CorpusSection> = {}): CorpusSection {
  return {
    ipfs_cid: 'bafk-section-cid',
    identifier: '33.10.010',
    title: 'Notice requirements',
    text: 'Notice text',
    source_url: 'https://example.test/section',
    official_cite: 'PCC 33.10.010',
    bluebook_citation: 'PCC 33.10.010',
    chapter: '33.10',
    title_number: '33',
    jsonld: '{}',
    ...overrides,
  };
}

function makeEntity(overrides: Partial<CorpusEntity> = {}): CorpusEntity {
  return {
    id: 'municipal_actor:director',
    type: 'municipal_actor',
    label: 'Director',
    properties: {},
    ...overrides,
  };
}

function makeRelationship(overrides: Partial<CorpusRelationship> = {}): CorpusRelationship {
  return {
    id: 'rel-1',
    source: 'bafk-section-cid',
    target: 'portland_code_section:33_10_020',
    type: 'cross_reference',
    properties: {},
    ...overrides,
  };
}

function makeProof(overrides: Partial<LogicProofSummary> = {}): LogicProofSummary {
  return {
    ipfs_cid: 'bafk-section-cid',
    identifier: '33.10.010',
    title: 'Notice requirements',
    formalization_scope: 'section',
    fol_status: 'success',
    deontic_status: 'success',
    deontic_temporal_fol: 'O(notice(x) -> before(hearing))',
    deontic_cognitive_event_calculus: 'Initiates(send_notice, informed_party, t)',
    frame_logic_ergo: 'section_notice_rule.',
    norm_operator: 'O',
    norm_type: 'obligation',
    zkp_backend: 'simulated',
    zkp_security_note: 'Local verification only',
    zkp_verified: true,
    ...overrides,
  };
}

describe('buildChatPromptStarters', () => {
  it('includes graph-derived and theorem-derived prompts for rich section context', () => {
    const prompts = buildChatPromptStarters(
      makeSection(),
      makeProof(),
      [
        makeEntity(),
        makeEntity({ id: 'municipal_subject:applicant', type: 'municipal_subject', label: 'Applicant' }),
        makeEntity({ id: 'requirement:notice', type: 'requirement', label: 'Notice requirement' }),
      ],
      [makeRelationship()],
    );

    expect(prompts).toContain('What duties does PCC 33.10.010 impose on Director?');
    expect(prompts).toContain('How does PCC 33.10.010 treat Notice requirement?');
    expect(prompts).toContain('What evidence shows how This section Cross Reference Section 33.10.020?');
    expect(prompts).toContain('What obligation does the theorem for PCC 33.10.010 formalize?');
    expect(prompts).toContain('What proof-backed conclusions about PCC 33.10.010 are certificate-verified?');
  });

  it('keeps fallback prompts available and de-duplicates repeated graph context', () => {
    const prompts = buildChatPromptStarters(
      makeSection(),
      null,
      [
        makeEntity({ id: 'municipal_actor:director', type: 'municipal_actor', label: 'Director' }),
        makeEntity({ id: 'municipal_actor:director', type: 'municipal_actor', label: 'Director' }),
      ],
      [
        makeRelationship({ id: 'rel-1' }),
        makeRelationship({ id: 'rel-2' }),
      ],
    );

    expect(prompts.slice(0, DEFAULT_CHAT_PROMPTS.length)).toEqual(DEFAULT_CHAT_PROMPTS);
    expect(prompts.filter((prompt) => prompt === 'How is PCC 33.10.010 connected to Director in the knowledge graph?')).toHaveLength(1);
    expect(prompts.length).toBeLessThanOrEqual(14);
  });

  it('falls back to the section title when no citation label is available', () => {
    const prompts = buildChatPromptStarters(
      makeSection({ bluebook_citation: '', official_cite: '', identifier: '', title: 'Tree preservation notices' }),
      makeProof({ deontic_temporal_fol: '', deontic_cognitive_event_calculus: '', zkp_verified: false }),
      [],
      [],
    );

    expect(prompts).toContain('What does Tree preservation notices require in plain language?');
    expect(prompts).toContain('Explain the O-based theorem for Tree preservation notices in plain language.');
    expect(prompts).not.toContain('What proof-backed conclusions about Tree preservation notices are certificate-verified?');
  });
});