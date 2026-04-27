export type CecSyntaxNodeType =
  | 'Root'
  | 'Sentence'
  | 'Phrase'
  | 'DeonticExpr'
  | 'CognitiveExpr'
  | 'TemporalExpr'
  | 'Conjunction'
  | 'Disjunction'
  | 'Negation'
  | 'Implication'
  | 'Predicate'
  | 'Term'
  | 'Variable'
  | 'Constant'
  | 'Word'
  | 'Operator';

export interface CecSyntaxNodeJson {
  type: CecSyntaxNodeType;
  value?: unknown;
  semantics?: unknown;
  metadata?: Record<string, unknown>;
  children?: CecSyntaxNodeJson[];
}

export class CecAstSyntaxNode {
  readonly nodeType: CecSyntaxNodeType;
  value: unknown;
  readonly children: CecAstSyntaxNode[] = [];
  parent?: CecAstSyntaxNode;
  semantics?: unknown;
  metadata: Record<string, unknown>;

  constructor(
    nodeType: CecSyntaxNodeType,
    value?: unknown,
    options: { children?: CecAstSyntaxNode[]; semantics?: unknown; metadata?: Record<string, unknown> } = {},
  ) {
    this.nodeType = nodeType;
    this.value = value;
    this.semantics = options.semantics;
    this.metadata = options.metadata ? { ...options.metadata } : {};
    if (options.children) this.addChildren(options.children);
  }

  addChild(child: CecAstSyntaxNode): CecAstSyntaxNode {
    this.children.push(child);
    child.parent = this;
    return child;
  }

  addChildren(children: CecAstSyntaxNode[]): this {
    children.forEach((child) => this.addChild(child));
    return this;
  }

  removeChild(child: CecAstSyntaxNode): boolean {
    const index = this.children.indexOf(child);
    if (index === -1) return false;
    this.children.splice(index, 1);
    child.parent = undefined;
    return true;
  }

  isLeaf(): boolean {
    return this.children.length === 0;
  }

  isRoot(): boolean {
    return this.parent === undefined;
  }

  height(): number {
    if (this.isLeaf()) return 0;
    return 1 + Math.max(...this.children.map((child) => child.height()));
  }

  size(): number {
    return 1 + this.children.reduce((total, child) => total + child.size(), 0);
  }

  depth(): number {
    return this.parent ? 1 + this.parent.depth() : 0;
  }

  clone(): CecAstSyntaxNode {
    return new CecAstSyntaxNode(this.nodeType, this.value, {
      semantics: this.semantics,
      metadata: { ...this.metadata },
      children: this.children.map((child) => child.clone()),
    });
  }

  toString(): string {
    return this.value === undefined || this.value === null
      ? this.nodeType
      : `${this.nodeType}(${String(this.value)})`;
  }
}

export class CecAstSyntaxTree {
  readonly root: CecAstSyntaxNode;

  constructor(root: CecAstSyntaxNode = new CecAstSyntaxNode('Root')) {
    this.root = root;
  }

  preorder(node: CecAstSyntaxNode = this.root): CecAstSyntaxNode[] {
    return [node, ...node.children.flatMap((child) => this.preorder(child))];
  }

  inorder(node: CecAstSyntaxNode = this.root): CecAstSyntaxNode[] {
    const nodes: CecAstSyntaxNode[] = [];
    if (node.children.length >= 1) nodes.push(...this.inorder(node.children[0]));
    nodes.push(node);
    if (node.children.length >= 2) {
      for (const child of node.children.slice(1)) nodes.push(...this.inorder(child));
    }
    return nodes;
  }

  postorder(node: CecAstSyntaxNode = this.root): CecAstSyntaxNode[] {
    return [...node.children.flatMap((child) => this.postorder(child)), node];
  }

  levelorder(node: CecAstSyntaxNode = this.root): CecAstSyntaxNode[] {
    const nodes: CecAstSyntaxNode[] = [];
    const queue = [node];
    while (queue.length > 0) {
      const current = queue.shift();
      if (!current) continue;
      nodes.push(current);
      queue.push(...current.children);
    }
    return nodes;
  }

  find(predicate: (node: CecAstSyntaxNode) => boolean): CecAstSyntaxNode | undefined {
    return this.preorder().find(predicate);
  }

  findAll(predicate: (node: CecAstSyntaxNode) => boolean): CecAstSyntaxNode[] {
    return this.preorder().filter(predicate);
  }

  transform(transformer: (node: CecAstSyntaxNode) => CecAstSyntaxNode | undefined): CecAstSyntaxTree {
    const transformNode = (node: CecAstSyntaxNode): CecAstSyntaxNode | undefined => {
      const transformed = transformer(node.clone());
      if (!transformed) return undefined;
      transformed.children.splice(0, transformed.children.length);
      for (const child of node.children) {
        const transformedChild = transformNode(child);
        if (transformedChild) transformed.addChild(transformedChild);
      }
      return transformed;
    };
    return new CecAstSyntaxTree(transformNode(this.root) ?? new CecAstSyntaxNode('Root'));
  }

  map(mapper: (value: unknown) => unknown): CecAstSyntaxTree {
    return this.transform((node) => {
      const mapped = new CecAstSyntaxNode(node.nodeType, node.value === undefined ? undefined : mapper(node.value), {
        semantics: node.semantics,
        metadata: { ...node.metadata },
      });
      return mapped;
    });
  }

  filter(predicate: (node: CecAstSyntaxNode) => boolean): CecAstSyntaxTree {
    return this.transform((node) => predicate(node) ? new CecAstSyntaxNode(node.nodeType, node.value, {
      semantics: node.semantics,
      metadata: { ...node.metadata },
    }) : undefined);
  }

  prettyPrint(node: CecAstSyntaxNode = this.root, indent = 0, prefix = ''): string {
    const lines = [`${prefix}${node.toString()}`];
    node.children.forEach((child, index) => {
      const isLast = index === node.children.length - 1;
      const childPrefix = `${'  '.repeat(indent)}${isLast ? '`- ' : '|- '}`;
      lines.push(this.prettyPrint(child, indent + 1, childPrefix).trimEnd());
    });
    return `${lines.join('\n')}\n`;
  }

  toJson(node: CecAstSyntaxNode = this.root): CecSyntaxNodeJson {
    const json: CecSyntaxNodeJson = {
      type: node.nodeType,
      value: node.value,
    };
    if (node.semantics !== undefined) json.semantics = node.semantics;
    if (Object.keys(node.metadata).length > 0) json.metadata = { ...node.metadata };
    if (node.children.length > 0) json.children = node.children.map((child) => this.toJson(child));
    return json;
  }

  leaves(): CecAstSyntaxNode[] {
    return this.preorder().filter((node) => node.isLeaf());
  }

  height(): number {
    return this.root.height();
  }

  size(): number {
    return this.root.size();
  }

  toString(): string {
    return this.prettyPrint();
  }

  static fromJson(data: CecSyntaxNodeJson): CecAstSyntaxTree {
    return new CecAstSyntaxTree(buildSyntaxNode(data));
  }
}

function buildSyntaxNode(data: CecSyntaxNodeJson): CecAstSyntaxNode {
  const node = new CecAstSyntaxNode(data.type, data.value, {
    semantics: data.semantics,
    metadata: data.metadata,
  });
  for (const child of data.children ?? []) {
    node.addChild(buildSyntaxNode(child));
  }
  return node;
}
