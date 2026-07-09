import { useState, useEffect } from 'react';
import type { User, Account, Transaction, AuditLog, PendingTransferRequest } from './types';
import { bankApi } from './api';
import { 
  Landmark, 
  LayoutDashboard, 
  ArrowRightLeft, 
  History, 
  Users, 
  ShieldAlert, 
  Clock, 
  LogOut, 
  LogIn, 
  Lock, 
  Unlock, 
  Plus, 
  Check,
  X, 
  Search,
  RefreshCw,
  AlertCircle,
  Settings,
  Coins
} from 'lucide-react';

function AccountHistoryRow({ accountId }: { accountId: string }) {
  const [txList, setTxList] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    let active = true;
    const loadTxs = async () => {
      try {
        const history = await bankApi.getTransactionHistory(accountId, { limit: 10 });
        if (active) {
          setTxList(history);
          setLoading(false);
        }
      } catch (e) {
        console.error("Failed to load history for " + accountId);
      }
    };
    loadTxs();
    return () => { active = false; };
  }, [accountId]);

  if (loading) return <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Loading transactions...</p>;
  
  if (txList.length === 0) return <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No transactions recorded yet.</p>;

  return (
    <div className="table-container">
      <table className="custom-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Amount</th>
            <th>Related Account</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          {txList.map(tx => (
            <tr key={tx.id} style={tx.type === 'TRANSFER_REJECTED' ? { textDecoration: 'line-through', opacity: 0.6 } : undefined}>
              <td>{new Date(tx.timestamp).toLocaleString()}</td>
              <td>
                <span className={`badge ${tx.type === 'DEPOSIT' || tx.type === 'TRANSFER_IN' ? 'badge-emerald' : 'badge-rose'}`} style={tx.type === 'TRANSFER_REJECTED' ? { background: 'rgba(244, 63, 94, 0.2)', borderColor: 'var(--accent-rose)', color: 'var(--text-muted)' } : undefined}>
                  {tx.type === 'TRANSFER_REJECTED' ? 'REJECTED' : tx.type}
                </span>
              </td>
              <td>{tx.amount.toFixed(2)} {tx.currency}</td>
              <td>{tx.related_account_id ? tx.related_account_id.substring(0, 13) + '...' : '-'}</td>
              <td>{tx.description || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AdminHistoryExplorer({ users }: { users: User[] }) {
  const [selectedUserId, setSelectedUserId] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('ALL');
  const [selectedCurrency, setSelectedCurrency] = useState<string>('ALL');
  const [transactions, setTransactions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    if (!selectedUserId) {
      setTransactions([]);
      return;
    }
    
    let active = true;
    const fetchMergedTxs = async () => {
      setLoading(true);
      try {
        const user = users.find(u => u.id === selectedUserId);
        if (!user) {
          if (active) {
            setTransactions([]);
            setLoading(false);
          }
          return;
        }

        // Filter accounts of this user based on selected type and currency
        const filteredAccounts = user.accounts.filter(acc => {
          const matchType = selectedType === 'ALL' || acc.account_type === selectedType;
          const matchCurrency = selectedCurrency === 'ALL' || acc.currency === selectedCurrency;
          return matchType && matchCurrency;
        });

        // Fetch transactions for all matching accounts in parallel
        const txPromises = filteredAccounts.map(acc => 
          bankApi.getTransactionHistory(acc.id, { limit: 50 }).then(txs => 
            txs.map(tx => ({
              ...tx,
              accountName: `${acc.account_type} (${acc.currency})`,
              clientName: user.name
            }))
          )
        );

        const results = await Promise.all(txPromises);
        const merged = results.flat().sort((a, b) => 
          new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
        );
        
        if (active) {
          setTransactions(merged);
        }
      } catch (err) {
        console.error("Failed to load admin transactions history", err);
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    fetchMergedTxs();
    return () => { active = false; };
  }, [selectedUserId, selectedType, selectedCurrency, users]);

  return (
    <div className="glass-panel">
      <h3 style={{ marginBottom: '1.5rem' }}>Admin Transaction Registry Explorer</h3>
      
      {/* Filters Row */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2.5rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: '200px' }}>
          <label className="form-label">Search Client</label>
          <select 
            className="form-select"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value)}
            style={{ background: '#0b0f19' }}
          >
            <option value="">-- Choose client --</option>
            {users.filter(u => u.id !== 'admin-user' && u.id !== 'bank-tax-user').map(u => (
              <option key={u.id} value={u.id}>
                👤 {u.name} (Accounts: {u.accounts.length})
              </option>
            ))}
          </select>
        </div>

        <div style={{ width: '150px' }}>
          <label className="form-label">Account Type</label>
          <select 
            className="form-select"
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            style={{ background: '#0b0f19' }}
          >
            <option value="ALL">All Types</option>
            <option value="CURRENT">Current</option>
            <option value="SAVINGS">Savings</option>
          </select>
        </div>

        <div style={{ width: '120px' }}>
          <label className="form-label">Currency</label>
          <select 
            className="form-select"
            value={selectedCurrency}
            onChange={(e) => setSelectedCurrency(e.target.value)}
            style={{ background: '#0b0f19' }}
          >
            <option value="ALL">All</option>
            <option value="CHF">CHF</option>
            <option value="EUR">EUR</option>
            <option value="USD">USD</option>
          </select>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <p style={{ color: 'var(--text-muted)' }}>Loading registry records...</p>
      ) : !selectedUserId ? (
        <p style={{ color: 'var(--text-muted)' }}>Please select a client to search history.</p>
      ) : transactions.length === 0 ? (
        <p style={{ color: 'var(--text-muted)' }}>No transactions found matching filters.</p>
      ) : (
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Client</th>
                <th>Account</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Target ID</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map(tx => (
                <tr key={tx.id} style={tx.type === 'TRANSFER_REJECTED' ? { textDecoration: 'line-through', opacity: 0.6 } : undefined}>
                  <td>{new Date(tx.timestamp).toLocaleString()}</td>
                  <td><strong>{tx.clientName}</strong></td>
                  <td>{tx.accountName}</td>
                  <td>
                    <span className={`badge ${tx.type === 'DEPOSIT' || tx.type === 'TRANSFER_IN' ? 'badge-emerald' : 'badge-rose'}`} style={tx.type === 'TRANSFER_REJECTED' ? { background: 'rgba(244, 63, 94, 0.2)', borderColor: 'var(--accent-rose)', color: 'var(--text-muted)' } : undefined}>
                      {tx.type === 'TRANSFER_REJECTED' ? 'REJECTED' : tx.type}
                    </span>
                  </td>
                  <td>{tx.amount.toFixed(2)} {tx.currency}</td>
                  <td>{tx.related_account_id ? tx.related_account_id.substring(0, 13) + '...' : '-'}</td>
                  <td>{tx.description || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function App() {
  // --- STATE MANAGEMENT ---
  const [users, setUsers] = useState<User[]>([]);
  const [activeUserId, setActiveUserId] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'dashboard' | 'transfer' | 'history' | 'accounts' | 'audit' | 'pending'>('dashboard');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Administrative credentials & auth states
  const [adminToken, setAdminToken] = useState<string | null>(localStorage.getItem('tiny_bank_admin_token'));
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);
  const [adminPassword, setAdminPassword] = useState<string>('');
  const [loginError, setLoginError] = useState<string | null>(null);
  
  // Form values
  const [depositAmounts, setDepositAmounts] = useState<Record<string, string>>({});
  const [withdrawAmounts, setWithdrawAmounts] = useState<Record<string, string>>({});
  const [transferAmount, setTransferAmount] = useState<string>('');
  const [transferSourceId, setTransferSourceId] = useState<string>('');
  const [transferTargetId, setTransferTargetId] = useState<string>('');
  const [newUserName, setNewUserName] = useState<string>('');
  
  // Admin update limit forms
  const [editingLimitAccountId, setEditingLimitAccountId] = useState<string>('');
  const [newWithdrawalLimit, setNewWithdrawalLimit] = useState<string>('');
  const [newTransferLimit, setNewTransferLimit] = useState<string>('');
  const [newMaxTransfers, setNewMaxTransfers] = useState<string>('');

  // Exchange rates configuration cache
  const [rates, setRates] = useState<Record<string, number>>({});
  const [margin, setMargin] = useState<number>(0.005);
  
  // Dynamic lists for admin panels
  const [pendingRequests, setPendingRequests] = useState<PendingTransferRequest[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [auditSearch, setAuditSearch] = useState<string>('');

  // Quick transaction messages
  const [txSuccessMessage, setTxSuccessMessage] = useState<string | null>(null);
  const [txErrorMessage, setTxErrorMessage] = useState<string | null>(null);

  // Last 3 transactions for dashboard
  const [lastTxs, setLastTxs] = useState<any[]>([]);
  const [loadingLastTxs, setLoadingLastTxs] = useState<boolean>(false);

  const isAdmin = !!adminToken;

  // --- CORE DATA LOADING ---
  const loadBankData = async (selectNewId?: string) => {
    try {
      // 1. Fetch configuration
      const config = await bankApi.getConfig();
      setRates(config.exchange_rates);
      setMargin(config.bank_margin);

      // 2. Fetch users
      const fetchedUsers = await bankApi.getUsers();
      setUsers(fetchedUsers);

      if (fetchedUsers.length > 0) {
        if (selectNewId) {
          setActiveUserId(selectNewId);
        } else if (!activeUserId || !fetchedUsers.some(u => u.id === activeUserId)) {
          // If no active user or active user was deleted, default to first standard user
          const standardUser = fetchedUsers.find(u => u.id !== 'bank-tax-user' && u.id !== 'admin-user');
          setActiveUserId(standardUser ? standardUser.id : fetchedUsers[0].id);
        }
      } else {
        setActiveUserId('');
      }

      // 3. If admin, fetch logs and pending requests
      if (isAdmin) {
        const [pending, logs] = await Promise.all([
          bankApi.listPendingTransfers(),
          bankApi.getAuditLogs()
        ]);
        setPendingRequests(pending);
        setAuditLogs(logs);
      }

      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to connect to the backend server.');
    } finally {
      setLoading(false);
    }
  };

  const fetchLastTransactions = async (userId: string) => {
    const user = users.find(u => u.id === userId);
    if (!user || user.accounts.length === 0) {
      setLastTxs([]);
      return;
    }
    setLoadingLastTxs(true);
    try {
      const isTaxUser = userId === 'bank-tax-user';
      const limitVal = isTaxUser ? 1000 : 3;

      const promises = user.accounts.map(acc => 
        bankApi.getTransactionHistory(acc.id, { limit: limitVal }).then(txs => 
          txs.map(tx => ({ ...tx, accountName: `${acc.account_type} (${acc.currency})` }))
        )
      );
      const results = await Promise.all(promises);
      const merged = results.flat().sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      const finalData = isTaxUser ? merged : merged.slice(0, 3);
      setLastTxs(finalData);
    } catch (e) {
      console.error("Failed to load last transactions for dashboard", e);
    } finally {
      setLoadingLastTxs(false);
    }
  };

  useEffect(() => {
    loadBankData();
  }, [adminToken]);

  // Refresh lists periodically when admin is active
  useEffect(() => {
    if (!isAdmin) return;
    const interval = setInterval(async () => {
      try {
        const pending = await bankApi.listPendingTransfers();
        setPendingRequests(pending);
      } catch (err) {
        console.error("Auto-fetch pending requests failed", err);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isAdmin]);

  // Reset transfer source/target and messages when active client changes
  useEffect(() => {
    const user = users.find(u => u.id === activeUserId);
    if (user && user.accounts.length > 0) {
      const firstActive = user.accounts.find(a => !a.is_frozen);
      setTransferSourceId(firstActive ? firstActive.id : user.accounts[0].id);
    } else {
      setTransferSourceId('');
    }
    setTransferTargetId('');
    setTxSuccessMessage(null);
    setTxErrorMessage(null);

    // Redirect to dashboard if bank-tax-user is active and currently in transfer tab
    if (activeUserId === 'bank-tax-user' && activeTab === 'transfer') {
      setActiveTab('dashboard');
    }
  }, [activeUserId, activeTab]);

  // Load dashboard last transactions when active client or bank data changes
  useEffect(() => {
    if (activeUserId && users.length > 0) {
      fetchLastTransactions(activeUserId);
    } else {
      setLastTxs([]);
    }
  }, [activeUserId, users]);

  // Reset tab if active user is changed and current tab is admin-only
  useEffect(() => {
    if (!isAdmin && (activeTab === 'audit' || activeTab === 'pending' || activeTab === 'accounts')) {
      setActiveTab('dashboard');
    }
  }, [activeUserId, activeTab, isAdmin]);

  // Auto-hide transaction success/error banners after 5 seconds
  useEffect(() => {
    if (txSuccessMessage) {
      const timer = setTimeout(() => setTxSuccessMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [txSuccessMessage]);

  useEffect(() => {
    if (txErrorMessage) {
      const timer = setTimeout(() => setTxErrorMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [txErrorMessage]);

  // --- AUTH ACTIONS ---
  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError(null);
    try {
      const response = await bankApi.login('admin', adminPassword);
      if (response.success && response.token) {
        localStorage.setItem('tiny_bank_admin_token', response.token);
        setAdminToken(response.token);
        setShowLoginModal(false);
        setAdminPassword('');
        setActiveTab('accounts');
      } else {
        setLoginError(response.message || 'Invalid credentials.');
      }
    } catch (err: any) {
      setLoginError(err.message || 'Login failed.');
    }
  };

  const handleAdminLogout = () => {
    localStorage.removeItem('tiny_bank_admin_token');
    setAdminToken(null);
    setPendingRequests([]);
    setAuditLogs([]);
    setActiveTab('dashboard');
  };

  const handleResetDatabase = async () => {
    if (window.confirm("Are you sure you want to reset the bank database? This will clear all accounts and clients.")) {
      try {
        setLoading(true);
        await bankApi.resetDatabase();
        handleAdminLogout();
        await loadBankData();
        alert("Tiny Bank database reset completed successfully!");
      } catch (err: any) {
        alert("Failed to reset database: " + err.message);
      } finally {
        setLoading(false);
      }
    }
  };

  // --- TRANSACTION ACTIONS ---
  const handleDeposit = async (accountId: string) => {
    setTxErrorMessage(null);
    setTxSuccessMessage(null);
    const amountStr = depositAmounts[accountId] || '';
    const amount = parseFloat(amountStr);
    if (isNaN(amount) || amount <= 0) return;

    try {
      await bankApi.deposit(accountId, amount);
      setTxSuccessMessage(`Successfully deposited ${amount.toFixed(2)}.`);
      setDepositAmounts(prev => ({ ...prev, [accountId]: '' }));
      loadBankData(activeUserId);
    } catch (err: any) {
      setTxErrorMessage(err.message || 'Deposit failed.');
    }
  };

  const handleWithdrawal = async (accountId: string) => {
    setTxErrorMessage(null);
    setTxSuccessMessage(null);
    const amountStr = withdrawAmounts[accountId] || '';
    const amount = parseFloat(amountStr);
    if (isNaN(amount) || amount <= 0) return;

    try {
      await bankApi.withdraw(accountId, amount);
      setTxSuccessMessage(`Successfully withdrew ${amount.toFixed(2)}.`);
      setWithdrawAmounts(prev => ({ ...prev, [accountId]: '' }));
      loadBankData(activeUserId);
    } catch (err: any) {
      setTxErrorMessage(err.message || 'Withdrawal failed.');
    }
  };

  const handleTransfer = async (e: React.FormEvent) => {
    e.preventDefault();
    setTxErrorMessage(null);
    setTxSuccessMessage(null);
    const amount = parseFloat(transferAmount);

    if (!transferSourceId || !transferTargetId || isNaN(amount) || amount <= 0) {
      setTxErrorMessage('Please verify all transfer fields.');
      return;
    }

    try {
      const response = await bankApi.transfer(transferSourceId, transferTargetId, amount);
      if (response.status === 'PENDING') {
        setTxSuccessMessage(`⚠️ Limit exceeded: ${response.message}`);
      } else {
        setTxSuccessMessage('Transfer executed successfully!');
      }
      setTransferAmount('');
      loadBankData(activeUserId);
    } catch (err: any) {
      setTxErrorMessage(err.message || 'Transfer failed.');
    }
  };

  // --- ADMIN RESOLUTIONS ---
  const handleResolvePending = async (requestId: string, approve: boolean) => {
    try {
      await bankApi.resolveTransferRequest(requestId, approve);
      alert(approve ? "Virement approuvé et exécuté !" : "Virement rejeté.");
      loadBankData(activeUserId);
    } catch (err: any) {
      alert("Resolution failed: " + err.message);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUserName.trim()) return;
    try {
      const user = await bankApi.createUser(newUserName);
      alert(`Client ${user.name} created successfully!`);
      setNewUserName('');
      loadBankData(user.id);
    } catch (err: any) {
      alert("Failed to create client: " + err.message);
    }
  };

  const handleDeactivateUser = async (userId: string) => {
    if (window.confirm("Deactivating this user will freeze all of their bank accounts. Proceed?")) {
      try {
        await bankApi.deactivateUser(userId);
        alert("Client deactivated successfully.");
        loadBankData(activeUserId);
      } catch (err: any) {
        alert("Deactivation failed: " + err.message);
      }
    }
  };

  const handleOpenAccount = async (userId: string, type: 'CURRENT' | 'SAVINGS', currency: 'CHF' | 'EUR' | 'USD') => {
    try {
      await bankApi.createAccount(userId, type, currency);
      alert(`New ${type} account in ${currency} opened successfully!`);
      loadBankData(activeUserId);
    } catch (err: any) {
      alert("Opening account failed: " + err.message);
    }
  };

  const handleToggleFreeze = async (account: Account) => {
    try {
      if (account.is_frozen) {
        await bankApi.unfreezeAccount(account.id);
        alert("Account unfrozen.");
      } else {
        await bankApi.freezeAccount(account.id);
        alert("Account frozen.");
      }
      loadBankData(activeUserId);
    } catch (err: any) {
      alert("Freeze operation failed: " + err.message);
    }
  };

  const handleUpdateLimits = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingLimitAccountId) return;
    try {
      await bankApi.updateAccountLimits(editingLimitAccountId, {
        daily_withdrawal_limit: newWithdrawalLimit ? parseFloat(newWithdrawalLimit) : undefined,
        daily_transfer_limit: newTransferLimit ? parseFloat(newTransferLimit) : undefined,
        max_daily_transfers: newMaxTransfers ? parseInt(newMaxTransfers) : undefined,
      });
      alert("Limits updated successfully.");
      setEditingLimitAccountId('');
      loadBankData(activeUserId);
    } catch (err: any) {
      alert("Limit update failed: " + err.message);
    }
  };

  const handleDeleteAccount = async (accountId: string) => {
    if (window.confirm("Deleting this account will permanently close it and transfer its remaining balance (converting if necessary) to the primary account. Proceed?")) {
      try {
        await bankApi.deleteAccount(accountId);
        alert("Account deleted and balance transferred successfully.");
        loadBankData(activeUserId);
      } catch (err: any) {
        alert("Account deletion failed: " + err.message);
      }
    }
  };

  // --- DERIVED STATES ---
  const activeUser = users.find(u => u.id === activeUserId) || null;
  const standardUsers = users.filter(u => u.id !== 'bank-tax-user' && u.id !== 'admin-user');
  
  // Tax collection status
  const taxUser = users.find(u => u.id === 'bank-tax-user');
  const taxAccount = taxUser?.accounts[0] || null;

  // Filtered audit logs
  const filteredLogs = auditLogs.filter(log => 
    log.action.toLowerCase().includes(auditSearch.toLowerCase()) ||
    log.details.toLowerCase().includes(auditSearch.toLowerCase())
  );

  return (
    <div className="app-container">
      {/* --- SIDEBAR NAVIGATION --- */}
      <aside className="sidebar">
        <div>
          <div className="brand-container">
            <span className="brand-logo">
              <Landmark size={24} />
              Tiny Bank
            </span>
          </div>

          <nav className="nav-menu">
            <button 
              className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              <LayoutDashboard size={18} />
              Dashboard
            </button>
            {activeUserId !== 'bank-tax-user' && (
              <button 
                className={`nav-item ${activeTab === 'transfer' ? 'active' : ''}`}
                onClick={() => setActiveTab('transfer')}
              >
                <ArrowRightLeft size={18} />
                Transfers
              </button>
            )}
            <button 
              className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <History size={18} />
              History
            </button>

            {/* Admin only navigations */}
            {isAdmin && (
              <>
                <button 
                  className={`nav-item ${activeTab === 'accounts' ? 'active' : ''}`}
                  onClick={() => setActiveTab('accounts')}
                >
                  <Users size={18} />
                  Manage Clients
                </button>
                <button 
                  className={`nav-item ${activeTab === 'pending' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('pending'); loadBankData(); }}
                >
                  <Clock size={18} />
                  Pending ({pendingRequests.length})
                </button>
                <button 
                  className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
                  onClick={() => { setActiveTab('audit'); loadBankData(); }}
                >
                  <ShieldAlert size={18} />
                  Audit Logs
                </button>
              </>
            )}
          </nav>
        </div>

        {/* Sidebar Footer: Active Client Selector & Reset */}
        <div className="user-selector-container">
          <label className="form-label" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Active Client View
          </label>
          {standardUsers.length === 0 ? (
            <div style={{ color: 'var(--accent-orange)', fontSize: '0.85rem', margin: '0.5rem 0' }}>
              No clients registered
            </div>
          ) : (
            <select 
              className="user-select"
              value={activeUserId}
              onChange={(e) => setActiveUserId(e.target.value)}
            >
              {standardUsers.map(u => (
                <option key={u.id} value={u.id}>
                  👤 {u.name} {!u.is_active ? '[Deactivated]' : ''}
                </option>
              ))}
              {/* Show system tax collector account if admin is authenticated */}
              {isAdmin && taxUser && (
                <option value={taxUser.id}>
                  💰 {taxUser.name} (Tax Collection)
                </option>
              )}
            </select>
          )}

          {/* Admin Connection controls */}
          <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem', flexDirection: 'column' }}>
            {isAdmin ? (
              <button onClick={handleAdminLogout} className="btn btn-rose" style={{ width: '100%', padding: '0.6rem' }}>
                <LogOut size={16} /> Logout Admin
              </button>
            ) : (
              <button onClick={() => { setLoginError(null); setShowLoginModal(true); }} className="btn btn-emerald" style={{ width: '100%', padding: '0.6rem' }}>
                <LogIn size={16} /> Admin Panel
              </button>
            )}
            
            <button onClick={handleResetDatabase} className="btn" style={{ background: '#1e293b', color: '#fda4af', width: '100%', padding: '0.6rem', fontSize: '0.85rem' }}>
              Reset Tiny Bank
            </button>
          </div>
        </div>
      </aside>

      {/* --- MAIN PAGE CONTENT --- */}
      <main className="main-content">
        <header className="page-header">
          <div>
            <h1 className="page-title">
              {activeTab === 'dashboard' && 'Dashboard'}
              {activeTab === 'transfer' && 'International Transfers'}
              {activeTab === 'history' && 'Transactions Registry'}
              {activeTab === 'accounts' && 'Client Management'}
              {activeTab === 'pending' && 'Pending Transfer Authorizations'}
              {activeTab === 'audit' && 'System Audit Trail'}
            </h1>
            <p className="page-subtitle">
              {activeTab === 'dashboard' && 'Monitor balances and execute instant deposits/withdrawals.'}
              {activeTab === 'transfer' && 'Secure transfer system with automatic multi-currency conversion.'}
              {activeTab === 'history' && 'Track, filter, and audit all transactions for the selected account.'}
              {activeTab === 'accounts' && 'Create users, open additional accounts, freeze records, and manage daily limits.'}
              {activeTab === 'pending' && 'Review and authorize or reject transactions exceeding standard user limits.'}
              {activeTab === 'audit' && 'Security event logs for administrative compliance audits.'}
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {isAdmin && (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                Bank Tax Vault: <strong style={{ color: 'var(--accent-cyan)' }}>{taxAccount ? taxAccount.balance.toFixed(2) : '0.00'} CHF</strong>
              </span>
            )}
            <button onClick={() => loadBankData(activeUserId)} className="btn btn-emerald" style={{ padding: '0.5rem 0.75rem' }}>
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </header>

        {/* Global Loading / Error Views */}
        {loading ? (
          <div style={{ display: 'flex', height: '50vh', alignItems: 'center', justifyContent: 'center' }}>
            <h3>Connecting to Tiny Bank...</h3>
          </div>
        ) : error ? (
          <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', maxWidth: '600px', margin: '2rem auto' }}>
            <AlertCircle size={48} style={{ color: 'var(--accent-rose)', marginBottom: '1rem' }} />
            <h3>Backend Offline</h3>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '2rem' }}>
              {error}. Ensure your Uvicorn FastAPI backend is running on port 8000.
            </p>
            <button onClick={() => loadBankData(activeUserId)} className="btn btn-primary">Try Again</button>
          </div>
        ) : (
          <div>
            {/* Feedback messages */}
            {txSuccessMessage && (
              <div className="glass-panel animate-pulse-subtle" style={{ background: 'rgba(16, 185, 129, 0.12)', borderColor: 'var(--accent-emerald)', color: '#a7f3d0', padding: '1rem', marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <Check size={18} /> <span>{txSuccessMessage}</span>
                </div>
                <button onClick={() => setTxSuccessMessage(null)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '0.2rem' }}>
                  <X size={16} />
                </button>
              </div>
            )}
            {txErrorMessage && (
              <div className="glass-panel" style={{ background: 'rgba(244, 63, 94, 0.12)', borderColor: 'var(--accent-rose)', color: '#fca5a5', padding: '1rem', marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                  <X size={18} /> <span>{txErrorMessage}</span>
                </div>
                <button onClick={() => setTxErrorMessage(null)} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '0.2rem' }}>
                  <X size={16} />
                </button>
              </div>
            )}

            {/* --- TAB 1: CLIENT DASHBOARD --- */}
            {activeTab === 'dashboard' && (
              <div>
                {!activeUser ? (
                  <div className="glass-panel" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)' }}>No active client selected. Select a client from the sidebar.</p>
                  </div>
                ) : (
                  <div>
                    <h2 style={{ marginBottom: '1.5rem', fontSize: '1.25rem', color: 'var(--text-secondary)' }}>
                      Welcome back, <strong>{activeUser.name}</strong> {!activeUser.is_active && <span className="badge badge-rose">Deactivated</span>}
                    </h2>
                    
                    <div className="account-grid">
                      {activeUser.accounts.map(acc => (
                        <div key={acc.id} className={`account-card ${acc.is_frozen ? 'frozen' : ''}`}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <span className="badge badge-cyan">{acc.account_type}</span>
                            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: {acc.id.substring(0, 8)}...</span>
                          </div>
                          
                          <div style={{ fontSize: '1.85rem', fontWeight: 700, margin: '1rem 0' }}>
                            {acc.balance.toFixed(2)} <span style={{ color: 'var(--accent-cyan)' }}>{acc.currency}</span>
                          </div>

                          {/* Quick Actions (only if account is not frozen and user is active) */}
                          {!acc.is_frozen && activeUser.is_active && activeUser.id !== 'bank-tax-user' && (
                            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                              <div style={{ flex: 1, display: 'flex', gap: '0.25rem' }}>
                                <input 
                                  type="number" 
                                  placeholder="Deposit" 
                                  className="form-input" 
                                  style={{ padding: '0.4rem', fontSize: '0.85rem' }}
                                  value={depositAmounts[acc.id] || ''} 
                                  onChange={(e) => setDepositAmounts({ ...depositAmounts, [acc.id]: e.target.value })}
                                />
                                <button onClick={() => handleDeposit(acc.id)} className="btn btn-emerald" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                                  Go
                                </button>
                              </div>
                              
                              <div style={{ flex: 1, display: 'flex', gap: '0.25rem' }}>
                                <input 
                                  type="number" 
                                  placeholder="Withdraw" 
                                  className="form-input" 
                                  style={{ padding: '0.4rem', fontSize: '0.85rem' }}
                                  value={withdrawAmounts[acc.id] || ''} 
                                  onChange={(e) => setWithdrawAmounts({ ...withdrawAmounts, [acc.id]: e.target.value })}
                                />
                                <button onClick={() => handleWithdrawal(acc.id)} className="btn btn-rose" style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}>
                                  Go
                                </button>
                              </div>
                            </div>
                          )}

                          {/* Show limits stats */}
                          <div style={{ marginTop: '1.25rem', paddingTop: '1rem', borderTop: '1px dashed var(--border-color)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                              <span>Withdraw spent today:</span>
                              <span>{acc.withdrawal_spent_today.toFixed(2)} / {acc.daily_withdrawal_limit.toFixed(0)} {acc.currency}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                              <span>Transfer spent today:</span>
                              <span>{acc.transfer_spent_today.toFixed(2)} / {acc.daily_transfer_limit.toFixed(0)} {acc.currency}</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Last Transactions / Tax Ledger Panel */}
                    <div className="glass-panel" style={{ marginTop: '2.5rem' }}>
                      <h3 style={{ marginBottom: '1.25rem', fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {activeUserId === 'bank-tax-user' ? (
                          <>
                            <Coins size={18} style={{ color: 'var(--accent-cyan)' }} /> Tax Collections Audit Ledger
                          </>
                        ) : (
                          <>
                            <History size={18} style={{ color: 'var(--accent-cyan)' }} /> Last 3 Transactions
                          </>
                        )}
                      </h3>
                      {loadingLastTxs ? (
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading activities...</p>
                      ) : lastTxs.length === 0 ? (
                        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No transaction history found.</p>
                      ) : (
                        <div className="table-container">
                          <table className="custom-table" style={{ fontSize: '0.9rem' }}>
                            <thead>
                              {activeUserId === 'bank-tax-user' ? (
                                <tr>
                                  <th>Date</th>
                                  <th>Tax Account</th>
                                  <th>Origin Account (Client)</th>
                                  <th>Amount Collected</th>
                                  <th>Description</th>
                                </tr>
                              ) : (
                                <tr>
                                  <th>Date</th>
                                  <th>Account</th>
                                  <th>Type</th>
                                  <th>Amount</th>
                                  <th>Details</th>
                                </tr>
                              )}
                            </thead>
                            <tbody>
                              {lastTxs.map(tx => {
                                if (activeUserId === 'bank-tax-user') {
                                  // Find the owner of the related account in the frontend users list
                                  const owner = users.find(u => u.accounts.some(a => a.id === tx.related_account_id));
                                  const originLabel = owner
                                    ? `👤 ${owner.name} (${tx.related_account_id?.substring(0, 8)}...)`
                                    : tx.related_account_id
                                      ? `💳 ${tx.related_account_id.substring(0, 8)}...`
                                      : '-';

                                  return (
                                    <tr key={tx.id}>
                                      <td>{new Date(tx.timestamp).toLocaleString()}</td>
                                      <td>{tx.accountName}</td>
                                      <td><strong>{originLabel}</strong></td>
                                      <td><span style={{ color: 'var(--accent-cyan)' }}>+{tx.amount.toFixed(2)} {tx.currency}</span></td>
                                      <td>{tx.description || '-'}</td>
                                    </tr>
                                  );
                                } else {
                                  return (
                                    <tr key={tx.id} style={tx.type === 'TRANSFER_REJECTED' ? { textDecoration: 'line-through', opacity: 0.6 } : undefined}>
                                      <td>{new Date(tx.timestamp).toLocaleString()}</td>
                                      <td>{tx.accountName}</td>
                                      <td>
                                        <span className={`badge ${tx.type === 'DEPOSIT' || tx.type === 'TRANSFER_IN' ? 'badge-emerald' : 'badge-rose'}`} style={tx.type === 'TRANSFER_REJECTED' ? { background: 'rgba(244, 63, 94, 0.2)', borderColor: 'var(--accent-rose)', color: 'var(--text-muted)' } : undefined}>
                                          {tx.type === 'TRANSFER_REJECTED' ? 'REJECTED' : tx.type}
                                        </span>
                                      </td>
                                      <td><strong>{tx.amount.toFixed(2)} {tx.currency}</strong></td>
                                      <td>{tx.description || (tx.related_account_id ? `Related: ${tx.related_account_id.substring(0, 8)}...` : '-')}</td>
                                    </tr>
                                  );
                                }
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* --- TAB 2: TRANSFER SYSTEM --- */}
            {activeTab === 'transfer' && (
              <div style={{ maxWidth: '600px', margin: '0 auto' }}>
                {!activeUser ? (
                  <div className="glass-panel" style={{ textAlign: 'center' }}>
                    <p style={{ color: 'var(--text-secondary)' }}>Select an active client to execute transfers.</p>
                  </div>
                ) : (
                  <div className="glass-panel">
                    <h3 style={{ marginBottom: '1.5rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                      <ArrowRightLeft size={20} style={{ color: 'var(--accent-cyan)' }} /> Send Funds
                    </h3>
                    
                    <form onSubmit={handleTransfer}>
                      <div className="form-group">
                        <label className="form-label">Source Account</label>
                        <select 
                          className="form-select"
                          value={transferSourceId}
                          onChange={(e) => setTransferSourceId(e.target.value)}
                          required
                        >
                          <option value="">-- Choose source --</option>
                          {activeUser.accounts.map(acc => (
                            <option key={acc.id} value={acc.id} disabled={acc.is_frozen}>
                              {acc.account_type} ({acc.currency}) - Balance: {acc.balance.toFixed(2)} {acc.currency} {acc.is_frozen ? '[GELÉ]' : ''}
                            </option>
                          ))}
                        </select>
                      </div>

                      {/* Recipient Dropdown Registry selector (Issue 4) */}
                      <div className="form-group">
                        <label className="form-label">Recipient Account Selector (Quick select)</label>
                        <select
                          className="form-select"
                          value={transferTargetId}
                          onChange={(e) => setTransferTargetId(e.target.value)}
                        >
                          <option value="">-- Select from client registry --</option>
                          {users
                            .filter(u => u.id !== 'admin-user' && u.id !== 'bank-tax-user')
                            .flatMap(u => u.accounts.map(acc => ({
                              id: acc.id,
                              label: `${u.id === activeUser.id ? '⭐' : `👤 ${u.name}`} - ${acc.account_type} (${acc.currency}) - ID: ${acc.id.substring(0, 8)}... (Bal: ${acc.balance} ${acc.currency})`
                            })))
                            .filter(opt => opt.id !== transferSourceId)
                            .map(opt => (
                              <option key={opt.id} value={opt.id}>
                                {opt.label}
                              </option>
                            ))}
                        </select>
                      </div>

                      <div className="form-group">
                        <label className="form-label">Recipient Account ID (UUID)</label>
                        <input 
                          type="text" 
                          placeholder="Enter recipient account ID" 
                          className="form-input"
                          value={transferTargetId}
                          onChange={(e) => setTransferTargetId(e.target.value)}
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label className="form-label">Amount</label>
                        <input 
                          type="number" 
                          step="0.01" 
                          placeholder="0.00" 
                          className="form-input"
                          value={transferAmount}
                          onChange={(e) => setTransferAmount(e.target.value)}
                          required
                        />
                      </div>

                      <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '1rem' }}>
                        Confirm Transfer
                      </button>
                    </form>

                    {/* Exchange rates preview card (uses rates & margin to prevent unused vars error) */}
                    <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px dashed var(--border-color)', fontSize: '0.85rem' }}>
                      <h4 style={{ color: 'var(--accent-cyan)', marginBottom: '0.75rem' }}>Bank Exchange Rates Info</h4>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', color: 'var(--text-secondary)' }}>
                        <div>EUR to CHF: <strong>{rates['EUR'] ? (rates['CHF'] / rates['EUR']).toFixed(4) : '...'}</strong></div>
                        <div>USD to CHF: <strong>{rates['USD'] ? (rates['CHF'] / rates['USD']).toFixed(4) : '...'}</strong></div>
                        <div>EUR to USD: <strong>{rates['EUR'] && rates['USD'] ? (rates['USD'] / rates['EUR']).toFixed(4) : '...'}</strong></div>
                        <div>Transfer Margin fee: <strong>{(margin * 100).toFixed(2)}%</strong></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* --- TAB 3: TRANSACTION HISTORY --- */}
            {activeTab === 'history' && (
              <div>
                {isAdmin ? (
                  <AdminHistoryExplorer users={users} />
                ) : !activeUser || activeUser.accounts.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>No accounts available to check history.</p>
                ) : (
                  <div>
                    {activeUser.accounts.map(acc => (
                      <div key={acc.id} className="glass-panel" style={{ padding: '1.5rem' }}>
                        <h4 style={{ marginBottom: '1rem', color: 'var(--accent-cyan)' }}>
                          {acc.account_type} Account ({acc.currency}) - {acc.id}
                        </h4>
                        <AccountHistoryRow accountId={acc.id} />
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* --- TAB 4: ADMIN CLIENTS MANAGER --- */}
            {activeTab === 'accounts' && isAdmin && (
              <div>
                {/* Client Creation Form */}
                <div className="glass-panel">
                  <h3 style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Plus size={20} style={{ color: 'var(--accent-emerald)' }} /> Register New Client
                  </h3>
                  <form onSubmit={handleCreateUser} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <input 
                      type="text" 
                      placeholder="Client Name (e.g. Alice)" 
                      className="form-input" 
                      style={{ flex: 1, minWidth: '250px' }}
                      value={newUserName}
                      onChange={(e) => setNewUserName(e.target.value)}
                    />
                    <button type="submit" className="btn btn-primary">Create Client</button>
                  </form>
                </div>

                {/* Clients list */}
                <div className="glass-panel">
                  <h3 style={{ marginBottom: '1.5rem' }}>Bank Accounts Registry</h3>
                  {users.filter(u => u.id !== 'admin-user').map(u => (
                    <div key={u.id} style={{ borderBottom: '1px solid var(--border-color)', padding: '1.5rem 0', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
                        <div>
                          <strong style={{ fontSize: '1.1rem' }}>{u.name}</strong>
                          <span style={{ marginLeft: '1rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: {u.id}</span>
                        </div>
                        
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
                          <span className={`badge ${u.is_active ? 'badge-emerald' : 'badge-rose'}`}>
                            {u.is_active ? 'Active' : 'Deactivated'}
                          </span>
                          
                          {u.is_active && u.id !== 'bank-tax-user' && (
                            <button onClick={() => handleDeactivateUser(u.id)} className="btn btn-rose" style={{ padding: '0.35rem 0.75rem', fontSize: '0.8rem' }}>
                              Deactivate Client
                            </button>
                          )}

                          {/* Dynamic Account Creation Select Form (Issue 2) */}
                          {u.is_active && u.id !== 'bank-tax-user' && (() => {
                            const allCombinations = [
                              { type: 'CURRENT', currency: 'CHF', label: 'Current (CHF)' },
                              { type: 'CURRENT', currency: 'EUR', label: 'Current (EUR)' },
                              { type: 'CURRENT', currency: 'USD', label: 'Current (USD)' },
                              { type: 'SAVINGS', currency: 'CHF', label: 'Savings (CHF)' },
                              { type: 'SAVINGS', currency: 'EUR', label: 'Savings (EUR)' },
                              { type: 'SAVINGS', currency: 'USD', label: 'Savings (USD)' }
                            ];
                            
                            const available = allCombinations.filter(comb => 
                              !u.accounts.some(a => a.account_type === comb.type && a.currency === comb.currency)
                            );
                            
                            if (available.length === 0) {
                              return <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>[Max accounts opened]</span>;
                            }
                            
                            return (
                              <form onSubmit={(e) => {
                                e.preventDefault();
                                const fd = new FormData(e.currentTarget);
                                const combo = fd.get('combo') as string;
                                const [type, currency] = combo.split('-');
                                handleOpenAccount(u.id, type as 'CURRENT' | 'SAVINGS', currency as 'CHF' | 'EUR' | 'USD');
                              }} style={{ display: 'inline-flex', gap: '0.35rem', alignItems: 'center', background: 'rgba(255,255,255,0.02)', padding: '0.25rem 0.5rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                                <select name="combo" className="form-select" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem', width: 'auto', background: '#0b0f19' }} required>
                                  {available.map(comb => (
                                    <option key={`${comb.type}-${comb.currency}`} value={`${comb.type}-${comb.currency}`}>
                                      {comb.label}
                                    </option>
                                  ))}
                                </select>
                                <button type="submit" className="btn btn-emerald" style={{ padding: '0.25rem 0.6rem', fontSize: '0.8rem' }}>
                                  + Open Account
                                </button>
                              </form>
                            );
                          })()}
                        </div>
                      </div>

                      {/* Accounts of this client, sorted by creation date (Issue 3 & 5) */}
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem', marginLeft: '1rem' }}>
                        {[...u.accounts]
                          .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
                          .map((acc, index) => (
                            <div key={acc.id} style={{ background: 'rgba(0,0,0,0.15)', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1rem' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>
                                  {acc.account_type} ({acc.currency})
                                  {index === 0 && <span style={{ color: 'var(--accent-cyan)', fontSize: '0.75rem', marginLeft: '0.4rem' }}>[Base Account]</span>}
                                </span>
                                <span className={`badge ${acc.is_frozen ? 'badge-rose' : 'badge-emerald'}`}>{acc.is_frozen ? 'Frozen' : 'Unlocked'}</span>
                              </div>
                              
                              <div style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0.5rem 0' }}>
                                {acc.balance.toFixed(2)} {acc.currency}
                              </div>
                              
                              <div style={{ display: 'flex', gap: '0.35rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                                <button onClick={() => handleToggleFreeze(acc)} className="btn" style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem', background: acc.is_frozen ? 'var(--accent-emerald-glow)' : 'var(--accent-rose-glow)', color: acc.is_frozen ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                                  {acc.is_frozen ? <Unlock size={12} /> : <Lock size={12} />} {acc.is_frozen ? 'Unlock' : 'Freeze'}
                                </button>

                                <button onClick={() => {
                                  setEditingLimitAccountId(acc.id);
                                  setNewWithdrawalLimit(acc.daily_withdrawal_limit.toString());
                                  setNewTransferLimit(acc.daily_transfer_limit.toString());
                                  setNewMaxTransfers(acc.max_daily_transfers.toString());
                                }} className="btn" style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem', background: '#334155', color: '#e2e8f0' }}>
                                  <Settings size={12} /> Limits
                                </button>

                                {/* Delete button: only for additional accounts (index > 0) (Issue 3 & 5) */}
                                {index > 0 && u.id !== 'bank-tax-user' && (
                                  <button onClick={() => handleDeleteAccount(acc.id)} className="btn btn-rose" style={{ padding: '0.3rem 0.5rem', fontSize: '0.75rem' }}>
                                    <X size={12} /> Delete
                                  </button>
                                )}
                              </div>
                            </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Edit limits modal overlay */}
                {editingLimitAccountId && (
                  <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
                    <div className="glass-panel" style={{ maxWidth: '400px', width: '90%' }}>
                      <h4 style={{ marginBottom: '1.25rem' }}>Modify Account Limits</h4>
                      <form onSubmit={handleUpdateLimits}>
                        <div className="form-group">
                          <label className="form-label">Daily Withdrawal Limit</label>
                          <input type="number" className="form-input" value={newWithdrawalLimit} onChange={(e) => setNewWithdrawalLimit(e.target.value)} required />
                        </div>
                        <div className="form-group">
                          <label className="form-label">Daily Transfer Limit</label>
                          <input type="number" className="form-input" value={newTransferLimit} onChange={(e) => setNewTransferLimit(e.target.value)} required />
                        </div>
                        <div className="form-group">
                          <label className="form-label">Max Transfers Count Today</label>
                          <input type="number" className="form-input" value={newMaxTransfers} onChange={(e) => setNewMaxTransfers(e.target.value)} required />
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                          <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Save</button>
                          <button type="button" onClick={() => setEditingLimitAccountId('')} className="btn" style={{ flex: 1, background: '#334155', color: 'white' }}>Cancel</button>
                        </div>
                      </form>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* --- TAB 5: ADMIN PENDING TRANSFER REQUESTS --- */}
            {activeTab === 'pending' && isAdmin && (
              <div className="glass-panel">
                <h3 style={{ marginBottom: '1.5rem' }}>Awaiting Limits Verification</h3>
                {pendingRequests.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>No pending transfer requests found.</p>
                ) : (
                  <div className="table-container">
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Request ID</th>
                          <th>Source Account</th>
                          <th>Target Account</th>
                          <th>Amount</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {pendingRequests.map(req => (
                          <tr key={req.id}>
                            <td>{new Date(req.timestamp).toLocaleString()}</td>
                            <td><code style={{ fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>{req.id.substring(0, 18)}...</code></td>
                            <td>{req.source_account_id.substring(0, 13)}...</td>
                            <td>{req.target_account_id.substring(0, 13)}...</td>
                            <td style={{ fontWeight: 700 }}>{req.amount.toFixed(2)}</td>
                            <td>
                              <div style={{ display: 'flex', gap: '0.25rem' }}>
                                <button onClick={() => handleResolvePending(req.id, true)} className="btn btn-emerald" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>
                                  Approve
                                </button>
                                <button onClick={() => handleResolvePending(req.id, false)} className="btn btn-rose" style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem' }}>
                                  Reject
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}

            {/* --- TAB 6: ADMIN AUDIT LOGS --- */}
            {activeTab === 'audit' && isAdmin && (
              <div className="glass-panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                  <h3>System Security Audit trail</h3>
                  <div style={{ position: 'relative', maxWidth: '300px', width: '100%' }}>
                    <Search size={16} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input 
                      type="text" 
                      placeholder="Search logs..." 
                      className="form-input" 
                      style={{ paddingLeft: '2.5rem' }}
                      value={auditSearch}
                      onChange={(e) => setAuditSearch(e.target.value)}
                    />
                  </div>
                </div>

                <div className="table-container" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th style={{ width: '200px' }}>Timestamp</th>
                        <th style={{ width: '150px' }}>Action</th>
                        <th>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLogs.map(log => (
                        <tr key={log.id}>
                          <td>{new Date(log.timestamp).toLocaleString()}</td>
                          <td>
                            <span className="badge badge-orange">{log.action}</span>
                          </td>
                          <td style={{ fontSize: '0.85rem' }}>{log.details}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* --- ADMIN LOGIN MODAL OVERLAY --- */}
      {showLoginModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.75)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="glass-panel" style={{ maxWidth: '400px', width: '90%', border: '1px solid var(--accent-cyan)' }}>
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <Lock size={36} style={{ color: 'var(--accent-cyan)', marginBottom: '0.5rem' }} />
              <h4>Administrative Access Required</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Enter system password to open operations console.</p>
            </div>

            {loginError && (
              <div style={{ background: 'var(--accent-rose-glow)', border: '1px solid var(--accent-rose)', color: '#fca5a5', padding: '0.5rem', borderRadius: '8px', fontSize: '0.85rem', marginBottom: '1rem', textAlign: 'center' }}>
                {loginError}
              </div>
            )}

            <form onSubmit={handleAdminLogin}>
              <div className="form-group">
                <label className="form-label">Password</label>
                <input 
                  type="password" 
                  placeholder="•••••" 
                  className="form-input" 
                  style={{ textAlign: 'center', fontSize: '1.25rem', letterSpacing: '0.1em' }}
                  value={adminPassword}
                  onChange={(e) => setAdminPassword(e.target.value)}
                  required 
                  autoFocus
                />
              </div>

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }}>Authenticate</button>
                <button type="button" onClick={() => setShowLoginModal(false)} className="btn" style={{ flex: 1, background: '#334155', color: 'white' }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;