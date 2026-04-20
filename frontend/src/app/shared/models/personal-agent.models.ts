export interface PersonalAgentSetting {
  setting_key: string;
  setting_value: string;
}

export interface PersonalAgent {
  id: string;
  is_active: boolean;
  created_at: string;
  agent_name: string;
  agent_type: string;
  agent_summary: string;
  language_model_id: string | null;
}

export interface PersonalAgentExpanded extends PersonalAgent {
  ag_settings: PersonalAgentSetting[];
}

export interface PersonalAgentCreateRequest {
  agent_name: string;
  agent_type: string;
  language_model_id?: string | null;
}

export interface PersonalAgentUpdateRequest {
  agent_id: string;
  agent_name: string;
  agent_summary?: string | null;
  language_model_id?: string | null;
}

export interface PersonalAgentSettingUpdateRequest {
  agent_id: string;
  setting_key: string;
  setting_value: string;
}
