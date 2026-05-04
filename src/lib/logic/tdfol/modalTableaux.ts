import { substituteFormula } from './ast';
import type {
  TdfolBinaryFormula,
  TdfolDeonticFormula,
  TdfolFormula,
  TdfolQuantifiedFormula,
  TdfolTemporalFormula,
  TdfolTerm,
  TdfolUnaryFormula,
} from './ast';
import { formatTdfolFormula } from './formatter';
import type {
  TdfolModalLogicType,
  TdfolTableauxBranchLike,
  TdfolTableauxWorldLike,
} from './countermodels';

export interface TdfolTableauxResult {
  isValid: boolean;
  closedBranches: number;
  totalBranches: number;
  openBranch?: TdfolTableauxBranch;
  proofSteps: string[];
}

export interface TdfolModalTableauxOptions {
  logicType?: TdfolModalLogicType;
  maxWorlds?: number;
  maxDepth?: number;
}

export class TdfolTableauxWorld implements TdfolTableauxWorldLike {
  readonly id: number;
  readonly positive = new Map<string, TdfolFormula>();
  readonly negative = new Map<string, TdfolFormula>();

  constructor(id: number) {
    this.id = id;
  }

  get formulas(): TdfolFormula[] {
    return [...this.positive.values()];
  }

  get negatedFormulas(): TdfolFormula[] {
    return [...this.negative.values()];
  }

  addFormula(formula: TdfolFormula, negated = false): void {
    (negated ? this.negative : this.positive).set(formulaKey(formula), formula);
  }

  removeFormula(formula: TdfolFormula, negated = false): void {
    (negated ? this.negative : this.positive).delete(formulaKey(formula));
  }

  hasFormula(formula: TdfolFormula, negated = false): boolean {
    return (negated ? this.negative : this.positive).has(formulaKey(formula));
  }

  hasContradiction(): boolean {
    for (const key of this.positive.keys()) {
      if (this.negative.has(key)) {
        return true;
      }
    }
    return false;
  }

  copy(): TdfolTableauxWorld {
    const world = new TdfolTableauxWorld(this.id);
    for (const formula of this.positive.values()) world.addFormula(formula);
    for (const formula of this.negative.values()) world.addFormula(formula, true);
    return world;
  }
}

export class TdfolTableauxBranch implements TdfolTableauxBranchLike {
  readonly worlds = new Map<number, TdfolTableauxWorld>();
  readonly accessibility = new Map<number, Set<number>>();
  readonly boxHistory = new Map<number, Map<string, TdfolFormula>>();
  readonly negDiamondHistory = new Map<number, Map<string, TdfolFormula>>();
  currentWorld = 0;
  isClosed = false;
  nextWorldId = 1;

  createWorld(): TdfolTableauxWorld {
    const world = new TdfolTableauxWorld(this.nextWorldId);
    this.worlds.set(world.id, world);
    this.accessibility.set(world.id, new Set());
    this.nextWorldId += 1;
    return world;
  }

  addWorld(world: TdfolTableauxWorld): void {
    this.worlds.set(world.id, world);
    this.accessibility.set(world.id, this.accessibility.get(world.id) ?? new Set());
    this.nextWorldId = Math.max(this.nextWorldId, world.id + 1);
  }

  addAccessibility(fromWorld: number, toWorld: number): void {
    this.accessibility.set(fromWorld, this.accessibility.get(fromWorld) ?? new Set());
    this.accessibility.get(fromWorld)?.add(toWorld);
  }

  getAccessibleWorlds(fromWorld: number): Set<number> {
    return new Set(this.accessibility.get(fromWorld) ?? []);
  }

  closeBranch(): void {
    this.isClosed = true;
  }

  rememberBox(worldId: number, formula: TdfolFormula): void {
    rememberFormula(this.boxHistory, worldId, formula);
  }

  getBoxHistory(worldId: number): TdfolFormula[] {
    return [...(this.boxHistory.get(worldId)?.values() ?? [])];
  }

  rememberNegDiamond(worldId: number, formula: TdfolFormula): void {
    rememberFormula(this.negDiamondHistory, worldId, formula);
  }

  getNegDiamondHistory(worldId: number): TdfolFormula[] {
    return [...(this.negDiamondHistory.get(worldId)?.values() ?? [])];
  }

