export type ExpansionRuleKind = 'literal' | 'alpha' | 'beta' | 'gamma' | 'delta';
export type ExpansionStrategy = 'depth-first' | 'breadth-first';

export interface ExpansionFormula {
  id: string;
  text: string;
  rule: ExpansionRuleKind;
  children?: ExpansionFormula[];
  branches?: ExpansionFormula[][];
  witness?: string;
}

export interface ExpansionDiagnostic {
  branchId: string;
  code: 'closed-branch' | 'open-branch' | 'empty-beta' | 'missing-witness';
  message: string;
  formulaId?: string;
}

export interface ExpansionBranch {
  id: string;
  formulas: ExpansionFormula[];
  closed: boolean;
  diagnostics: ExpansionDiagnostic[];
}

export interface ExpansionResult {
  strategy: ExpansionStrategy;
  branches: ExpansionBranch[];
  diagnostics: ExpansionDiagnostic[];
  appliedRuleIds: string[];
}

export interface InteractiveExpansionNode {
  id: string;
  label: string;
  branchId: string;
  rule: ExpansionRuleKind;
  status: 'open' | 'closed';
  witness?: string;
}

export interface InteractiveExpansionEdge {
  from: string;
  to: string;
  branchId: string;
  kind: 'same-branch' | 'split-branch';
}

export interface InteractiveExpansionRenderState {
  strategy: ExpansionStrategy;
  nodes: InteractiveExpansionNode[];
  edges: InteractiveExpansionEdge[];
  diagnostics: ExpansionDiagnostic[];
}

const complementOf = (text: string): string => {
  const trimmed = text.trim();
  return trimmed.startsWith('not ') ? trimmed.slice(4).trim() : `not ${trimmed}`;
};

const makeBranchId = (parentId: string, index: number): string => `${parentId}.${index + 1}`;

const hasContradiction = (formulas: ExpansionFormula[]): boolean => {
  const seen = new Set(formulas.map((formula) => formula.text.trim()));
  for (const formula of formulas) {
    if (seen.has(complementOf(formula.text))) {
      return true;
    }
  }
  return false;
};

const collectRuleIds = (formula: ExpansionFormula, applied: string[]): void => {
  if (formula.rule !== 'literal') {
    applied.push(formula.id);
  }
  for (const child of formula.children ?? []) {
    collectRuleIds(child, applied);
  }
  for (const branch of formula.branches ?? []) {
    for (const child of branch) {
      collectRuleIds(child, applied);
    }
  }
};

const appendSequential = (
  formulas: ExpansionFormula[],
  source: ExpansionFormula,
): ExpansionFormula[] => {
  const next = formulas.slice();
  for (const child of source.children ?? []) {
    next.push(child);
  }
  return next;
};

const expandFormula = (
  branchId: string,
  formulas: ExpansionFormula[],
  source: ExpansionFormula,
): ExpansionBranch[] => {
  if (source.rule === 'beta') {
    const betaBranches = source.branches ?? [];
    if (betaBranches.length === 0) {
      return [
        {
          id: branchId,
          formulas,
          closed: false,
          diagnostics: [
            {
              branchId,
              code: 'empty-beta',
              formulaId: source.id,
              message: `Beta formula ${source.id} has no branch alternatives.`,
            },
          ],
        },
      ];
    }
    return betaBranches.map((branch, index) =>
      finalizeBranch(makeBranchId(branchId, index), formulas.concat(branch)),
    );
  }

  if (source.rule === 'delta' && !source.witness) {
    const diagnostic: ExpansionDiagnostic = {
      branchId,
      code: 'missing-witness',
      formulaId: source.id,
      message: `Delta formula ${source.id} requires a deterministic witness.`,
    };
    const finalized = finalizeBranch(branchId, appendSequential(formulas, source));
    return [{ ...finalized, diagnostics: finalized.diagnostics.concat(diagnostic) }];
  }

  return [finalizeBranch(branchId, appendSequential(formulas, source))];
};

const finalizeBranch = (branchId: string, formulas: ExpansionFormula[]): ExpansionBranch => {
  const closed = hasContradiction(formulas);
  const diagnostic: ExpansionDiagnostic = closed
    ? {
        branchId,
        code: 'closed-branch',
        message: `Branch ${branchId} closes by complementary literals.`,
      }
    : { branchId, code: 'open-branch', message: `Branch ${branchId} remains open.` };
  return { id: branchId, formulas, closed, diagnostics: [diagnostic] };
};

export const expandFormulaTree = (
  root: ExpansionFormula,
  strategy: ExpansionStrategy = 'depth-first',
): ExpansionResult => {
  const seed = finalizeBranch('b1', [root]);
  const work: ExpansionBranch[] = [seed];
  const completed: ExpansionBranch[] = [];
  const appliedRuleIds: string[] = [];

  while (work.length > 0) {
    const branch = strategy === 'depth-first' ? work.pop()! : work.shift()!;
    const source = branch.formulas.find((formula) => formula.rule !== 'literal');
    if (!source || branch.closed) {
      completed.push(branch);
      continue;
    }

    collectRuleIds(source, appliedRuleIds);
    const expanded = expandFormula(
      branch.id,
      branch.formulas.filter((formula) => formula.id !== source.id),
      source,
    );
    if (strategy === 'depth-first') {
      work.push(...expanded.reverse());
    } else {
      work.push(...expanded);
    }
  }

  const diagnostics = completed.flatMap((branch) => branch.diagnostics);
  return { strategy, branches: completed, diagnostics, appliedRuleIds };
};

export const renderInteractiveExpansion = (
  result: ExpansionResult,
): InteractiveExpansionRenderState => {
  const nodes: InteractiveExpansionNode[] = [];
  const edges: InteractiveExpansionEdge[] = [];

  for (const branch of result.branches) {
    branch.formulas.forEach((formula, index) => {
      nodes.push({
        id: `${branch.id}:${formula.id}`,
        label: formula.text,
        branchId: branch.id,
        rule: formula.rule,
        status: branch.closed ? 'closed' : 'open',
        witness: formula.witness,
      });
      if (index > 0) {
        edges.push({
          from: `${branch.id}:${branch.formulas[index - 1].id}`,
          to: `${branch.id}:${formula.id}`,
          branchId: branch.id,
          kind: branch.id.includes('.') ? 'split-branch' : 'same-branch',
        });
      }
    });
  }

  return { strategy: result.strategy, nodes, edges, diagnostics: result.diagnostics };
};
