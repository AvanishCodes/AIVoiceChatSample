import {
  BenchmarkItem,
  ChatMessage,
  CustomerProfile,
  DemoUser,
  SampleTicketScenario,
  SqlQueryResult,
  TicketBrief,
  TokenResponse,
  User,
} from '../types';

const API_BASE = '/api';

class ApiService {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    this.accessToken = localStorage.getItem('fleetpanda_access_token');
    this.refreshToken = localStorage.getItem('fleetpanda_refresh_token');
  }

  public setTokens(access: string, refresh: string) {
    this.accessToken = access;
    this.refreshToken = refresh;
    localStorage.setItem('fleetpanda_access_token', access);
    localStorage.setItem('fleetpanda_refresh_token', refresh);
  }

  public clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    localStorage.removeItem('fleetpanda_access_token');
    localStorage.removeItem('fleetpanda_refresh_token');
  }

  public getAccessToken(): string | null {
    return this.accessToken;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (this.accessToken && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
      });

      if (response.status === 401 && retryCount === 0 && this.refreshToken) {
        // Attempt token refresh
        const refreshed = await this.refreshAuthToken();
        if (refreshed) {
          return this.request<T>(endpoint, options, retryCount + 1);
        }
      }

      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (err: any) {
      console.error(`API Error on ${endpoint}:`, err);
      throw err;
    }
  }

  public async login(email: string, password: string): Promise<TokenResponse> {
    const res = await this.request<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setTokens(res.access_token, res.refresh_token);
    return res;
  }

  public async refreshAuthToken(): Promise<boolean> {
    if (!this.refreshToken) return false;
    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: this.refreshToken }),
      });
      if (res.ok) {
        const data = await res.json();
        this.setTokens(data.access_token, data.refresh_token);
        return true;
      }
    } catch (e) {
      console.warn('Failed to refresh token:', e);
    }
    this.clearTokens();
    return false;
  }

  public async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  public async getDemoUsers(): Promise<DemoUser[]> {
    return this.request<DemoUser[]>('/auth/demo-users');
  }

  public async sendChatMessage(
    message: string,
    tenant_id?: number | null,
    provider?: string,
    enable_voice = false
  ) {
    return this.request<any>('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        tenant_id,
        provider,
        enable_voice_response: enable_voice,
      }),
    });
  }

  public async sendVoiceMessage(
    audioBlob: Blob,
    tenant_id?: number | null,
    provider?: string
  ) {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    if (tenant_id !== undefined && tenant_id !== null) {
      formData.append('tenant_id', String(tenant_id));
    }
    if (provider) {
      formData.append('provider', provider);
    }

    return this.request<any>('/voice', {
      method: 'POST',
      body: formData,
    });
  }

  public async executeSqlQuery(
    query: string,
    tenant_id?: number | null,
    provider?: string
  ): Promise<SqlQueryResult> {
    return this.request<SqlQueryResult>('/sql/query', {
      method: 'POST',
      body: JSON.stringify({
        query,
        tenant_id,
        provider,
      }),
    });
  }

  public async getSqlBenchmarks(): Promise<BenchmarkItem[]> {
    return this.request<BenchmarkItem[]>('/sql/benchmark');
  }

  public async triageTicket(ticketData: Record<string, any>): Promise<TicketBrief> {
    return this.request<TicketBrief>('/triage/ticket', {
      method: 'POST',
      body: JSON.stringify(ticketData),
    });
  }

  public async getTriageSamples(): Promise<SampleTicketScenario[]> {
    return this.request<SampleTicketScenario[]>('/triage/samples');
  }

  public async getTenants(): Promise<CustomerProfile[]> {
    return this.request<CustomerProfile[]>('/tenants');
  }

  public async synthesizeSpeech(text: string): Promise<Blob> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    const res = await fetch(`${API_BASE}/audio/synthesize`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ text }),
    });

    if (!res.ok) throw new Error('Speech synthesis failed');
    return await res.blob();
  }
}

export const api = new ApiService();