  copy(): TdfolTableauxBranch {
    const branch = new TdfolTableauxBranch();
    for (const [id, world] of this.worlds.entries()) branch.worlds.set(id, world.copy());
    for (const [id, targets] of this.accessibility.entries())
      branch.accessibility.set(id, new Set(targets));
    branch.currentWorld = this.currentWorld;
    branch.isClosed = this.isClosed;
    branch.nextWorldId = this.nextWorldId;
    branch.copyHistoryFrom(this.boxHistory, branch.boxHistory);
    branch.copyHistoryFrom(this.negDiamondHistory, branch.negDiamondHistory);
    return branch;
  }

  private copyHistoryFrom(
    source: Map<number, Map<string, TdfolFormula>>,
    target: Map<number, Map<string, TdfolFormula>>,
  ): void {
    for (const [worldId, formulas] of source.entries()) {
      target.set(worldId, new Map(formulas));
    }
  }
}

export class TdfolModalTableaux {
  readonly logicType: TdfolModalLogicType;
  readonly maxWorlds: number;
  readonly maxDepth: number;

  constructor(options: TdfolModalTableauxOptions = {}) {
    this.logicType = options.logicType ?? 'K';
    this.maxWorlds = options.maxWorlds ?? 100;
    this.maxDepth = options.maxDepth ?? 50;
  }

  prove(formula: TdfolFormula): TdfolTableauxResult {
    const initialBranch = new TdfolTableauxBranch();
    const root = new TdfolTableauxWorld(0);
    root.addFormula(formula, true);
    initialBranch.addWorld(root);
    if (this.isReflexiveLogic()) {
      initialBranch.addAccessibility(0, 0);
    }

    let branches = [initialBranch];
    const proofSteps: string[] = [];

    for (let depth = 0; depth < this.maxDepth; depth += 1) {
      const nextBranches: TdfolTableauxBranch[] = [];
      for (const branch of branches) {
        if (branch.isClosed) {
          nextBranches.push(branch);
          continue;
        }
        const expanded = this.expandBranch(branch, proofSteps);
        nextBranches.push(...(expanded ?? [branch]));
      }

      branches = nextBranches;
      const closedCount = branches.filter((branch) => branch.isClosed).length;
      if (closedCount === branches.length) {
        return {
          isValid: true,
          closedBranches: closedCount,
          totalBranches: branches.length,
          proofSteps,
        };
      }
      if (!branches.some((branch) => !branch.isClosed && this.canExpand(branch))) {
        break;
      }
    }

    const closedCount = branches.filter((branch) => branch.isClosed).length;
    return {
      isValid: false,
      closedBranches: closedCount,
      totalBranches: branches.length,
      openBranch: branches.find((branch) => !branch.isClosed),
      proofSteps,
    };
  }

  private canExpand(branch: TdfolTableauxBranch): boolean {
    if (branch.isClosed) return false;
    for (const world of branch.worlds.values()) {
      if ([...world.positive.values(), ...world.negative.values()].some(needsExpansion)) {
        return true;
      }
    }
    return false;
  }

  private expandBranch(
    branch: TdfolTableauxBranch,
    proofSteps: string[],
  ): TdfolTableauxBranch[] | undefined {
    this.closeContradictoryWorlds(branch, proofSteps);
    if (branch.isClosed) return [branch];

    for (const [worldId, world] of branch.worlds.entries()) {
      for (const formula of [...world.positive.values()]) {
        if (needsExpansion(formula))
          return this.expandFormula(branch, worldId, formula, false, proofSteps);
      }
      for (const formula of [...world.negative.values()]) {
        if (needsExpansion(formula))
          return this.expandFormula(branch, worldId, formula, true, proofSteps);
      }
    }
    return undefined;
  }

  private expandFormula(
    branch: TdfolTableauxBranch,
    worldId: number,
    formula: TdfolFormula,
    negated: boolean,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    const world = branch.worlds.get(worldId);
    if (!world || !world.hasFormula(formula, negated)) return [branch];
    world.removeFormula(formula, negated);

    let branches: TdfolTableauxBranch[];
    if (formula.kind === 'binary')
      branches = this.expandBinary(branch, worldId, formula, negated, proofSteps);
    else if (formula.kind === 'unary')
      branches = this.expandUnary(branch, worldId, formula, negated, proofSteps);
    else if (formula.kind === 'quantified')
      branches = this.expandQuantified(branch, worldId, formula, negated, proofSteps);
    else if (formula.kind === 'temporal')
      branches = this.expandTemporal(branch, worldId, formula, negated, proofSteps);
    else if (formula.kind === 'deontic')
      branches = this.expandDeontic(branch, worldId, formula, negated, proofSteps);
    else {
      world.addFormula(formula, negated);
      branches = [branch];
    }

    for (const expandedBranch of branches) {
      this.closeContradictoryWorlds(expandedBranch, proofSteps);
    }
    return branches;
  }

