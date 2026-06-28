import {
  DeonticAnalyzer,
  type AnalyzedDeonticStatement,
  type DeonticConflictType,
} from '../deontic/analyzer';

export type NlPolicyConflictSeverity = 'low' | 'medium' | 'high';

export interface NlPolicyDocument {
  id?: string;
  text?: string;
  content?: string;
  title?: string;
  source?: string;
  date?: string;
}

export interface NlPolicyConflictDetectorOptions {
  entityFilter?: string[];
  conflictTypes?: DeonticConflictType[];
  minimumConfidence?: number;
}

export interface NlPolicyConflict {
  id: string;
  type: DeonticConflictType;
  severity: NlPolicyConflictSeverity;
  policy_ids: string[];
  entity: string;
  modalities: [string, string];
  actions: [string, string];
  contexts: [string, string];
  confidence: number;
  description: string;
  resolution: string;
}

export interface NlPolicyConflictDetectionResult {
  conflicts: NlPolicyConflict[];
  statements: AnalyzedDeonticStatement[];
  statistics: {
    total_policies: number;
    total_statements: number;
    conflicts: number;
    average_confidence: number;
  };
}

const DEFAULT_CONFLICT_TYPES: DeonticConflictType[] = [
  'direct',
  'conditional',
  'jurisdictional',
  'temporal',
];

export function detectNlPolicyConflicts(
  policies: NlPolicyDocument[],
  options: NlPolicyConflictDetectorOptions = {},
): NlPolicyConflictDetectionResult {
  const analyzer = new DeonticAnalyzer();
  const normalizedPolicies = policies.map((policy, index) => ({
    content: policy.text ?? policy.content ?? '',
    title: policy.title,
    source: policy.source ?? policy.id ?? `policy_${index}`,
    date: policy.date,
  }));
  const statements = analyzer.extractDeonticStatements(
    { documents: normalizedPolicies },
    options.entityFilter,
  );
  const minimumConfidence = options.minimumConfidence ?? 0;
  const confidentStatements = statements.filter(
    (statement) => statement.confidence >= minimumConfidence,
  );
  const rawConflicts = analyzer.detectDeonticConflicts(
    confidentStatements,
    options.conflictTypes ?? DEFAULT_CONFLICT_TYPES,
  );
  const conflicts = rawConflicts.map<NlPolicyConflict>((conflict) => {
    const confidence = Math.min(conflict.statement1.confidence, conflict.statement2.confidence);
    return {
      id: conflict.id,
      type: conflict.type,
      severity: conflict.severity,
      policy_ids: [conflict.statement1.document_source, conflict.statement2.document_source],
      entity: conflict.entities[0] ?? conflict.statement1.entity,
      modalities: [conflict.statement1.modality, conflict.statement2.modality],
      actions: [conflict.statement1.action, conflict.statement2.action],
      contexts: [conflict.statement1.context, conflict.statement2.context],
      confidence,
      description: conflict.description,
      resolution: conflict.resolution,
    };
  });
  return {
    conflicts,
    statements: confidentStatements,
    statistics: {
      total_policies: policies.length,
      total_statements: confidentStatements.length,
      conflicts: conflicts.length,
      average_confidence: confidentStatements.length
        ? confidentStatements.reduce((total, statement) => total + statement.confidence, 0) /
          confidentStatements.length
        : 0,
    },
  };
}

export class NlPolicyConflictDetector {
  detect(
    policies: NlPolicyDocument[],
    options: NlPolicyConflictDetectorOptions = {},
  ): NlPolicyConflictDetectionResult {
    return detectNlPolicyConflicts(policies, options);
  }
}
