import type { AnalyzedDeonticStatement, DeonticStatementModality } from './analyzer';

export type DeonticNodeType = 'actor' | 'fact' | 'condition' | 'action' | 'outcome' | 'authority';
export type DeonticGraphModality = 'obligation' | 'prohibition' | 'permission' | 'entitlement';

export interface DeonticNode {
  id: string;
  node_type: DeonticNodeType;
  label: string;
  active: boolean;
  confidence: number;
  attributes: Record<string, unknown>;
}

export interface DeonticRule {
  id: string;
  modality: DeonticGraphModality;
  source_ids: string[];
  target_id: string;
  predicate: string;
  active: boolean;
  confidence: number;
  authority_ids: string[];
  evidence_ids: string[];
  attributes: Record<string, unknown>;
}

export interface DeonticGraphConflict {
  rule_id: string;
  conflicting_rule_id: string;
  target_id: string;
  modalities: string[];
  reason: string;
}

export interface DeonticRuleAssessment {
  rule_id: string;
  target_id: string;
  modality: string;
  active: boolean;
  satisfied_sources: string[];
  missing_sources: string[];
  authority_ids: string[];
  evidence_ids: string[];
}

export interface DeonticGraphSummary {
  total_nodes: number;
  total_rules: number;
  active_rule_count: number;
  inactive_rule_count: number;
  node_types: Record<string, number>;
  modalities: Record<string, number>;
  active_modalities: Record<string, number>;
  governed_target_count: number;
}

export interface DeonticGraphData {
  metadata?: Record<string, unknown>;
  nodes?: Record<string, Partial<DeonticNode>>;
  rules?: Record<string, Partial<DeonticRule>>;
}

export type DeonticGraphRow = Record<string, unknown>;

export class DeonticGraph {
  readonly nodes = new Map<string, DeonticNode>();
  readonly rules = new Map<string, DeonticRule>();
  metadata: Record<string, unknown>;

  constructor(now = new Date().toISOString()) {
    this.metadata = {
      created_at: now,
      last_updated: now,
      version: '1.0',
    };
  }

  addNode(node: DeonticNode): string {
    this.nodes.set(node.id, normalizeNode(node));
    this.updateMetadata();
    return node.id;
  }

  addRule(rule: DeonticRule): string {
    this.rules.set(rule.id, normalizeRule(rule));
    this.updateMetadata();
    return rule.id;
  }

  getNode(nodeId: string): DeonticNode | undefined {
    return this.nodes.get(nodeId);
  }

  rulesForTarget(targetId: string): DeonticRule[] {
    return [...this.rules.values()].filter((rule) => rule.target_id === targetId);
  }

  rulesForSource(sourceId: string): DeonticRule[] {
    return [...this.rules.values()].filter((rule) => rule.source_ids.includes(sourceId));
  }

  activeRules(): DeonticRule[] {
    return [...this.rules.values()].filter((rule) => rule.active);
  }

  inactiveRules(): DeonticRule[] {
    return [...this.rules.values()].filter((rule) => !rule.active);
  }

  modalityDistribution(): Record<string, number> {
    return countBy([...this.rules.values()], (rule) => rule.modality);
  }

  activeModalityDistribution(): Record<string, number> {
    return countBy(this.activeRules(), (rule) => rule.modality);
  }

  nodeTypeDistribution(): Record<string, number> {
    return countBy([...this.nodes.values()], (node) => node.node_type);
  }

  governedTargets(): string[] {
    return unique([...this.rules.values()].map((rule) => rule.target_id));
  }

  summary(): DeonticGraphSummary {
    return {
      total_nodes: this.nodes.size,
      total_rules: this.rules.size,
      active_rule_count: this.activeRules().length,
      inactive_rule_count: this.inactiveRules().length,
      node_types: this.nodeTypeDistribution(),
      modalities: this.modalityDistribution(),
      active_modalities: this.activeModalityDistribution(),
      governed_target_count: this.governedTargets().length,
    };
  }

  assessRules(): DeonticRuleAssessment[] {
    return [...this.rules.values()].map((rule) => {
      const satisfied_sources: string[] = [];
      const missing_sources: string[] = [];
      for (const sourceId of rule.source_ids) {
        const node = this.nodes.get(sourceId);
        if (node?.active) {
          satisfied_sources.push(sourceId);
        } else {
          missing_sources.push(sourceId);
        }
      }
      return {
        rule_id: rule.id,
        target_id: rule.target_id,
        modality: rule.modality,
        active: rule.active,
        satisfied_sources,
        missing_sources,
        authority_ids: [...rule.authority_ids],
        evidence_ids: [...rule.evidence_ids],
      };
    });
  }

