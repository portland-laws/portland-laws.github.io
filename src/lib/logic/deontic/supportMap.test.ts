import { DeonticGraphBuilder } from './graph';
import { SupportMapBuilder } from './supportMap';

describe('deontic support map parity helpers', () => {
  it('builds rule-centered support maps from deontic graphs', () => {
    const graph = new DeonticGraphBuilder().buildFromMatrix([
      {
        rule_id: 'rule:appeal',
        modality: 'permission',
        predicate: 'appeal',
        target_id: 'action:appeal',
        target_label: 'appeal permit denial',
        sources: ['fact:denied', 'condition:timely'],
        authorities: ['code:appeals'],
        evidence_ids: ['ev:appeal'],
        active: true,
      },
      {
        rule_id: 'rule:inactive',
        modality: 'obligation',
        predicate: 'file notice',
        target_id: 'action:notice',
        target_label: 'file notice',
        sources: ['fact:notice'],
        active: false,
      },
    ]);

    const supportMap = new SupportMapBuilder().buildFromDeonticGraph(graph, {
      factCatalog: {
        'fact:denied': {
          predicate: 'PermitDenied(applicant)',
          status: 'established',
          evidence_ids: ['doc:denial'],
          attributes: { page: 2 },
        },
      },
      filingMap: {
        'rule:appeal': [
          {
            filing_id: 'motion:1',
            filing_type: 'appeal',
            proposition: 'Applicant may appeal denial.',
          },
        ],
      },
    });

    expect(supportMap.entries).toHaveLength(1);
    expect(supportMap.entries[0]).toMatchObject({
      rule_id: 'rule:appeal',
      target_label: 'appeal permit denial',
      modality: 'permission',
      facts: [
        {
          fact_id: 'fact:denied',
          predicate: 'PermitDenied(applicant)',
          status: 'established',
          source_ids: ['doc:denial'],
          attributes: { page: 2 },
        },
      ],
      filings: [
        {
          filing_id: 'motion:1',
          filing_type: 'appeal',
          proposition: 'Applicant may appeal denial.',
        },
      ],
    });
    expect(supportMap.toDict()).toMatchObject({ entry_count: 1 });
  });

  it('can include inactive rules and supplies Python-style defaults', () => {
    const graph = new DeonticGraphBuilder().buildFromMatrix([
      {
        rule_id: 'rule:inactive',
        target_id: 'action:notice',
        target_label: 'file notice',
        sources: ['fact:notice'],
        active: false,
      },
    ]);

    const supportMap = new SupportMapBuilder().buildFromDeonticGraph(graph, { onlyActive: false });

    expect(supportMap.entries[0]).toMatchObject({
      rule_id: 'rule:inactive',
      modality: 'obligation',
      predicate: 'file notice',
      support_status: 'unsupported',
      satisfied_source_ids: [],
      missing_source_ids: ['fact:notice'],
      facts: [
        {
          fact_id: 'fact:notice',
          predicate: 'fact:notice',
          status: 'alleged',
          source_ids: [],
          attributes: {},
        },
      ],
      filings: [],
    });
  });

  it('recognizes graph fact nodes and exports support summaries', () => {
    const graph = new DeonticGraphBuilder().buildFromMatrix([
      {
        rule_id: 'rule:mixed',
        modality: 'obligation',
        predicate: 'inspect premises',
        target_id: 'action:inspect',
        target_label: 'inspect premises',
        sources: [
          {
            id: 'finding:permit-issued',
            label: 'Permit was issued',
            node_type: 'fact',
            active: true,
          },
          {
            id: 'condition:notice',
            label: 'Notice was served',
            node_type: 'condition',
            active: false,
          },
        ],
        authorities: ['code:inspection'],
        evidence_ids: ['ev:inspection'],
        active: true,
      },
    ]);

    const supportMap = new SupportMapBuilder().buildFromDeonticGraph(graph);

    expect(supportMap.entries[0]).toMatchObject({
      rule_id: 'rule:mixed',
      support_status: 'partial',
      satisfied_source_ids: ['finding:permit-issued'],
      missing_source_ids: ['condition:notice'],
      facts: [
        {
          fact_id: 'finding:permit-issued',
          predicate: 'Permit was issued',
          status: 'established',
        },
      ],
    });
    expect(supportMap.summary()).toMatchObject({
      entry_count: 1,
      partial_entry_count: 1,
      established_fact_count: 1,
      missing_source_count: 1,
      authority_count: 1,
      evidence_count: 1,
    });
    expect(supportMap.toDict()).toMatchObject({
      entry_count: 1,
      summary: { partial_entry_count: 1 },
    });
  });
});
