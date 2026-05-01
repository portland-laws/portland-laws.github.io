export type WorkflowFieldKind =
  | "text"
  | "textarea"
  | "number"
  | "date"
  | "checkbox"
  | "radio"
  | "select"
  | "file"
  | "display"
  | "unknown";

export type WorkflowActionKind =
  | "navigate"
  | "save_draft"
  | "continue"
  | "back"
  | "cancel"
  | "submit"
  | "upload"
  | "download"
  | "unknown";

export interface SemanticSelector {
  role: string;
  accessibleName: string;
  labelText?: string;
  nearbyHeading?: string;
  urlState?: string;
  testId?: string;
  fallbackCss?: string;
  fallbackXpath?: string;
}

export interface WorkflowValidationMessage {
  id: string;
  text: string;
  severity: "error" | "warning" | "info";
  fieldId?: string;
  selector?: SemanticSelector;
}

export interface WorkflowUploadControl {
  id: string;
  label: string;
  required: boolean;
  acceptedFileTypes: string[];
  maxFileSizeHint?: string;
  namingRuleHint?: string;
  selector?: SemanticSelector;
}

export interface WorkflowField {
  id: string;
  label: string;
  kind: WorkflowFieldKind;
  required: boolean;
  selector: SemanticSelector;
  valueState: "[REDACTED]";
  options?: string[];
  validationMessageIds?: string[];
  description?: string;
}

export interface WorkflowAction {
  id: string;
  label: string;
  kind: WorkflowActionKind;
  selector: SemanticSelector;
  enabled: boolean;
  targetStateId?: string;
  confirmationRequired?: boolean;
}

export interface WorkflowNavigationEdge {
  fromStateId: string;
  actionId: string;
  toStateId: string;
  guard: string;
}

export interface DevHubWorkflowState {
  id: string;
  workflow: string;
  urlPattern: string;
  heading: string;
  fields: WorkflowField[];
  actions: WorkflowAction[];
  validationMessages: WorkflowValidationMessage[];
  uploadControls?: WorkflowUploadControl[];
  nextStates: string[];
  capturedAt: string;
}

export interface DevHubWorkflowSnapshotFixture {
  fixtureKind: "devhub_workflow_snapshots";
  schemaVersion: 1;
  redactionPolicy: string;
  generatedAt: string;
  states: DevHubWorkflowState[];
  navigationEdges: WorkflowNavigationEdge[];
}

export function validateSemanticSelector(selector: SemanticSelector, context: string): string[] {
  const errors: string[] = [];
  if (!selector.role.trim()) errors.push(`${context} selector role is required`);
  if (!selector.accessibleName.trim()) errors.push(`${context} selector accessibleName is required`);
  if (!selector.labelText && !selector.nearbyHeading && !selector.urlState && !selector.testId) {
    errors.push(`${context} selector needs semantic context beyond role/name`);
  }
  return errors;
}

export function validateDevHubWorkflowState(state: DevHubWorkflowState): string[] {
  const errors: string[] = [];
  if (!state.id.trim()) errors.push("state id is required");
  if (!state.workflow.trim()) errors.push(`state ${state.id} workflow is required`);
  if (!state.urlPattern.startsWith("https://devhub.portlandoregon.gov/")) {
    errors.push(`state ${state.id} urlPattern must be a DevHub HTTPS URL pattern`);
  }
  if (!state.heading.trim()) errors.push(`state ${state.id} heading is required`);
  if (!state.capturedAt.endsWith("Z")) errors.push(`state ${state.id} capturedAt must end in Z`);

  const messageIds = new Set(state.validationMessages.map((message) => message.id));
  const fieldIds = new Set();
  for (const field of state.fields) {
    if (fieldIds.has(field.id)) errors.push(`state ${state.id} duplicate field id ${field.id}`);
    fieldIds.add(field.id);
    if (field.valueState !== "[REDACTED]") errors.push(`field ${field.id} valueState must be [REDACTED]`);
    errors.push(...validateSemanticSelector(field.selector, `field ${field.id}`));
    for (const messageId of field.validationMessageIds ?? []) {
      if (!messageIds.has(messageId)) errors.push(`field ${field.id} references unknown validation message ${messageId}`);
    }
  }

  for (const action of state.actions) {
    errors.push(...validateSemanticSelector(action.selector, `action ${action.id}`));
    if (["submit", "upload", "cancel"].includes(action.kind) && !action.confirmationRequired) {
      errors.push(`action ${action.id} must require confirmation in fixtures`);
    }
  }

  for (const upload of state.uploadControls ?? []) {
    if (!upload.acceptedFileTypes.length) errors.push(`upload control ${upload.id} requires acceptedFileTypes`);
    if (upload.selector) errors.push(...validateSemanticSelector(upload.selector, `upload control ${upload.id}`));
  }
  return errors;
}
