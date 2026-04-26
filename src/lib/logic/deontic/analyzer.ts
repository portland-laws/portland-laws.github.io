export type DeonticStatementModality = 'obligation' | 'permission' | 'prohibition';
export type DeonticConflictType = 'direct' | 'conditional' | 'jurisdictional' | 'temporal';

export interface DeonticDocument {
  content?: string;
  title?: string;
  source?: string;
  date?: string;
}

export interface DeonticCorpus {
  documents?: DeonticDocument[];
}

export interface AnalyzedDeonticStatement {
  id: string;
  entity: string;
  modality: DeonticStatementModality;
  action: string;
  document_id: number;
  document_source: string;
  document_date: string;
  context: string;
  confidence: number;
  conditions: string[];
  exceptions: string[];
}

export interface DeonticConflict {
  id: string;
  type: DeonticConflictType;
  severity: 'low' | 'medium' | 'high';
  entities: string[];
  statement1: AnalyzedDeonticStatement;
  statement2: AnalyzedDeonticStatement;
  description: string;
  resolution: string;
}

const PATTERNS: Record<DeonticStatementModality, RegExp[]> = {
  obligation: [
    /(\w+(?:\s+\w+)*)\s+(?:must|shall|should|is required to|has to|ought to)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:has an obligation to|is obligated to)\s+([^.!?]+)/gi,
    /it is (?:mandatory|required|necessary) (?:for\s+)?(\w+(?:\s+\w+)*)\s+to\s+([^.!?]+)/gi,
  ],
  permission: [
    /(\w+(?:\s+\w+)*)\s+(?:may|can|might|is allowed to|is permitted to)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:has the right to|is entitled to)\s+([^.!?]+)/gi,
    /it is (?:permissible|acceptable) (?:for\s+)?(\w+(?:\s+\w+)*)\s+to\s+([^.!?]+)/gi,
  ],
  prohibition: [
    /(\w+(?:\s+\w+)*)\s+(?:must not|shall not|should not|cannot|may not|is not allowed to|is prohibited from)\s+([^.!?]+)/gi,
    /(\w+(?:\s+\w+)*)\s+(?:is forbidden to|is banned from)\s+([^.!?]+)/gi,
    /it is (?:forbidden|prohibited|illegal) (?:for\s+)?(\w+(?:\s+\w+)*)\s+to\s+([^.!?]+)/gi,
  ],
};

export class DeonticAnalyzer {
  extractDeonticStatements(corpus: DeonticCorpus, entityFilter?: string[]): AnalyzedDeonticStatement[] {
    const statements: Array<AnalyzedDeonticStatement & { match_start: number }> = [];
    for (const [documentId, document] of (corpus.documents ?? []).entries()) {
      const content = `${document.content ?? ''} ${document.title ?? ''}`.trim();
      const occupiedRanges: Array<[number, number]> = [];
      for (const modality of ['prohibition', 'obligation', 'permission'] as DeonticStatementModality[]) {
        const patterns = PATTERNS[modality];
        for (const pattern of patterns) {
          for (const match of content.matchAll(pattern)) {
            const start = match.index ?? 0;
            const end = start + match[0].length;
            if (occupiedRanges.some(([rangeStart, rangeEnd]) => start < rangeEnd && end > rangeStart)) {
              continue;
            }
            occupiedRanges.push([start, end]);
            const entity = match[1].trim();
            if (entityFilter?.length && !entityFilter.some((filter) => entity.toLowerCase().includes(filter.toLowerCase()))) {
              continue;
            }
            const action = match[2].trim();
            statements.push({
              id: `stmt_${documentId}_${statements.length}`,
              entity,
              modality,
              action,
              document_id: documentId,
              document_source: document.source ?? 'unknown',
              document_date: document.date ?? new Date(0).toISOString(),
              context: this.getSentenceContext(content, start, end),
              confidence: this.calculateStatementConfidence(entity, action, modality),
              conditions: this.extractConditions(content, start, end),
              exceptions: this.extractExceptions(content, start, end),
              match_start: start,
            });
          }
        }
      }
    }
    return statements
      .sort((left, right) => left.document_id - right.document_id || left.match_start - right.match_start)
      .map(({ match_start: _matchStart, ...statement }) => statement);
  }

  detectDeonticConflicts(statements: AnalyzedDeonticStatement[], conflictTypes: DeonticConflictType[]): DeonticConflict[] {
    const conflicts: DeonticConflict[] = [];
    for (let index = 0; index < statements.length; index += 1) {
      for (let other = index + 1; other < statements.length; other += 1) {
        const conflict = this.checkStatementConflict(statements[index], statements[other], conflictTypes);
        if (conflict) conflicts.push(conflict);
      }
    }
    return conflicts;
  }

