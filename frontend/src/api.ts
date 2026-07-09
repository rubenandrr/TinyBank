import type { User, Account, Transaction, AuditLog, PendingTransferRequest } from './types';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Retrieves the current administrative authentication token from localStorage
 * and builds the appropriate header.
 */
function getAdminHeaders(): Record<string, string> {
  const token = localStorage.getItem('tiny_bank_admin_token');
  return token ? { 'X-Admin-Token': token } : {};
}

/**
 * Helper to process the fetch Response, parsing JSON and throwing formatted errors on failure.
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let errorMessage = `HTTP error! Status: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData && errorData.detail) {
        errorMessage = errorData.detail;
      } else if (errorData && errorData.error) {
        errorMessage = errorData.error;
      }
    } catch {
      errorMessage = response.statusText || errorMessage;
    }
    throw new Error(errorMessage);
  }
  return response.json() as Promise<T>;
}

export const bankApi = {
  // Configuration
  async getConfig(): Promise<{ exchange_rates: Record<string, number>; bank_margin: number }> {
    const res = await fetch(`${API_BASE_URL}/config`);
    return handleResponse(res);
  },

  // Authentication
  async login(username: string, password_raw: string): Promise<{ success: boolean; message: string; user_id: string; token: string }> {
    const res = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password: password_raw }),
    });
    return handleResponse(res);
  },

  // Users
  async getUsers(): Promise<User[]> {
    const res = await fetch(`${API_BASE_URL}/users`, {
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  async getUser(userId: string): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/users/${userId}`, {
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  async createUser(name: string): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/users`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...getAdminHeaders() 
      },
      body: JSON.stringify({ name }),
    });
    return handleResponse(res);
  },

  async deactivateUser(userId: string): Promise<User> {
    const res = await fetch(`${API_BASE_URL}/users/${userId}/deactivate`, {
      method: 'POST',
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  // Accounts
  async createAccount(userId: string, accountType: 'CURRENT' | 'SAVINGS', currency: 'CHF' | 'EUR' | 'USD'): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...getAdminHeaders() 
      },
      body: JSON.stringify({
        user_id: userId,
        account_type: accountType,
        currency,
      }),
    });
    return handleResponse(res);
  },

  async freezeAccount(accountId: string): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts/${accountId}/freeze`, {
      method: 'POST',
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  async unfreezeAccount(accountId: string): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts/${accountId}/unfreeze`, {
      method: 'POST',
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  async updateAccountLimits(
    accountId: string,
    limits: { daily_withdrawal_limit?: number; daily_transfer_limit?: number; max_daily_transfers?: number }
  ): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts/${accountId}/limits`, {
      method: 'PUT',
      headers: { 
        'Content-Type': 'application/json',
        ...getAdminHeaders() 
      },
      body: JSON.stringify(limits),
    });
    return handleResponse(res);
  },

  async deleteAccount(accountId: string): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts/${accountId}`, {
      method: 'DELETE',
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  // Transactions
  async deposit(accountId: string, amount: number): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts/${accountId}/deposit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount }),
    });
    return handleResponse(res);
  },

  async withdraw(accountId: string, amount: number): Promise<Account> {
    const res = await fetch(`${API_BASE_URL}/accounts/${accountId}/withdraw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount }),
    });
    return handleResponse(res);
  },

  async transfer(sourceAccountId: string, targetAccountId: string, amount: number): Promise<{
    status?: 'PENDING';
    message: string;
    request?: PendingTransferRequest;
    source_account?: Account;
    target_account?: Account;
  }> {
    const res = await fetch(`${API_BASE_URL}/transfers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        source_account_id: sourceAccountId,
        target_account_id: targetAccountId,
        amount,
      }),
    });
    return handleResponse(res);
  },

  async getTransactionHistory(
    accountId: string,
    filters?: { type?: string; from_date?: string; limit?: number; offset?: number }
  ): Promise<Transaction[]> {
    const url = new URL(`${API_BASE_URL}/accounts/${accountId}/transactions`);
    if (filters) {
      if (filters.type && filters.type !== 'ALL') url.searchParams.append('type', filters.type);
      if (filters.from_date) url.searchParams.append('from_date', filters.from_date);
      if (filters.limit !== undefined) url.searchParams.append('limit', filters.limit.toString());
      if (filters.offset !== undefined) url.searchParams.append('offset', filters.offset.toString());
    }
    const res = await fetch(url.toString());
    return handleResponse(res);
  },

  // Admin Pending Transfer resolution
  async listPendingTransfers(): Promise<PendingTransferRequest[]> {
    const res = await fetch(`${API_BASE_URL}/admin/transfers/requests`, {
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  async resolveTransferRequest(requestId: string, approve: boolean): Promise<PendingTransferRequest> {
    const res = await fetch(`${API_BASE_URL}/admin/transfers/requests/${requestId}/resolve`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...getAdminHeaders() 
      },
      body: JSON.stringify({ approve }),
    });
    return handleResponse(res);
  },

  // Audit Logs
  async getAuditLogs(): Promise<AuditLog[]> {
    const res = await fetch(`${API_BASE_URL}/audit`, {
      headers: getAdminHeaders(),
    });
    return handleResponse(res);
  },

  // System cleanup
  async resetDatabase(): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/reset`, {
      method: 'POST',
    });
    return handleResponse(res);
  },
};