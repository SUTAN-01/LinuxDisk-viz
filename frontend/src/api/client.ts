export interface ApiError {
  status: number;
  message: string;
}

export class ApiClient {
  _fetch: typeof fetch;
  private baseUrl: string;
  private readToken: string;
  private writeToken: string;

  constructor(baseUrl: string, readToken: string, writeToken: string) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.readToken = readToken;
    this.writeToken = writeToken;
    this._fetch = fetch.bind(globalThis);
  }

  private tokenFor(requireWrite: boolean): string {
    return requireWrite ? this.writeToken : this.readToken;
  }

  private url(path: string): string {
    return this.baseUrl + (path.startsWith("/") ? path : "/" + path);
  }

  async get(path: string, requireWrite = false): Promise<any> {
    return this._request("GET", path, undefined, requireWrite);
  }

  async post(path: string, body?: any, requireWrite = true): Promise<any> {
    return this._request("POST", path, body, requireWrite);
  }

  async delete(path: string, requireWrite = true): Promise<any> {
    return this._request("DELETE", path, undefined, requireWrite);
  }

  private async _request(
    method: string,
    path: string,
    body: any,
    requireWrite: boolean,
  ): Promise<any> {
    const headers: Record<string, string> = {
      Authorization: "Bearer " + this.tokenFor(requireWrite),
    };
    const init: RequestInit = { method, headers };
    if (body !== undefined) {
      headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    const resp = await this._fetch(this.url(path), init);
    if (!resp.ok) {
      let msg = resp.statusText;
      try {
        const j = await resp.json();
        msg = j.detail || msg;
      } catch {
        /* not json */
      }
      const err: ApiError = { status: resp.status, message: msg };
      throw err;
    }
    const ct = resp.headers?.get("content-type") || "";
    if (ct.includes("application/json")) {
      return resp.json();
    }
    return resp;
  }

  /** Open a WebSocket. Token is sent via query param. */
  ws(path: string): WebSocket {
    const sep = path.includes("?") ? "&" : "?";
    const url = this.url(path) + sep + "token=" + encodeURIComponent(this.readToken);
    const wsUrl = url.replace(/^http/, "ws");
    return new WebSocket(wsUrl);
  }
}