  sourceGapSummary(): Record<string, unknown> {
    const assessments = this.assessRules();
    return {
      rule_count: assessments.length,
      fully_supported_rule_count: assessments.filter((assessment) => assessment.missing_sources.length === 0).length,
      rules_with_gaps: assessments.filter((assessment) => assessment.missing_sources.length > 0),
    };
  }

  detectConflicts(options: { onlyActive?: boolean } = {}): DeonticGraphConflict[] {
    const onlyActive = options.onlyActive ?? true;
    const rules = [...this.rules.values()].filter((rule) => rule.active || !onlyActive);
    const conflicts: DeonticGraphConflict[] = [];
    const seenPairs = new Set<string>();

    for (let index = 0; index < rules.length; index += 1) {
      for (const right of rules.slice(index + 1)) {
        const left = rules[index];
        if (left.target_id !== right.target_id || left.predicate !== right.predicate) continue;
        if (!modalitiesConflict(left.modality, right.modality)) continue;
        const pair = [left.id, right.id].sort().join('|');
        if (seenPairs.has(pair)) continue;
        seenPairs.add(pair);
        conflicts.push({
          rule_id: left.id,
          conflicting_rule_id: right.id,
          target_id: left.target_id,
          modalities: [left.modality, right.modality],
          reason: 'Rules govern the same target and predicate with incompatible modalities.',
        });
      }
    }

    return conflicts;
  }

  exportReasoningRows(): Array<Record<string, unknown>> {
    return this.assessRules().map((assessment) => {
      const target = this.nodes.get(assessment.target_id);
      return {
        rule_id: assessment.rule_id,
        target_id: assessment.target_id,
        target_label: target?.label ?? assessment.target_id,
        modality: assessment.modality,
        active: assessment.active,
        satisfied_sources: [...assessment.satisfied_sources],
        missing_sources: [...assessment.missing_sources],
        authority_ids: [...assessment.authority_ids],
        evidence_ids: [...assessment.evidence_ids],
      };
    });
  }

  toDict(): Record<string, unknown> {
    return {
      metadata: { ...this.metadata },
      nodes: Object.fromEntries([...this.nodes.entries()].map(([id, node]) => [id, { ...node, attributes: { ...node.attributes } }])),
      rules: Object.fromEntries(
        [...this.rules.entries()].map(([id, rule]) => [
          id,
          {
            ...rule,
            source_ids: [...rule.source_ids],
            authority_ids: [...rule.authority_ids],
            evidence_ids: [...rule.evidence_ids],
            attributes: { ...rule.attributes },
          },
        ]),
      ),
      summary: this.summary(),
    };
  }

  toJson(): string {
    return JSON.stringify(this.toDict(), null, 2);
  }

  static fromDict(data: DeonticGraphData): DeonticGraph {
    const graph = new DeonticGraph();
    graph.metadata = { ...graph.metadata, ...(data.metadata ?? {}) };
    for (const [nodeId, node] of Object.entries(data.nodes ?? {})) {
      graph.nodes.set(
        nodeId,
        normalizeNode({
          id: String(node.id ?? nodeId),
          node_type: normalizeNodeType(node.node_type),
          label: String(node.label ?? ''),
          active: Boolean(node.active ?? false),
          confidence: Number(node.confidence ?? 0),
          attributes: { ...(node.attributes ?? {}) },
        }),
      );
    }
    for (const [ruleId, rule] of Object.entries(data.rules ?? {})) {
      graph.rules.set(
        ruleId,
        normalizeRule({
          id: String(rule.id ?? ruleId),
          modality: normalizeModality(rule.modality),
          source_ids: toStringList(rule.source_ids),
          target_id: String(rule.target_id ?? ''),
          predicate: String(rule.predicate ?? ''),
          active: Boolean(rule.active ?? false),
          confidence: Number(rule.confidence ?? 0),
          authority_ids: toStringList(rule.authority_ids),
          evidence_ids: toStringList(rule.evidence_ids),
          attributes: { ...(rule.attributes ?? {}) },
        }),
      );
    }
    return graph;
  }

  private updateMetadata(): void {
    this.metadata.last_updated = new Date().toISOString();
  }
}