  private expandBinary(
    branch: TdfolTableauxBranch,
    worldId: number,
    formula: TdfolBinaryFormula,
    negated: boolean,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    const world = branch.worlds.get(worldId);
    if (!world) return [branch];

    if (formula.operator === 'AND') {
      if (!negated) {
        world.addFormula(formula.left);
        world.addFormula(formula.right);
        proofSteps.push(`AND expansion at world ${worldId}`);
        return [branch];
      }
      return this.split(
        branch,
        worldId,
        formula.left,
        true,
        formula.right,
        true,
        `Negated AND split at world ${worldId}`,
        proofSteps,
      );
    }

    if (formula.operator === 'OR') {
      if (!negated) {
        return this.split(
          branch,
          worldId,
          formula.left,
          false,
          formula.right,
          false,
          `OR split at world ${worldId}`,
          proofSteps,
        );
      }
      world.addFormula(formula.left, true);
      world.addFormula(formula.right, true);
      proofSteps.push(`Negated OR expansion at world ${worldId}`);
      return [branch];
    }

    if (formula.operator === 'IMPLIES') {
      if (!negated) {
        return this.split(
          branch,
          worldId,
          formula.left,
          true,
          formula.right,
          false,
          `IMPLIES split at world ${worldId}`,
          proofSteps,
        );
      }
      world.addFormula(formula.left);
      world.addFormula(formula.right, true);
      proofSteps.push(`Negated IMPLIES expansion at world ${worldId}`);
      return [branch];
    }

    if (formula.operator === 'IFF') {
      if (!negated) {
        world.addFormula({
          kind: 'binary',
          operator: 'IMPLIES',
          left: formula.left,
          right: formula.right,
        });
        world.addFormula({
          kind: 'binary',
          operator: 'IMPLIES',
          left: formula.right,
          right: formula.left,
        });
        proofSteps.push(`IFF expansion at world ${worldId}`);
        return [branch];
      }
      return this.split(
        branch,
        worldId,
        { kind: 'binary', operator: 'IMPLIES', left: formula.left, right: formula.right },
        true,
        { kind: 'binary', operator: 'IMPLIES', left: formula.right, right: formula.left },
        true,
        `Negated IFF split at world ${worldId}`,
        proofSteps,
      );
    }

    return [branch];
  }

  private expandUnary(
    branch: TdfolTableauxBranch,
    worldId: number,
    formula: TdfolUnaryFormula,
    negated: boolean,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    branch.worlds.get(worldId)?.addFormula(formula.formula, !negated);
    proofSteps.push(`Double negation at world ${worldId}`);
    return [branch];
  }

  private expandQuantified(
    branch: TdfolTableauxBranch,
    worldId: number,
    formula: TdfolQuantifiedFormula,
    negated: boolean,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    const world = branch.worlds.get(worldId);
    if (!world) return [branch];

    const constants = collectBranchConstants(branch);
    const witness =
      formula.quantifier === 'FORALL'
        ? negated
          ? makeWitness(formula, worldId)
          : (constants[0] ?? makeGammaConstant(formula))
        : negated
          ? (constants[0] ?? makeGammaConstant(formula))
          : makeWitness(formula, worldId);
    const instantiated = substituteFormula(formula.formula, formula.variable.name, witness);
    world.addFormula(instantiated, negated);
    proofSteps.push(
      `${formula.quantifier} instantiation at world ${worldId} with ${formatTermKey(witness)}`,
    );
    return [branch];
  }

  private expandTemporal(
    branch: TdfolTableauxBranch,
    worldId: number,
    formula: TdfolTemporalFormula,
    negated: boolean,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    if (formula.operator === 'ALWAYS') {
      if (!negated) {
        branch.rememberBox(worldId, formula.formula);
        let accessible = branch.getAccessibleWorlds(worldId);
        if (accessible.size === 0 && this.isSerialLogic()) {
          const newWorld = this.createAccessibleWorld(branch, worldId);
          accessible = new Set([newWorld.id]);
        }
        for (const target of accessible) branch.worlds.get(target)?.addFormula(formula.formula);
        if (this.isReflexiveLogic()) branch.worlds.get(worldId)?.addFormula(formula.formula);
        proofSteps.push(`BOX expansion at world ${worldId} to ${accessible.size} worlds`);
        return [branch];
      }
      const newWorld = this.createAccessibleWorld(branch, worldId);
      newWorld.addFormula(formula.formula, true);
      this.propagateModalHistories(branch, worldId, newWorld);
      this.applyS5WorldLinks(branch, newWorld);
      proofSteps.push(`Negated BOX: created world ${newWorld.id}`);
      return [branch];
    }

    if (formula.operator === 'EVENTUALLY') {
      if (!negated) {
        const newWorld = this.createAccessibleWorld(branch, worldId);
        newWorld.addFormula(formula.formula);
        this.propagateModalHistories(branch, worldId, newWorld);
        this.applyS5WorldLinks(branch, newWorld);
        proofSteps.push(`DIAMOND: created world ${newWorld.id}`);
        return [branch];
      }
      branch.rememberNegDiamond(worldId, formula.formula);
      for (const target of branch.getAccessibleWorlds(worldId))
        branch.worlds.get(target)?.addFormula(formula.formula, true);
      proofSteps.push(`Negated DIAMOND expansion at world ${worldId}`);
      return [branch];
    }

    return [branch];
  }

