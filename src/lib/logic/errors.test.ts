import { LogicError, LogicParseError, LogicValidationError } from './errors';

describe('logic errors', () => {
  it('formats errors with optional context', () => {
    const error = new LogicError('Bad formula', { formula: 'P ->', offset: 4 });

    expect(error.message).toBe('Bad formula');
    expect(error.context).toEqual({ formula: 'P ->', offset: 4 });
    expect(error.toString()).toBe('Bad formula (Context: formula=P ->, offset=4)');
  });

  it('preserves subclass names', () => {
    expect(new LogicParseError('Parse failed').name).toBe('LogicParseError');
    expect(new LogicValidationError('Invalid row')).toBeInstanceOf(LogicError);
  });
});

