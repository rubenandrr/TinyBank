export type AccountType = 'CURRENT' | 'SAVINGS';
export type Currency = 'CHF' | 'EUR' | 'USD';
export type TransactionType = 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER_IN' | 'TRANSFER_OUT';

export interface Account {
  id: string;
  user_id: string;
  account_type: AccountType;
  balance: number;
  currency: Currency;
  is_frozen: boolean;
  daily_withdrawal_limit: number;
  daily_transfer_limit: number;
  max_daily_transfers: number;
  withdrawal_spent_today: number;
  transfer_spent_today: number;
  transfers_count_today: number;
  created_at: string;
}

export interface User {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  accounts: Account[];
}

export interface Transaction {
  id: string;
  account_id: string;
  type: TransactionType;
  amount: number;
  currency: Currency;
  related_account_id: string | null;
  description: string | null;
  timestamp: string;
}

export interface AuditLog {
  id: string;
  action: string;
  details: string;
  timestamp: string;
}

export interface PendingTransferRequest {
  id: string;
  source_account_id: string;
  target_account_id: string;
  amount: number;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  timestamp: string;
}