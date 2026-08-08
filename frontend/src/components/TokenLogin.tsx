import { useState } from "react";

interface TokenLoginProps {
  onLogin: (readToken: string, writeToken: string) => void;
}

export function TokenLogin({ onLogin }: TokenLoginProps) {
  const [readToken, setReadToken] = useState("");
  const [writeToken, setWriteToken] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!readToken.trim() || !writeToken.trim()) return;
    onLogin(readToken.trim(), writeToken.trim());
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>diskviz 登录</h2>
      <div>
        <label htmlFor="read-token">read-token</label>
        <input
          id="read-token"
          aria-label="read-token"
          type="password"
          value={readToken}
          onChange={(e) => setReadToken(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="write-token">write-token</label>
        <input
          id="write-token"
          aria-label="write-token"
          type="password"
          value={writeToken}
          onChange={(e) => setWriteToken(e.target.value)}
        />
      </div>
      <button type="submit">登录</button>
    </form>
  );
}