export class DeonticGraphBuilder {
  private nodeCounter = 0;
  private ruleCounter = 0;

  buildFromMatrix(rows: Iterable<DeonticGraphRow>): DeonticGraph {
    const graph = new DeonticGraph();
    for (const row of rows) {
      if (!row || typeof row !== 'object') continue;
      const targetId = this.ensureNode(graph, row.target_id, {
        label: String(row.target_label ?? row.predicate ?? 'Governed action'),
        node_type: normalizeNodeType(row.target_type),
        active: Boolean(row.target_active ?? false),
        confidence: Number(row.target_confidence ?? 0),
        attributes: objectRecord(row.target_attributes),
      });

      const sourceIds = toArray(row.sources).map((source) => {
        if (source && typeof source === 'object') {
          const item = source as Record<string, unknown>;
          return this.ensureNode(graph, item.id, {
            label: String(item.label ?? item.id ?? 'Condition'),
            node_type: normalizeNodeType(item.node_type, 'condition'),
            active: Boolean(item.active ?? false),
            confidence: Number(item.confidence ?? 0),
            attributes: objectRecord(item.attributes),
          });
        }
        return this.ensureNode(graph, String(source), {
          label: String(source),
          node_type: 'condition',
        });
      });

      const authorityIds = toArray(row.authorities).map((authority) => {
        if (authority && typeof authority === 'object') {
          const item = authority as Record<string, unknown>;
          return this.ensureNode(graph, item.id, {
            label: String(item.label ?? item.id ?? 'Authority'),
            node_type: 'authority',
            attributes: objectRecord(item.attributes),
          });
        }
        return this.ensureNode(graph, String(authority), {
          label: String(authority),
          node_type: 'authority',
        });
      });

      graph.addRule({
        id: String(row.rule_id ?? this.nextRuleId()),
        modality: normalizeModality(row.modality),
        source_ids: sourceIds,
        target_id: targetId,
        predicate: String(row.predicate ?? row.target_label ?? 'governs'),
        active: Boolean(row.active ?? false),
        confidence: Number(row.confidence ?? 0),
        authority_ids: authorityIds,
        evidence_ids: toStringList(row.evidence_ids),
        attributes: objectRecord(row.attributes),
      });
    }
    return graph;
  }

  buildFromFindings(findings: Iterable<Record<string, unknown>>, defaultModality: DeonticGraphModality = 'obligation'): DeonticGraph {
    const rows = [...findings].filter(isRecord).map((finding, index) => ({
      rule_id: finding.id ?? `finding_rule_${index + 1}`,
      modality: finding.modality ?? defaultModality,
      predicate: finding.predicate ?? finding.label ?? 'governs',
      target_id: finding.target_id ?? finding.action_id ?? `action_${index + 1}`,
      target_label: finding.target_label ?? finding.action ?? 'Governed action',
      target_type: finding.target_type ?? 'action',
      sources: finding.sources ?? finding.conditions ?? finding.actors ?? [],
      authorities: finding.authorities ?? [],
      evidence_ids: finding.evidence_ids ?? [],
      confidence: finding.confidence ?? 0,
      active: finding.active ?? false,
      attributes: objectRecord(finding.attributes),
    }));
    return this.buildFromMatrix(rows);
  }

  buildFromStatements(statements: Iterable<Partial<AnalyzedDeonticStatement>>, options: { includeContextAsEvidence?: boolean } = {}): DeonticGraph {
    const includeContextAsEvidence = options.includeContextAsEvidence ?? true;
    const rows = [...statements].filter(isRecord).map((statement, index) => {
      const rowIndex = index + 1;
      const entityLabel = String(statement.entity ?? `Entity ${rowIndex}`).trim();
      const actionLabel = String(statement.action ?? 'Governed action').trim();
      const sourceNodes: Array<Record<string, unknown>> = [
        {
          id: `actor_${safeIdentifier(entityLabel)}`,
          label: entityLabel,
          node_type: 'actor',
          confidence: Number(statement.confidence ?? 0),
        },
      ];

      for (const [conditionIndex, condition] of toStringList(statement.conditions).entries()) {
        sourceNodes.push({
          id: `condition_${rowIndex}_${conditionIndex + 1}`,
          label: condition.trim(),
          node_type: 'condition',
        });
      }

      const sourceName = String(statement.document_source ?? '').trim();
      const authorities = sourceName ? [{ id: `authority_${safeIdentifier(sourceName)}`, label: sourceName }] : [];
      const context = String(statement.context ?? '').trim();

      return {
        rule_id: statement.id ?? `statement_rule_${rowIndex}`,
        modality: normalizeStatementModality(statement.modality),
        predicate: actionLabel,
        target_id: `action_${safeIdentifier(actionLabel)}_${rowIndex}`,
        target_label: actionLabel,
        target_type: 'action',
        sources: sourceNodes,
        authorities,
        evidence_ids: includeContextAsEvidence && context ? [`context_${rowIndex}`] : [],
        confidence: Number(statement.confidence ?? 0),
        attributes: {
          exceptions: toStringList(statement.exceptions),
          document_date: statement.document_date,
          document_id: statement.document_id,
          document_source: statement.document_source,
          context: statement.context,
        },
      };
    });
    return this.buildFromMatrix(rows);
  }

