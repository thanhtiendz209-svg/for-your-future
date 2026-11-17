"""
API Client for For Your Future Frontend.
Communicates with FastAPI Backend (/api/v1) with JWT Bearer Token management and SSE Streaming.
"""

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
  role: string;
  email: string;
  name: string;
}

export interface RecommendationRequestPayload {
  target_year: number;
  student_method: string;
  student_group_code: string;
  student_score: number;
  max_annual_budget: number;
  student_gender: string;
  student_height?: number | null;
  student_eye_degree?: number | null;
  preferred_city?: string | null;
  holland_code: string;
  bonus_points?: number;
}

export interface RecommendationItem {
  university_id: string;
  university_name: string;
  university_short_name?: string;
  faculty_ratio?: number;
  facilities: string[];
  program_id: string;
  program_name: string;
  credential: string;
  benchmark_score: number;
  minimum_threshold?: number | null;
  score_margin: number;
  official_tuition: number;
  is_subsidized: boolean;
  actual_tuition: number;
  career_name: string;
  job_growth_rate: number;
  hiring_companies: string[];
  holland_match_score: number;
  city: string;
  transport_score?: number;
  safety_level: "Safe" | "Target" | "Reach";
  warning?: string | null;
}

export interface RecommendationResponse {
  total_found: number;
  target_year: number;
  holland_code: string;
  student_group_code: string;
  results: RecommendationItem[];
  empty_suggestions?: string[];
}

const API_BASE = "/api/v1";

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("for_your_future_jwt");
    }
  }

  public setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("for_your_future_jwt", token);
      } else {
        localStorage.removeItem("for_your_future_jwt");
      }
    }
  }

  public getToken(): string | null {
    return this.token;
  }

  private getHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...extraHeaders,
    };
    if (this.token) {
      headers["Authorization"] = `Bearer ${this.token}`;
    }
    return headers;
  }

  // --- AUTH ---
  public async register(payload: any): Promise<AuthToken> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Đăng ký không thành công");
    }
    const data: AuthToken = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  public async login(payload: any): Promise<AuthToken> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Email hoặc mật khẩu không chính xác");
    }
    const data: AuthToken = await res.json();
    this.setToken(data.access_token);
    return data;
  }

  public async getMe(): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error("Chưa đăng nhập");
    return res.json();
  }

  public logout() {
    this.setToken(null);
  }

  // --- PROFILE ---
  public async getProfile(): Promise<any> {
    const res = await fetch(`${API_BASE}/students/profile`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) throw new Error("Không thể tải hồ sơ");
    return res.json();
  }

  public async updateProfile(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/profile`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  public async updateBackground(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/background`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  public async updateAcademic(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/academic`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  public async updateHealth(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/health`, {
      method: "PUT",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  public async importLocal(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/students/import-local`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  // --- ASSESSMENTS ---
  public async savePersonality(payload: any): Promise<any> {
    const res = await fetch(`${API_BASE}/assessments/personality`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  public async getLatestPersonality(testType?: string): Promise<any> {
    const url = testType
      ? `${API_BASE}/assessments/personality/latest?test_type=${encodeURIComponent(testType)}`
      : `${API_BASE}/assessments/personality/latest`;
    const res = await fetch(url, { headers: this.getHeaders() });
    return res.json();
  }

  // --- UNIVERSITIES ---
  public async getUniversities(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/universities?${qs}`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }

  public async getUniversity(uniId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/universities/${uniId}`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }

  public async getUniversityPrograms(uniId: string, nganh?: string): Promise<any[]> {
    const url = nganh
      ? `${API_BASE}/universities/${uniId}/programs?nganh=${encodeURIComponent(nganh)}`
      : `${API_BASE}/universities/${uniId}/programs`;
    const res = await fetch(url, { headers: this.getHeaders() });
    return res.json();
  }

  // --- CAREERS ---
  public async getCareers(params: Record<string, string> = {}): Promise<any[]> {
    const qs = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/careers?${qs}`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }

  public async getCareer(careerId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/careers/${careerId}`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }

  public async getCareersByHolland(code: string): Promise<any[]> {
    const res = await fetch(`${API_BASE}/careers/by-holland/${code}`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }

  // --- RECOMMENDATION ENGINE ---
  public async getRecommendations(payload: RecommendationRequestPayload): Promise<RecommendationResponse> {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: "POST",
      headers: this.getHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      throw new Error("Không thể xử lý khuyến nghị nguyện vọng.");
    }
    return res.json();
  }

  // --- AI CONSULTATION SSE STREAMING ---
  public async streamConsultation(
    queryText: string,
    contextItems: any[] | null,
    onToken: (token: string) => void,
    onDone: () => void,
    onError: (err: any) => void,
    abortSignal?: AbortSignal
  ) {
    try {
      const res = await fetch(`${API_BASE}/consult/stream`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify({
          query_text: queryText,
          context_items: contextItems,
        }),
        signal: abortSignal,
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: Lỗi kết nối dịch vụ tư vấn AI.`);
      }

      const reader = res.body?.getReader();
      if (!reader) throw new Error("ReadableStream not supported");

      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data: ")) {
            const dataStr = trimmed.slice(6).trim();
            if (dataStr === "[DONE]") {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(dataStr);
              if (parsed.token) {
                onToken(parsed.token);
              }
            } catch (e) {
              // ignore parse errors on partial chunks
            }
          }
        }
      }
      onDone();
    } catch (e: any) {
      if (e.name === "AbortError") {
        console.log("Stream consultation aborted by user.");
      } else {
        onError(e);
      }
    }
  }

  // --- ADMIN & STATS ---
  public async getAdminHealth(): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/health`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }

  public async getAdminStats(): Promise<any> {
    const res = await fetch(`${API_BASE}/admin/stats`, {
      headers: this.getHeaders(),
    });
    return res.json();
  }
}

export const apiClient = new ApiClient();