  checkStatementConflict(
    stmt1: AnalyzedDeonticStatement,
    stmt2: AnalyzedDeonticStatement,
    conflictTypes: DeonticConflictType[],
  ): DeonticConflict | null {
    if (stmt1.entity.toLowerCase() !== stmt2.entity.toLowerCase()) return null;
    const directConflict = this.actionsAreSimilar(stmt1.action, stmt2.action) && modalitiesConflict(stmt1.modality, stmt2.modality);
    if (conflictTypes.includes('direct') && directConflict) {
      return this.buildConflict(stmt1, stmt2, 'direct', 'high', `Direct conflict: ${stmt1.entity} ${stmt1.modality} vs ${stmt2.modality} ${stmt1.action}`);
    }
    if (conflictTypes.includes('conditional') && stmt1.conditions.length && stmt2.conditions.length && conditionsOverlap(stmt1.conditions, stmt2.conditions) && directConflict) {
      return this.buildConflict(stmt1, stmt2, 'conditional', 'medium', `Conditional conflict: ${stmt1.entity} under overlapping conditions`);
    }
    if (conflictTypes.includes('jurisdictional') && stmt1.document_source !== stmt2.document_source && directConflict) {
      return this.buildConflict(stmt1, stmt2, 'jurisdictional', 'medium', `Jurisdictional conflict between ${stmt1.document_source} and ${stmt2.document_source}`);
    }
    if (conflictTypes.includes('temporal') && stmt1.document_date !== stmt2.document_date && directConflict) {
      return this.buildConflict(stmt1, stmt2, 'temporal', 'low', `Temporal conflict: rule changed between ${stmt1.document_date} and ${stmt2.document_date}`);
    }
    return null;
  }

  actionsAreSimilar(action1: string, action2: string, threshold = 0.7): boolean {
    const words1 = new Set(action1.toLowerCase().split(/\s+/).filter(Boolean));
    const words2 = new Set(action2.toLowerCase().split(/\s+/).filter(Boolean));
    if (words1.size === 0 || words2.size === 0) return false;
    const intersection = [...words1].filter((word) => words2.has(word)).length;
    const union = new Set([...words1, ...words2]).size;
    return intersection / union >= threshold;
  }

  organizeByEntities(statements: AnalyzedDeonticStatement[]): Record<string, AnalyzedDeonticStatement[]> {
    return statements.reduce<Record<string, AnalyzedDeonticStatement[]>>((groups, statement) => {
      groups[statement.entity] ??= [];
      groups[statement.entity].push(statement);
      return groups;
    }, {});
  }

  calculateStatistics(statements: AnalyzedDeonticStatement[], conflicts: DeonticConflict[] = []): Record<string, number> {
    return {
      total_statements: statements.length,
      obligations: statements.filter((statement) => statement.modality === 'obligation').length,
      permissions: statements.filter((statement) => statement.modality === 'permission').length,
      prohibitions: statements.filter((statement) => statement.modality === 'prohibition').length,
      conflicts: conflicts.length,
      average_confidence: statements.length ? statements.reduce((total, statement) => total + statement.confidence, 0) / statements.length : 0,
    };
  }

  getSentenceContext(content: string, start: number, end: number): string {
    const left = content.lastIndexOf('.', start);
    const right = content.indexOf('.', end);
    return content.slice(left === -1 ? 0 : left + 1, right === -1 ? content.length : right + 1).trim();
  }

  calculateStatementConfidence(entity: string, action: string, modality: DeonticStatementModality): number {
    let score = 0.5;
    if (entity.length > 1) score += 0.15;
    if (action.length > 2) score += 0.2;
    if (modality) score += 0.1;
    return Math.min(1, score);
  }

  extractConditions(content: string, start: number, end: number): string[] {
    return extractNearby(content, start, end, [/\bif\s+([^,.!?]+)/gi, /\bwhen\s+([^,.!?]+)/gi, /\bprovided that\s+([^,.!?]+)/gi]);
  }

  extractExceptions(content: string, start: number, end: number): string[] {
    return extractNearby(content, start, end, [/\bunless\s+([^,.!?]+)/gi, /\bexcept\s+(?:for\s+)?([^,.!?]+)/gi]);
  }

  private buildConflict(
    stmt1: AnalyzedDeonticStatement,
    stmt2: AnalyzedDeonticStatement,
    type: DeonticConflictType,
    severity: DeonticConflict['severity'],
    description: string,
  ): DeonticConflict {
    return {
      id: `conflict_${stmt1.id}_${stmt2.id}`,
      type,
      severity,
      entities: [stmt1.entity],
      statement1: stmt1,
      statement2: stmt2,
      description,
      resolution: suggestConflictResolution(stmt1, stmt2, type),
    };
  }
}

function modalitiesConflict(left: DeonticStatementModality, right: DeonticStatementModality): boolean {
  return (
    (left === 'obligation' && right === 'prohibition') ||
    (left === 'prohibition' && right === 'obligation') ||
    (left === 'permission' && right === 'prohibition') ||
    (left === 'prohibition' && right === 'permission')
  );
}

function conditionsOverlap(left: string[], right: string[]): boolean {
  return left.some((condition) => right.some((other) => condition.toLowerCase() === other.toLowerCase()));
}

function suggestConflictResolution(stmt1: AnalyzedDeonticStatement, stmt2: AnalyzedDeonticStatement, type: DeonticConflictType): string {
  if (type === 'temporal') return 'Prefer the newer dated rule when jurisdiction and scope match.';
  if (type === 'jurisdictional') return 'Compare source authority and jurisdiction before applying either rule.';
  if (type === 'conditional') return 'Narrow or prioritize overlapping conditions.';
  return `Review whether ${stmt1.modality} and ${stmt2.modality} apply to the same action and scope.`;
}

function extractNearby(content: string, start: number, end: number, patterns: RegExp[]): string[] {
  const window = content.slice(Math.max(0, start - 160), Math.min(content.length, end + 160)).toLowerCase();
  return [...new Set(patterns.flatMap((pattern) => [...window.matchAll(pattern)].map((match) => match[1].trim())))];
}