  private ensureNode(
    graph: DeonticGraph,
    nodeId: unknown,
    options: {
      label: string;
      node_type: DeonticNodeType;
      active?: boolean;
      confidence?: number;
      attributes?: Record<string, unknown>;
    },
  ): string {
    const id = String(nodeId || this.nextNodeId(options.node_type));
    if (graph.getNode(id)) return id;
    graph.addNode({
      id,
      node_type: options.node_type,
      label: options.label,
      active: options.active ?? false,
      confidence: options.confidence ?? 0,
      attributes: options.attributes ?? {},
    });
    return id;
  }

  private nextNodeId(nodeType: DeonticNodeType): string {
    this.nodeCounter += 1;
    return `${nodeType}_${this.nodeCounter}`;
  }

  private nextRuleId(): string {
    this.ruleCounter += 1;
    return `rule_${this.ruleCounter}`;
  }
}

export function safeIdentifier(value: string): string {
  return String(value)
    .split('')
    .map((char) => (/[a-z0-9]/i.test(char) ? char.toLowerCase() : '_'))
    .join('')
    .replace(/^_+|_+$/g, '') || 'item';
}

export function modalitiesConflict(left: DeonticGraphModality, right: DeonticGraphModality): boolean {
  const pair = new Set([left, right]);
  return (
    (pair.has('obligation') && pair.has('prohibition')) ||
    (pair.has('entitlement') && pair.has('prohibition'))
  );
}

function normalizeNode(node: DeonticNode): DeonticNode {
  return {
    id: String(node.id),
    node_type: normalizeNodeType(node.node_type),
    label: String(node.label),
    active: Boolean(node.active),
    confidence: Number(node.confidence || 0),
    attributes: objectRecord(node.attributes),
  };
}

function normalizeRule(rule: DeonticRule): DeonticRule {
  return {
    id: String(rule.id),
    modality: normalizeModality(rule.modality),
    source_ids: toStringList(rule.source_ids),
    target_id: String(rule.target_id),
    predicate: String(rule.predicate),
    active: Boolean(rule.active),
    confidence: Number(rule.confidence || 0),
    authority_ids: toStringList(rule.authority_ids),
    evidence_ids: toStringList(rule.evidence_ids),
    attributes: objectRecord(rule.attributes),
  };
}

function normalizeNodeType(value: unknown, fallback: DeonticNodeType = 'action'): DeonticNodeType {
  return ['actor', 'fact', 'condition', 'action', 'outcome', 'authority'].includes(String(value))
    ? (String(value) as DeonticNodeType)
    : fallback;
}

function normalizeModality(value: unknown): DeonticGraphModality {
  const raw = String(value ?? 'obligation').toLowerCase();
  return ['obligation', 'prohibition', 'permission', 'entitlement'].includes(raw) ? (raw as DeonticGraphModality) : 'obligation';
}

function normalizeStatementModality(value: unknown): DeonticGraphModality {
  const raw = String(value ?? 'obligation').toLowerCase() as DeonticStatementModality;
  if (raw === 'permission') return 'permission';
  if (raw === 'prohibition') return 'prohibition';
  return 'obligation';
}

function countBy<T>(values: T[], fn: (value: T) => string): Record<string, number> {
  return values.reduce<Record<string, number>>((counts, value) => {
    const key = fn(value);
    counts[key] = (counts[key] ?? 0) + 1;
    return counts;
  }, {});
}

function unique(values: string[]): string[] {
  return [...new Set(values)];
}

function toStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function toArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function objectRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value) ? { ...(value as Record<string, unknown>) } : {};
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === 'object' && !Array.isArray(value));
}
