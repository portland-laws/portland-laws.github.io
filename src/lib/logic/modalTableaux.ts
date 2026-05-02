export type ModalFormula =
  | { kind: 'atom'; name: string }
  | { kind: 'not'; formula: ModalFormula }
  | { kind: 'and'; formulas: ModalFormula[] }
  | { kind: 'or'; formulas: ModalFormula[] }
  | { kind: 'box'; formula: ModalFormula }
  | { kind: 'diamond'; formula: ModalFormula };

export interface ModalTableauxOptions {
  maxDepth?: number;
  maxBranches?: number;
}

export interface ModalTableauxWorld {
  id: string;
  depth: number;
  trueAtoms: string[];
  falseAtoms: string[];
}

export interface ModalTableauxResult {
  satisfiable: boolean;
  status: 'satisfiable' | 'unsatisfiable' | 'inconclusive';
  reason: string;
  worlds: ModalTableauxWorld[];
  metadata: {
    logic: 'modal-k';
    backend: 'typescript-tableaux';
    browserNative: true;
    serverCallsAllowed: false;
    pythonFallback: false;
    maxDepth: number;
    branchesExplored: number;
  };
}

interface WorldState {
  id: string;
  depth: number;
  pending: ModalFormula[];
  trueAtoms: string[];
  falseAtoms: string[];
  boxes: ModalFormula[];
}

interface BranchState {
  worlds: WorldState[];
  branchesExplored: number;
}

type BranchOutcome =
  | { kind: 'open'; branch: BranchState }
  | { kind: 'closed'; branchesExplored: number }
  | { kind: 'inconclusive'; branch: BranchState; reason: string };

export function atom(name: string): ModalFormula {
  return { kind: 'atom', name };
}

export function not(formula: ModalFormula): ModalFormula {
  return { kind: 'not', formula };
}

export function box(formula: ModalFormula): ModalFormula {
  return { kind: 'box', formula };
}

export function diamond(formula: ModalFormula): ModalFormula {
  return { kind: 'diamond', formula };
}

export function checkModalTableaux(
  formula: ModalFormula,
  options: ModalTableauxOptions = {},
): ModalTableauxResult {
  const maxDepth = options.maxDepth ?? 8;
  const maxBranches = options.maxBranches ?? 128;
  const root: BranchState = {
    worlds: [{ id: 'w0', depth: 0, pending: [formula], trueAtoms: [], falseAtoms: [], boxes: [] }],
    branchesExplored: 1,
  };
  const outcome = expandBranch(root, maxDepth, maxBranches);
  const branchesExplored =
    outcome.kind === 'closed' ? outcome.branchesExplored : outcome.branch.branchesExplored;
  const worlds = outcome.kind === 'closed' ? [] : toPublicWorlds(outcome.branch.worlds);

  if (outcome.kind === 'open') {
    return result(true, 'satisfiable', 'open branch found', worlds, maxDepth, branchesExplored);
  }
  if (outcome.kind === 'inconclusive') {
    return result(false, 'inconclusive', outcome.reason, worlds, maxDepth, branchesExplored);
  }
  return result(false, 'unsatisfiable', 'all branches closed', worlds, maxDepth, branchesExplored);
}

function expandBranch(branch: BranchState, maxDepth: number, maxBranches: number): BranchOutcome {
  while (true) {
    const world = branch.worlds.find((candidate) => candidate.pending.length > 0);
    if (!world) return { kind: 'open', branch };

    const formula = world.pending.shift();
    if (!formula) continue;

    if (formula.kind === 'atom') {
      if (world.falseAtoms.includes(formula.name))
        return { kind: 'closed', branchesExplored: branch.branchesExplored };
      addUnique(world.trueAtoms, formula.name);
      continue;
    }

    if (formula.kind === 'not') {
      const inner = formula.formula;
      if (inner.kind === 'atom') {
        if (world.trueAtoms.includes(inner.name))
          return { kind: 'closed', branchesExplored: branch.branchesExplored };
        addUnique(world.falseAtoms, inner.name);
      } else if (inner.kind === 'not') {
        world.pending.unshift(inner.formula);
      } else if (inner.kind === 'and') {
        const fork = inner.formulas.map((child) => not(child));
        return expandDisjunction(branch, world.id, fork, maxDepth, maxBranches);
      } else if (inner.kind === 'or') {
        world.pending.unshift(...inner.formulas.map((child) => not(child)));
      } else if (inner.kind === 'box') {
        world.pending.unshift(diamond(not(inner.formula)));
      } else {
        world.pending.unshift(box(not(inner.formula)));
      }
      continue;
    }

    if (formula.kind === 'and') {
      world.pending.unshift(...formula.formulas);
    } else if (formula.kind === 'or') {
      return expandDisjunction(branch, world.id, formula.formulas, maxDepth, maxBranches);
    } else if (formula.kind === 'box') {
      world.boxes.push(formula.formula);
    } else if (formula.kind === 'diamond') {
      if (world.depth >= maxDepth) {
        return {
          kind: 'inconclusive',
          branch,
          reason: 'modal depth bound reached before satisfying diamond',
        };
      }
      const child: WorldState = {
        id: `w${branch.worlds.length}`,
        depth: world.depth + 1,
        pending: [formula.formula, ...world.boxes],
        trueAtoms: [],
        falseAtoms: [],
        boxes: [],
      };
      branch.worlds.push(child);
    }
  }
}

function expandDisjunction(
  branch: BranchState,
  worldId: string,
  formulas: ModalFormula[],
  maxDepth: number,
  maxBranches: number,
): BranchOutcome {
  let explored = branch.branchesExplored;
  for (const formula of formulas) {
    if (explored >= maxBranches) {
      return {
        kind: 'inconclusive',
        branch,
        reason: 'branch bound reached before an open branch was found',
      };
    }
    const next = cloneBranch(branch);
    next.branchesExplored = explored + 1;
    next.worlds.find((world) => world.id === worldId)?.pending.unshift(formula);
    const outcome = expandBranch(next, maxDepth, maxBranches);
    explored =
      outcome.kind === 'closed' ? outcome.branchesExplored : outcome.branch.branchesExplored;
    if (outcome.kind !== 'closed') return outcome;
  }
  return { kind: 'closed', branchesExplored: explored };
}

function cloneBranch(branch: BranchState): BranchState {
  return {
    branchesExplored: branch.branchesExplored,
    worlds: branch.worlds.map((world) => ({
      id: world.id,
      depth: world.depth,
      pending: [...world.pending],
      trueAtoms: [...world.trueAtoms],
      falseAtoms: [...world.falseAtoms],
      boxes: [...world.boxes],
    })),
  };
}

function addUnique(values: string[], value: string): void {
  if (!values.includes(value)) values.push(value);
}

function toPublicWorlds(worlds: WorldState[]): ModalTableauxWorld[] {
  return worlds.map((world) => ({
    id: world.id,
    depth: world.depth,
    trueAtoms: [...world.trueAtoms].sort(),
    falseAtoms: [...world.falseAtoms].sort(),
  }));
}

function result(
  satisfiable: boolean,
  status: ModalTableauxResult['status'],
  reason: string,
  worlds: ModalTableauxWorld[],
  maxDepth: number,
  branchesExplored: number,
): ModalTableauxResult {
  return {
    satisfiable,
    status,
    reason,
    worlds,
    metadata: {
      logic: 'modal-k',
      backend: 'typescript-tableaux',
      browserNative: true,
      serverCallsAllowed: false,
      pythonFallback: false,
      maxDepth,
      branchesExplored,
    },
  };
}
