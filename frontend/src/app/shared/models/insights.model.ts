export interface AgentProfile {
  name: string;
  type: string;
  role: string;
  avatar: string;
  bio: string[];
  ctaLabel?: string;
  ctaLink?: string;
  ctaIcon?: string;
  referenceNotebook?: string;
}
