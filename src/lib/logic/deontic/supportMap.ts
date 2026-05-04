import type { DeonticGraph, DeonticRule } from './graph';

export type SupportStatus = 'supported' | 'partial' | 'unsupported';

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
  satisfied_source_ids: string[];
  missing_source_ids: string[];
  support_status: SupportStatus;
}

export interface MotionSupportMap {
  entries: SupportMapEntry[];
  toDict(): Record<string, unknown>;
  summary(): Record<string, unknown>;
}

export type FactCatalog = Record<string, Partial<SupportFact> & { evidence_ids?: string[] }>;
export type FilingMap = Record<string, Array<Partial<FilingSupportReference>>>;

export class BrowserMotionSupportMap implements MotionSupportMap {
  constructor(readonly entries: SupportMapEntry[] = []) {}

  toDict(): Record<string, unknown> {
    return {
      entry_count: this.entries.length,
      summary: this.summary(),
      entries: this.entries.map((entry) => ({
        ...entry,
        facts: entry.facts.map((fact) => ({
          ...fact,
          source_ids: [...fact.source_ids],
          attributes: { ...fact.attributes },
        })),
        filings: entry.filings.map((filing) => ({ ...filing })),
        authority_ids: [...entry.authority_ids],
        evidence_ids: [...entry.evidence_ids],
        satisfied_source_ids: [...entry.satisfied_source_ids],
        missing_source_ids: [...entry.missing_source_ids],
      })),
    };
  }

  summary(): Record<string, unknown> {
    const authorityIds = new Set<string>();
    const evidenceIds = new Set<string>();
    let establishedFactCount = 0;
    let allegedFactCount = 0;
    let missingSourceCount = 0;

    for (const entry of this.entries) {
      entry.authority_ids.forEach((authorityId) => authorityIds.add(authorityId));
      entry.evidence_ids.forEach((evidenceId) => evidenceIds.add(evidenceId));
      missingSourceCount += entry.missing_source_ids.length;
      for (const fact of entry.facts) {
        if (fact.status === 'established') {
          establishedFactCount += 1;
        } else {
          allegedFactCount += 1;
        }
      }
    }

    return {
      entry_count: this.entries.length,
      active_entry_count: this.entries.filter((entry) => entry.active).length,
      supported_entry_count: this.entries.filter((entry) => entry.support_status === 'supported')
        .length,
      partial_entry_count: this.entries.filter((entry) => entry.support_status === 'partial')
        .length,
      unsupported_entry_count: this.entries.filter(
        (entry) => entry.support_status === 'unsupported',
      ).length,
      established_fact_count: establishedFactCount,
      alleged_fact_count: allegedFactCount,
      missing_source_count: missingSourceCount,
      authority_count: authorityIds.size,
      evidence_count: evidenceIds.size,
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
      .map((rule) =>
        this.buildEntry(rule, graph, options.factCatalog ?? {}, options.filingMap ?? {}),
      )
      .sort(
        (left, right) =>
          Number(!left.active) - Number(!right.active) || left.rule_id.localeCompare(right.rule_id),
      );

    return new BrowserMotionSupportMap(entries);
  }

  private buildEntry(
    rule: DeonticRule,
    graph: DeonticGraph,
    factCatalog: FactCatalog,
    filingMap: FilingMap,
  ): SupportMapEntry {
    const target = graph.getNode(rule.target_id);
    const satisfied_source_ids: string[] = [];
    const missing_source_ids: string[] = [];
    for (const sourceId of rule.source_ids) {
      const sourceNode = graph.getNode(sourceId);
      if (sourceNode?.active) {
        satisfied_source_ids.push(sourceId);
      } else {
        missing_source_ids.push(sourceId);
      }
    }

    return {
      rule_id: rule.id,
      target_id: rule.target_id,
      target_label: target?.label ?? rule.target_id,
      modality: rule.modality,
      predicate: rule.predicate,
      active: rule.active,
      facts: this.buildFactEntries(rule.source_ids, graph, factCatalog),
      filings: this.buildFilingEntries(rule.id, filingMap[rule.id] ?? []),
      authority_ids: [...rule.authority_ids],
      evidence_ids: [...rule.evidence_ids],
      satisfied_source_ids,
      missing_source_ids,
      support_status: classifySupport(satisfied_source_ids.length, missing_source_ids.length),
    };
  }

  private buildFactEntries(
    sourceIds: string[],
    graph: DeonticGraph,
    factCatalog: FactCatalog,
  ): SupportFact[] {
    return sourceIds
      .filter(
        (sourceId) => sourceId.startsWith('fact:') || graph.getNode(sourceId)?.node_type === 'fact',
      )
      .map((sourceId) => {
        const node = graph.getNode(sourceId);
        const payload = factCatalog[sourceId] ?? {};
        return {
          fact_id: sourceId,
          predicate: String(payload.predicate ?? node?.label ?? sourceId),
          status: String(payload.status ?? (node?.active ? 'established' : 'alleged')),
          source_ids: toStringList(payload.source_ids ?? payload.evidence_ids),
          attributes: objectRecord(payload.attributes),
        };
      });
  }

  private buildFilingEntries(
    ruleId: string,
    filings: Array<Partial<FilingSupportReference>>,
  ): FilingSupportReference[] {
    return filings.map((filing) => ({
      filing_id: String(filing.filing_id ?? ruleId),
      filing_type: String(filing.filing_type ?? 'motion'),
      proposition: String(filing.proposition ?? ''),
    }));
  }
}

function classifySupport(satisfiedCount: number, missingCount: number): SupportStatus {
  if (missingCount === 0) return 'supported';
  if (satisfiedCount > 0) return 'partial';
  return 'unsupported';
}

function toStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function objectRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? { ...(value as Record<string, unknown>) }
    : {};
}
