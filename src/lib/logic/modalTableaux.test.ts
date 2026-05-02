import { atom, box, checkModalTableaux, diamond, not } from './modalTableaux';

describe('checkModalTableaux', () => {
  it('finds an open branch for a satisfiable modal formula', () => {
    const result = checkModalTableaux({
      kind: 'and',
      formulas: [atom('permitFiled'), diamond(atom('inspectionScheduled'))],
    });

    expect(result).toMatchObject({
      satisfiable: true,
      status: 'satisfiable',
      metadata: {
        logic: 'modal-k',
        backend: 'typescript-tableaux',
        browserNative: true,
        serverCallsAllowed: false,
        pythonFallback: false,
      },
    });
    expect(result.worlds.map((world) => world.trueAtoms)).toEqual([
      ['permitFiled'],
      ['inspectionScheduled'],
    ]);
  });

  it('closes contradictory propositional branches', () => {
    const result = checkModalTableaux({
      kind: 'and',
      formulas: [atom('validNotice'), not(atom('validNotice'))],
    });

    expect(result).toMatchObject({
      satisfiable: false,
      status: 'unsatisfiable',
      reason: 'all branches closed',
    });
    expect(result.worlds).toEqual([]);
  });

  it('propagates box requirements to diamond successor worlds', () => {
    const result = checkModalTableaux({
      kind: 'and',
      formulas: [box(atom('appealAvailable')), diamond(atom('hearingRequested'))],
    });

    expect(result.status).toBe('satisfiable');
    expect(result.worlds[1]).toMatchObject({
      depth: 1,
      trueAtoms: ['appealAvailable', 'hearingRequested'],
    });
  });

  it('fails closed as inconclusive when a required successor exceeds the depth bound', () => {
    const result = checkModalTableaux(diamond(diamond(atom('futureReview'))), { maxDepth: 1 });

    expect(result).toMatchObject({
      satisfiable: false,
      status: 'inconclusive',
      reason: 'modal depth bound reached before satisfying diamond',
      metadata: { maxDepth: 1 },
    });
  });
});