  private expandDeontic(
    branch: TdfolTableauxBranch,
    worldId: number,
    formula: TdfolDeonticFormula,
    negated: boolean,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    if (formula.operator === 'OBLIGATION') {
      return this.expandTemporal(
        branch,
        worldId,
        { kind: 'temporal', operator: 'ALWAYS', formula: formula.formula },
        negated,
        proofSteps,
      );
    }
    if (formula.operator === 'PERMISSION') {
      return this.expandTemporal(
        branch,
        worldId,
        { kind: 'temporal', operator: 'EVENTUALLY', formula: formula.formula },
        negated,
        proofSteps,
      );
    }
    if (formula.operator === 'PROHIBITION') {
      return this.expandTemporal(
        branch,
        worldId,
        { kind: 'temporal', operator: 'ALWAYS', formula: formula.formula },
        !negated,
        proofSteps,
      );
    }
    return [branch];
  }

  private split(
    branch: TdfolTableauxBranch,
    worldId: number,
    left: TdfolFormula,
    leftNegated: boolean,
    right: TdfolFormula,
    rightNegated: boolean,
    step: string,
    proofSteps: string[],
  ): TdfolTableauxBranch[] {
    const leftBranch = branch.copy();
    const rightBranch = branch.copy();
    leftBranch.worlds.get(worldId)?.addFormula(left, leftNegated);
    rightBranch.worlds.get(worldId)?.addFormula(right, rightNegated);
    proofSteps.push(step);
    return [leftBranch, rightBranch];
  }

  private createAccessibleWorld(
    branch: TdfolTableauxBranch,
    fromWorld: number,
  ): TdfolTableauxWorld {
    if (branch.worlds.size >= this.maxWorlds) {
      throw new Error(`Modal tableaux world budget exceeded (${this.maxWorlds})`);
    }
    const world = branch.createWorld();
    branch.addAccessibility(fromWorld, world.id);
    if (this.isReflexiveLogic()) branch.addAccessibility(world.id, world.id);
    return world;
  }

  private propagateModalHistories(
    branch: TdfolTableauxBranch,
    sourceWorld: number,
    targetWorld: TdfolTableauxWorld,
  ): void {
    for (const body of this.getPropagatedBoxes(branch, sourceWorld)) targetWorld.addFormula(body);
    for (const body of this.getPropagatedNegDiamonds(branch, sourceWorld))
      targetWorld.addFormula(body, true);
  }

  private getPropagatedBoxes(branch: TdfolTableauxBranch, worldId: number): TdfolFormula[] {
    const formulas = new Map<string, TdfolFormula>();
    for (const body of branch.getBoxHistory(worldId)) formulas.set(formulaKey(body), body);
    for (const formula of branch.worlds.get(worldId)?.formulas ?? []) {
      if (formula.kind === 'temporal' && formula.operator === 'ALWAYS')
        formulas.set(formulaKey(formula.formula), formula.formula);
    }
    if (this.logicType === 'S4' || this.logicType === 'S5') {
      for (const ancestor of this.getAncestorWorlds(branch, worldId)) {
        for (const body of branch.getBoxHistory(ancestor)) formulas.set(formulaKey(body), body);
      }
    }
    return [...formulas.values()];
  }

  private getPropagatedNegDiamonds(branch: TdfolTableauxBranch, worldId: number): TdfolFormula[] {
    const formulas = new Map<string, TdfolFormula>();
    for (const body of branch.getNegDiamondHistory(worldId)) formulas.set(formulaKey(body), body);
    if (this.logicType === 'S4' || this.logicType === 'S5') {
      for (const ancestor of this.getAncestorWorlds(branch, worldId)) {
        for (const body of branch.getNegDiamondHistory(ancestor))
          formulas.set(formulaKey(body), body);
      }
    }
    return [...formulas.values()];
  }

