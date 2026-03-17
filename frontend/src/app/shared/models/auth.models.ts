export type SubscriptionTier = 'pro' | 'free';

export interface AuthSession {
  accessToken: string;
  refreshToken: string;
  username: string;
  email: string;
  subscriptionTier: SubscriptionTier;
  expiresAt: number;
}
