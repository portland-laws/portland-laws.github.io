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
});
