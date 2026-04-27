import type { CecBinaryExpression, CecExpression, CecUnaryExpression } from './ast';
import { formatCecExpression } from './formatter';

export type CecModalLogicType = 'K' | 'T' | 'D' | 'S4' | 'S5';

export interface CecTableauxResult {
  isValid: boolean;
  closedBranches: number;
  totalBranches: number;
  openBranch?: CecTableauxBranch;
  proofSteps: string[];
}

export interface CecModalTableauxOptions {
  logicType?: CecModalLogicType;
  maxWorlds?: number;
  maxDepth?: number;
}

export class CecTableauxWorld {
  readonly id: number;
  readonly positive = new Map<string, CecExpression>();
  readonly negative = new Map<string, CecExpression>();

  constructor(id: number) {
    this.id = id;
  }

  get formulas(): CecExpression[] {
    return [...this.positive.values()];
  }

  get negatedFormulas(): CecExpression[] {
    return [...this.negative.values()];
  }

  addFormula(expression: CecExpression, negated = false): void {
    (negated ? this.negative : this.positive).set(expressionKey(expression), expression);
  }

  removeFormula(expression: CecExpression, negated = false): void {
    (negated ? this.negative : this.positive).delete(expressionKey(expression));
  }

  hasFormula(expression: CecExpression, negated = false): boolean {
    return (negated ? this.negative : this.positive).has(expressionKey(expression));
  }

  hasContradiction(): boolean {
    for (const key of this.positive.keys()) {
      if (this.negative.has(key)) return true;
    }
    return false;
  }

  copy(): CecTableauxWorld {
    const world = new CecTableauxWorld(this.id);
    for (const formula of this.positive.values()) world.addFormula(formula);
    for (const formula of this.negative.values()) world.addFormula(formula, true);
    return world;
  }
}

export class CecTableauxBranch {
  readonly worlds = new Map<number, CecTableauxWorld>();
  readonly accessibility = new Map<number, Set<number>>();
  readonly boxHistory = new Map<number, Map<string, CecExpression>>();
  readonly negDiamondHistory = new Map<number, Map<string, CecExpression>>();
  currentWorld = 0;
  isClosed = false;
  nextWorldId = 1;

  createWorld(): CecTableauxWorld {
    const world = new CecTableauxWorld(this.nextWorldId);
    this.worlds.set(world.id, world);
    this.accessibility.set(world.id, new Set());
    this.nextWorldId += 1;
    return world;
  }

  addWorld(world: CecTableauxWorld): void {
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

  rememberBox(worldId: number, formula: CecExpression): void {
    rememberExpression(this.boxHistory, worldId, formula);
  }

  getBoxHistory(worldId: number): CecExpression[] {
    return [...(this.boxHistory.get(worldId)?.values() ?? [])];
  }

  rememberNegDiamond(worldId: number, formula: CecExpression): void {
    rememberExpression(this.negDiamondHistory, worldId, formula);
  }

  getNegDiamondHistory(worldId: number): CecExpression[] {
    return [...(this.negDiamondHistory.get(worldId)?.values() ?? [])];
  }

  copy(): CecTableauxBranch {
    const branch = new CecTableauxBranch();
    for (const [id, world] of this.worlds.entries()) branch.worlds.set(id, world.copy());
    for (const [id, targets] of this.accessibility.entries()) branch.accessibility.set(id, new Set(targets));
    branch.currentWorld = this.currentWorld;
    branch.isClosed = this.isClosed;
    branch.nextWorldId = this.nextWorldId;
    copyHistory(this.boxHistory, branch.boxHistory);
    copyHistory(this.negDiamondHistory, branch.negDiamondHistory);
    return branch;
  }
}

export class CecModalTableaux {
  readonly logicType: CecModalLogicType;
  readonly maxWorlds: number;
  readonly maxDepth: number;

  constructor(options: CecModalTableauxOptions = {}) {
    this.logicType = options.logicType ?? 'K';
    this.maxWorlds = options.maxWorlds ?? 100;
    this.maxDepth = options.maxDepth ?? 50;
  }

