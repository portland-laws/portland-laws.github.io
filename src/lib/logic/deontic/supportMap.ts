import type { DeonticGraph, DeonticRule } from './graph';

export interface SupportFact {
  fact_id: string;
  predicate: string;
  status: string;
  source_ids: string[];
  attributes: Record<string, unknown>;
}

export interface FilingSupportReference {
  filing_id: string;
  filing_type: string;
  proposition: string;
}

export interface SupportMapEntry {
  rule_id: string;
  target_id: string;
  target_label: string;
  modality: string;
  predicate: string;
  active: boolean;
  facts: SupportFact[];
  filings: FilingSupportReference[];
  authority_ids: string[];
  evidence_ids: string[];
}

export interface MotionSupportMap {
  entries: SupportMapEntry[];
  toDict(): Record<string, unknown>;
}

export type FactCatalog = Record<string, Partial<SupportFact> & { evidence_ids?: string[] }>;
export type FilingMap = Record<string, Array<Partial<FilingSupportReference>>>;

export class BrowserMotionSupportMap implements MotionSupportMap {
  constructor(readonly entries: SupportMapEntry[] = []) {}

  toDict(): Record<string, unknown> {
    return {
      entry_count: this.entries.length,
      entries: this.entries.map((entry) => ({
        ...entry,
        facts: entry.facts.map((fact) => ({ ...fact, source_ids: [...fact.source_ids], attributes: { ...fact.attributes } })),
        filings: entry.filings.map((filing) => ({ ...filing })),
        authority_ids: [...entry.authority_ids],
        evidence_ids: [...entry.evidence_ids],
      })),
    };
  }
}

export class SupportMapBuilder {
  buildFromDeonticGraph(
    graph: DeonticGraph,
    options: {
      factCatalog?: FactCatalog;
      filingMap?: FilingMap;
      onlyActive?: boolean;
    } = {},
  ): MotionSupportMap {
    const onlyActive = options.onlyActive ?? true;
    const entries = [...graph.rules.values()]
      .filter((rule) => rule.active || !onlyActive)
      .map((rule) => this.buildEntry(rule, graph, options.factCatalog ?? {}, options.filingMap ?? {}))
      .sort((left, right) => Number(!left.active) - Number(!right.active) || left.rule_id.localeCompare(right.rule_id));

    return new BrowserMotionSupportMap(entries);
  }

  private buildEntry(rule: DeonticRule, graph: DeonticGraph, factCatalog: FactCatalog, filingMap: FilingMap): SupportMapEntry {
    const target = graph.getNode(rule.target_id);
    return {
      rule_id: rule.id,
      target_id: rule.target_id,
      target_label: target?.label ?? rule.target_id,
      modality: rule.modality,
      predicate: rule.predicate,
      active: rule.active,
      facts: this.buildFactEntries(rule.source_ids, factCatalog),
      filings: this.buildFilingEntries(rule.id, filingMap[rule.id] ?? []),
      authority_ids: [...rule.authority_ids],
      evidence_ids: [...rule.evidence_ids],
    };
  }

  private buildFactEntries(sourceIds: string[], factCatalog: FactCatalog): SupportFact[] {
    return sourceIds
      .filter((sourceId) => sourceId.startsWith('fact:'))
      .map((sourceId) => {
        const payload = factCatalog[sourceId] ?? {};
        return {
          fact_id: sourceId,
          predicate: String(payload.predicate ?? sourceId),
          status: String(payload.status ?? 'alleged'),
          source_ids: toStringList(payload.source_ids ?? payload.evidence_ids),
          attributes: objectRecord(payload.attributes),
        };
      });
  }

  private buildFilingEntries(ruleId: string, filings: Array<Partial<FilingSupportReference>>): FilingSupportReference[] {
    return filings.map((filing) => ({
      filing_id: String(filing.filing_id ?? ruleId),
      filing_type: String(filing.filing_type ?? 'motion'),
      proposition: String(filing.proposition ?? ''),
    }));
  }
}

function toStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function objectRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? { ...(value as Record<string, unknown>) } : {};
}
