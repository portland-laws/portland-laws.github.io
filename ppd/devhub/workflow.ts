export type DevHubWorkflowStateKind =
  | "public_portal"
  | "sign_in_handoff"
  | "account_home"
  | "my_permits"
  | "draft_request"
  | "application_form"
  | "document_upload"
  | "corrections_upload"
  | "fee_payment"
  | "inspection_scheduling"
  | "review_status"
  | "unknown";

export type DevHubFieldKind = "text" | "number" | "date" | "checkbox" | "radio" | "select" | "file" | "acknowledgment" | "hidden" | "unknown";

export type DevHubActionKind =
  | "navigate"
  | "read_status"
  | "download_own_document"
  | "save_draft"
  | "fill_field"
  | "attach_draft_file"
  | "official_upload"
  | "certify_acknowledgment"
  | "submit_application"
  | "pay_fee"
  | "enter_payment_details"
  | "schedule_inspection"
  | "cancel_request"
  | "other";

export type DevHubSelectorKind = "role_name" | "label_text" | "heading_context" | "test_id" | "css" | "xpath";

export interface DevHubSelector {
  kind: DevHubSelectorKind;
  value: string;
  description?: string;
}

export interface DevHubField {
  id: string;
  label: string;
  kind: DevHubFieldKind;
  required: boolean;
  selector?: DevHubSelector;
  helpText?: string;
  options?: string[];
  validationMessages?: string[];
  redactedValuePresent?: boolean;
}

export interface DevHubWorkflowAction {
  id: string;
  label: string;
  kind: DevHubActionKind;
  selector?: DevHubSelector;
  enabled?: boolean;
  confirmationText?: string;
  consequenceSummary?: string;
  nextStateIds?: string[];
}

export interface DevHubWorkflowState {
  id: string;
  workflow: string;
  kind: DevHubWorkflowStateKind;
  urlPattern: string;
  heading: string;
  capturedAt: string;
  fields: DevHubField[];
  actions: DevHubWorkflowAction[];
  validationMessages?: string[];
  nextStateIds?: string[];
  privateValuesRedacted: boolean;
  notes?: string[];
}

export type ActionGateClassification = "safe_read_only" | "reversible_draft_edit" | "potentially_consequential" | "financial";

export function classifyDevHubAction(action: DevHubWorkflowAction): ActionGateClassification {
  if (action.kind === "pay_fee" || action.kind === "enter_payment_details") return "financial";
  if (
    action.kind === "official_upload" ||
    action.kind === "certify_acknowledgment" ||
    action.kind === "submit_application" ||
    action.kind === "schedule_inspection" ||
    action.kind === "cancel_request"
  ) {
    return "potentially_consequential";
  }
  if (action.kind === "save_draft" || action.kind === "fill_field" || action.kind === "attach_draft_file") return "reversible_draft_edit";
  return "safe_read_only";
}

export function validateDevHubWorkflowState(state: DevHubWorkflowState): string[] {
  const errors: string[] = [];
  if (!state.id.trim()) errors.push("state id is required");
  if (!state.workflow.trim()) errors.push("workflow is required");
  if (!state.heading.trim()) errors.push(`state ${state.id} heading is required`);
  if (!state.capturedAt.trim()) errors.push(`state ${state.id} capturedAt is required`);
  if (state.privateValuesRedacted !== true) errors.push(`state ${state.id} must redact private values`);

  const fieldIds = new Set<string>();
  for (const field of state.fields ?? []) {
    if (!field.id.trim()) errors.push("field id is required");
    if (!field.label.trim()) errors.push(`field ${field.id} label is required`);
    if ((field.kind === "select" || field.kind === "radio") && (!field.options || field.options.length === 0)) {
      errors.push(`field ${field.id} must include options`);
    }
    fieldIds.add(field.id);
  }
  if (fieldIds.size !== (state.fields ?? []).length) errors.push(`state ${state.id} has duplicate field ids`);

  const actionIds = new Set<string>();
  for (const action of state.actions ?? []) {
    if (!action.id.trim()) errors.push("action id is required");
    if (!action.label.trim()) errors.push(`action ${action.id} label is required`);
    const classification = classifyDevHubAction(action);
    if ((classification === "potentially_consequential" || classification === "financial") && !action.confirmationText?.trim()) {
      errors.push(`action ${action.id} requires confirmation text`);
    }
    actionIds.add(action.id);
  }
  if (actionIds.size !== (state.actions ?? []).length) errors.push(`state ${state.id} has duplicate action ids`);

  return errors;
}