  prove(formula: CecExpression): CecTableauxResult {
    const initialBranch = new CecTableauxBranch();
    const root = new CecTableauxWorld(0);
    root.addFormula(formula, true);
    initialBranch.addWorld(root);
    if (this.isReflexiveLogic()) initialBranch.addAccessibility(0, 0);

    let branches = [initialBranch];
    const proofSteps: string[] = [];

    for (let depth = 0; depth < this.maxDepth; depth += 1) {
      const nextBranches: CecTableauxBranch[] = [];
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
        return { isValid: true, closedBranches: closedCount, totalBranches: branches.length, proofSteps };
      }
      if (!branches.some((branch) => !branch.isClosed && this.canExpand(branch))) break;
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

  private canExpand(branch: CecTableauxBranch): boolean {
    if (branch.isClosed) return false;
    for (const world of branch.worlds.values()) {
      if ([...world.positive.values(), ...world.negative.values()].some(needsExpansion)) return true;
    }
    return false;
  }

  private expandBranch(branch: CecTableauxBranch, proofSteps: string[]): CecTableauxBranch[] | undefined {
    this.closeContradictoryWorlds(branch, proofSteps);
    if (branch.isClosed) return [branch];

    for (const [worldId, world] of branch.worlds.entries()) {
      for (const formula of [...world.positive.values()]) {
        if (needsExpansion(formula)) return this.expandFormula(branch, worldId, formula, false, proofSteps);
      }
      for (const formula of [...world.negative.values()]) {
        if (needsExpansion(formula)) return this.expandFormula(branch, worldId, formula, true, proofSteps);
      }
    }
    return undefined;
  }

  private expandFormula(
    branch: CecTableauxBranch,
    worldId: number,
    formula: CecExpression,
    negated: boolean,
    proofSteps: string[],
  ): CecTableauxBranch[] {
    const world = branch.worlds.get(worldId);
    if (!world || !world.hasFormula(formula, negated)) return [branch];
    world.removeFormula(formula, negated);

    let branches: CecTableauxBranch[];
    if (formula.kind === 'binary') branches = this.expandBinary(branch, worldId, formula, negated, proofSteps);
    else if (formula.kind === 'unary') branches = this.expandUnary(branch, worldId, formula, negated, proofSteps);
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
    branch: CecTableauxBranch,
    worldId: number,
    formula: CecBinaryExpression,
    negated: boolean,
    proofSteps: string[],
  ): CecTableauxBranch[] {
    const world = branch.worlds.get(worldId);
    if (!world) return [branch];

    if (formula.operator === 'and') {
      if (!negated) {
        world.addFormula(formula.left);
        world.addFormula(formula.right);
        proofSteps.push(`CEC AND expansion at world ${worldId}`);
        return [branch];
      }
      return this.split(branch, worldId, formula.left, true, formula.right, true, `CEC negated AND split at world ${worldId}`, proofSteps);
    }

    if (formula.operator === 'or') {
      if (!negated) {
        return this.split(branch, worldId, formula.left, false, formula.right, false, `CEC OR split at world ${worldId}`, proofSteps);
      }
      world.addFormula(formula.left, true);
      world.addFormula(formula.right, true);
      proofSteps.push(`CEC negated OR expansion at world ${worldId}`);
      return [branch];
    }

    if (formula.operator === 'implies') {
      if (!negated) {
        return this.split(branch, worldId, formula.left, true, formula.right, false, `CEC IMPLIES split at world ${worldId}`, proofSteps);
      }
      world.addFormula(formula.left);
      world.addFormula(formula.right, true);
      proofSteps.push(`CEC negated IMPLIES expansion at world ${worldId}`);
      return [branch];
    }

    if (formula.operator === 'iff') {
      if (!negated) {
        world.addFormula({ kind: 'binary', operator: 'implies', left: formula.left, right: formula.right });
        world.addFormula({ kind: 'binary', operator: 'implies', left: formula.right, right: formula.left });
        proofSteps.push(`CEC IFF expansion at world ${worldId}`);
        return [branch];
      }
      return this.split(
        branch,
        worldId,
        { kind: 'binary', operator: 'implies', left: formula.left, right: formula.right },
        true,
        { kind: 'binary', operator: 'implies', left: formula.right, right: formula.left },
        true,
        `CEC negated IFF split at world ${worldId}`,
        proofSteps,
      );
    }

    return [branch];
  }

  private expandUnary(
    branch: CecTableauxBranch,
    worldId: number,
    formula: CecUnaryExpression,
    negated: boolean,
    proofSteps: string[],
  ): CecTableauxBranch[] {
    if (formula.operator === 'not') {
      branch.worlds.get(worldId)?.addFormula(formula.expression, !negated);
      proofSteps.push(`CEC negation expansion at world ${worldId}`);
      return [branch];
    }
    if (formula.operator === 'always') return this.expandBox(branch, worldId, formula.expression, negated, proofSteps);
    if (formula.operator === 'eventually') return this.expandDiamond(branch, worldId, formula.expression, negated, proofSteps);
    if (formula.operator === 'O') return this.expandBox(branch, worldId, formula.expression, negated, proofSteps);
    if (formula.operator === 'P') return this.expandDiamond(branch, worldId, formula.expression, negated, proofSteps);
    if (formula.operator === 'F') {
      const prohibited: CecExpression = { kind: 'unary', operator: 'not', expression: formula.expression };
      return this.expandBox(branch, worldId, prohibited, negated, proofSteps);
    }
    return [branch];
  }

  private expandBox(
    branch: CecTableauxBranch,
    worldId: number,
    formula: CecExpression,
    negated: boolean,
    proofSteps: string[],
  ): CecTableauxBranch[] {
    if (!negated) {
      branch.rememberBox(worldId, formula);
      let accessible = branch.getAccessibleWorlds(worldId);
      if (accessible.size === 0 && this.isSerialLogic()) {
        const newWorld = this.createAccessibleWorld(branch, worldId);
        accessible = new Set([newWorld.id]);
      }
      for (const target of accessible) branch.worlds.get(target)?.addFormula(formula);
      if (this.isReflexiveLogic()) branch.worlds.get(worldId)?.addFormula(formula);
      proofSteps.push(`CEC BOX expansion at world ${worldId} to ${accessible.size} worlds`);
      return [branch];
    }
    const newWorld = this.createAccessibleWorld(branch, worldId);
    newWorld.addFormula(formula, true);
    this.propagateModalHistories(branch, worldId, newWorld);
    this.applyS5WorldLinks(branch, newWorld);
    proofSteps.push(`CEC negated BOX: created world ${newWorld.id}`);
    return [branch];
  }

  private expandDiamond(
    branch: CecTableauxBranch,
    worldId: number,
    formula: CecExpression,
    negated: boolean,
    proofSteps: string[],
  ): CecTableauxBranch[] {
    if (!negated) {
      const newWorld = this.createAccessibleWorld(branch, worldId);
      newWorld.addFormula(formula);
      this.propagateModalHistories(branch, worldId, newWorld);
      this.applyS5WorldLinks(branch, newWorld);
      proofSteps.push(`CEC DIAMOND: created world ${newWorld.id}`);
      return [branch];
    }
    branch.rememberNegDiamond(worldId, formula);
    for (const target of branch.getAccessibleWorlds(worldId)) branch.worlds.get(target)?.addFormula(formula, true);
    proofSteps.push(`CEC negated DIAMOND expansion at world ${worldId}`);
    return [branch];
  }

  private split(
    branch: CecTableauxBranch,
    worldId: number,
    left: CecExpression,
    leftNegated: boolean,
    right: CecExpression,
    rightNegated: boolean,
    step: string,
    proofSteps: string[],
  ): CecTableauxBranch[] {
    const leftBranch = branch.copy();
    const rightBranch = branch.copy();
    leftBranch.worlds.get(worldId)?.addFormula(left, leftNegated);
    rightBranch.worlds.get(worldId)?.addFormula(right, rightNegated);
    proofSteps.push(step);
    return [leftBranch, rightBranch];
  }

  private createAccessibleWorld(branch: CecTableauxBranch, fromWorld: number): CecTableauxWorld {
    if (branch.worlds.size >= this.maxWorlds) {
      throw new Error(`CEC modal tableaux world budget exceeded (${this.maxWorlds})`);
    }
    const world = branch.createWorld();
    branch.addAccessibility(fromWorld, world.id);
    if (this.isReflexiveLogic()) branch.addAccessibility(world.id, world.id);
    return world;
  }

  private propagateModalHistories(branch: CecTableauxBranch, sourceWorld: number, targetWorld: CecTableauxWorld): void {
    for (const body of this.getPropagatedBoxes(branch, sourceWorld)) targetWorld.addFormula(body);
    for (const body of this.getPropagatedNegDiamonds(branch, sourceWorld)) targetWorld.addFormula(body, true);
  }

  private getPropagatedBoxes(branch: CecTableauxBranch, worldId: number): CecExpression[] {
    const formulas = new Map<string, CecExpression>();
    for (const body of branch.getBoxHistory(worldId)) formulas.set(expressionKey(body), body);
    for (const formula of branch.worlds.get(worldId)?.formulas ?? []) {
      if (formula.kind === 'unary' && (formula.operator === 'always' || formula.operator === 'O')) {
        formulas.set(expressionKey(formula.expression), formula.expression);
      }
    }
    if (this.logicType === 'S4' || this.logicType === 'S5') {
      for (const ancestor of this.getAncestorWorlds(branch, worldId)) {
        for (const body of branch.getBoxHistory(ancestor)) formulas.set(expressionKey(body), body);
      }
    }
    return [...formulas.values()];
  }

  private getPropagatedNegDiamonds(branch: CecTableauxBranch, worldId: number): CecExpression[] {
    const formulas = new Map<string, CecExpression>();
    for (const body of branch.getNegDiamondHistory(worldId)) formulas.set(expressionKey(body), body);
    if (this.logicType === 'S4' || this.logicType === 'S5') {
      for (const ancestor of this.getAncestorWorlds(branch, worldId)) {
        for (const body of branch.getNegDiamondHistory(ancestor)) formulas.set(expressionKey(body), body);
      }
    }
    return [...formulas.values()];
  }

  private getAncestorWorlds(branch: CecTableauxBranch, worldId: number): number[] {
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

  private applyS5WorldLinks(branch: CecTableauxBranch, newWorld: CecTableauxWorld): void {
    if (this.logicType !== 'S5') return;
    for (const worldId of branch.worlds.keys()) {
      if (worldId === newWorld.id) continue;
      branch.addAccessibility(worldId, newWorld.id);
      branch.addAccessibility(newWorld.id, worldId);
      for (const body of branch.getBoxHistory(worldId)) newWorld.addFormula(body);
    }
  }

  private closeContradictoryWorlds(branch: CecTableauxBranch, proofSteps: string[]): void {
    if (branch.isClosed) return;
    for (const [worldId, world] of branch.worlds.entries()) {
      if (world.hasContradiction()) {
        branch.closeBranch();
        proofSteps.push(`CEC branch closed: contradiction at world ${worldId}`);
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

export function proveCecModalFormula(formula: CecExpression, logicType: CecModalLogicType = 'K'): CecTableauxResult {
  return new CecModalTableaux({ logicType }).prove(formula);
}

function rememberExpression(history: Map<number, Map<string, CecExpression>>, worldId: number, formula: CecExpression): void {
  const formulas = history.get(worldId) ?? new Map<string, CecExpression>();
  formulas.set(expressionKey(formula), formula);
  history.set(worldId, formulas);
}

function copyHistory(source: Map<number, Map<string, CecExpression>>, target: Map<number, Map<string, CecExpression>>): void {
  for (const [worldId, formulas] of source.entries()) {
    target.set(worldId, new Map(formulas));
  }
}

function needsExpansion(formula: CecExpression): boolean {
  return formula.kind === 'unary' || formula.kind === 'binary';
}

function expressionKey(formula: CecExpression): string {
  return formatCecExpression(formula);
}