  private getAncestorWorlds(branch: TdfolTableauxBranch, worldId: number): number[] {
    const ancestors = new Set<number>();
    const queue = [worldId];
    while (queue.length > 0) {
      const current = queue.pop();
      if (current === undefined) continue;
      for (const [source, targets] of branch.accessibility.entries()) {
        if (targets.has(current) && !ancestors.has(source)) {
          ancestors.add(source);
          queue.push(source);
        }
      }
    }
    return [...ancestors];
  }

  private applyS5WorldLinks(branch: TdfolTableauxBranch, newWorld: TdfolTableauxWorld): void {
    if (this.logicType !== 'S5') return;
    for (const worldId of branch.worlds.keys()) {
      if (worldId === newWorld.id) continue;
      branch.addAccessibility(worldId, newWorld.id);
      branch.addAccessibility(newWorld.id, worldId);
      for (const body of branch.getBoxHistory(worldId)) newWorld.addFormula(body);
    }
  }

  private closeContradictoryWorlds(branch: TdfolTableauxBranch, proofSteps: string[]): void {
    if (branch.isClosed) return;
    for (const [worldId, world] of branch.worlds.entries()) {
      if (world.hasContradiction()) {
        branch.closeBranch();
        proofSteps.push(`Branch closed: contradiction at world ${worldId}`);
        return;
      }
    }
  }

  private isReflexiveLogic(): boolean {
    return this.logicType === 'T' || this.logicType === 'S4' || this.logicType === 'S5';
  }

  private isSerialLogic(): boolean {
    return this.logicType === 'D' || this.logicType === 'S4' || this.logicType === 'S5';
  }
}

export function proveTdfolModalFormula(
  formula: TdfolFormula,
  logicType: TdfolModalLogicType = 'K',
): TdfolTableauxResult {
  return new TdfolModalTableaux({ logicType }).prove(formula);
}

function rememberFormula(
  history: Map<number, Map<string, TdfolFormula>>,
  worldId: number,
  formula: TdfolFormula,
): void {
  const formulas = history.get(worldId) ?? new Map<string, TdfolFormula>();
  formulas.set(formulaKey(formula), formula);
  history.set(worldId, formulas);
}

function needsExpansion(formula: TdfolFormula): boolean {
  return (
    formula.kind === 'unary' ||
    formula.kind === 'binary' ||
    formula.kind === 'quantified' ||
    formula.kind === 'temporal' ||
    formula.kind === 'deontic'
  );
}

function formulaKey(formula: TdfolFormula): string {
  return formatTdfolFormula(formula);
}

function collectBranchConstants(branch: TdfolTableauxBranch): TdfolTerm[] {
  const constants = new Map<string, TdfolTerm>();
  for (const world of branch.worlds.values()) {
    for (const formula of [...world.positive.values(), ...world.negative.values()]) {
      collectFormulaConstants(formula, constants);
    }
  }
  return [...constants.values()];
}

function collectFormulaConstants(formula: TdfolFormula, constants: Map<string, TdfolTerm>): void {
  if (formula.kind === 'predicate') {
    for (const term of formula.args) collectTermConstants(term, constants);
  } else if (
    formula.kind === 'unary' ||
    formula.kind === 'deontic' ||
    formula.kind === 'temporal'
  ) {
    collectFormulaConstants(formula.formula, constants);
  } else if (formula.kind === 'binary') {
    collectFormulaConstants(formula.left, constants);
    collectFormulaConstants(formula.right, constants);
  } else if (formula.kind === 'quantified') {
    collectFormulaConstants(formula.formula, constants);
  }
}

function collectTermConstants(term: TdfolTerm, constants: Map<string, TdfolTerm>): void {
  if (term.kind === 'constant') {
    constants.set(formatTermKey(term), term);
  } else if (term.kind === 'function') {
    for (const arg of term.args) collectTermConstants(arg, constants);
  }
}

function makeGammaConstant(formula: TdfolQuantifiedFormula): TdfolTerm {
  return { kind: 'constant', name: `gamma_${formula.variable.name}`, sort: formula.variable.sort };
}

function makeWitness(formula: TdfolQuantifiedFormula, worldId: number): TdfolTerm {
  return {
    kind: 'constant',
    name: `skolem_w${worldId}_${formula.variable.name}`,
    sort: formula.variable.sort,
  };
}

function formatTermKey(term: TdfolTerm): string {
  if (term.kind === 'function') {
    return `${term.name}(${term.args.map(formatTermKey).join(',')})`;
  }
  return term.name;
}
