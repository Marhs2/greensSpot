import { useState } from "react";
import { Leaf, Mail, Lock, User, ArrowLeft, Eye, EyeOff, Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { login as apiLogin, signup as apiSignup, ApiError } from "../../lib/api";
import type { AuthUser } from "../../lib/types";

function AuthCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <span className="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-md">
            <Leaf className="size-6" strokeWidth={2.5} />
          </span>
          <div className="text-center">
            <h1 className="text-[22px] tracking-tight text-foreground">GreenSpot</h1>
            <p className="text-[13px] text-muted-foreground">서울 도시 녹지 인프라 분석 플랫폼</p>
          </div>
        </div>
        {children}
      </div>
    </div>
  );
}

function FieldWrapper({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-[13px] text-foreground">{label}</Label>
      {children}
    </div>
  );
}

export function LoginPage({
  onSuccess,
  onGoRegister,
  onGuest,
}: {
  onSuccess: (user: AuthUser) => void;
  onGoRegister: () => void;
  onGuest: () => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await apiLogin(email.trim(), password);
      onSuccess(user);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "로그인에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard>
      <div className="rounded-xl border border-border bg-card p-7 shadow-sm">
        <h2 className="mb-1 text-[18px] text-foreground">로그인</h2>
        <p className="mb-6 text-[13px] text-muted-foreground">GreenSpot에 로그인하세요</p>

        <form onSubmit={submit} className="space-y-4">
          <FieldWrapper label="이메일">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-9"
                required
                autoComplete="email"
              />
            </div>
          </FieldWrapper>

          <FieldWrapper label="비밀번호">
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type={showPw ? "text" : "password"}
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-9 pr-10"
                required
                autoComplete="current-password"
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                tabIndex={-1}
              >
                {showPw ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
          </FieldWrapper>

          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-[12px] text-destructive">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : null}
            로그인
          </Button>
        </form>

        <div className="mt-4 text-center text-[13px] text-muted-foreground">
          계정이 없으신가요?{" "}
          <button onClick={onGoRegister} className="font-medium text-primary hover:underline">
            회원가입
          </button>
        </div>
      </div>

      <button
        onClick={onGuest}
        className="mt-4 flex w-full items-center justify-center gap-2 text-[13px] text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" /> 로그인 없이 둘러보기
      </button>
    </AuthCard>
  );
}

export function RegisterPage({
  onSuccess,
  onGoLogin,
  onGuest,
}: {
  onSuccess: (user: AuthUser) => void;
  onGoLogin: () => void;
  onGuest: () => void;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (name.trim().length < 2) {
      setError("이름은 2자 이상 입력해 주세요.");
      return;
    }
    if (password.length < 6) {
      setError("비밀번호는 최소 6자 이상이어야 합니다.");
      return;
    }
    setLoading(true);
    try {
      const user = await apiSignup(name.trim(), email.trim(), password);
      onSuccess(user);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "회원가입에 실패했습니다.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthCard>
      <div className="rounded-xl border border-border bg-card p-7 shadow-sm">
        <h2 className="mb-1 text-[18px] text-foreground">회원가입</h2>
        <p className="mb-6 text-[13px] text-muted-foreground">GreenSpot 계정을 만드세요</p>

        <form onSubmit={submit} className="space-y-4">
          <FieldWrapper label="이름">
            <div className="relative">
              <User className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="홍길동"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="pl-9"
                required
                minLength={2}
                autoComplete="name"
              />
            </div>
          </FieldWrapper>

          <FieldWrapper label="이메일">
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="pl-9"
                required
                autoComplete="email"
              />
            </div>
          </FieldWrapper>

          <FieldWrapper label="비밀번호">
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type={showPw ? "text" : "password"}
                placeholder="최소 6자"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="pl-9 pr-10"
                required
                autoComplete="new-password"
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                tabIndex={-1}
              >
                {showPw ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
              </button>
            </div>
            <p className="text-[11px] text-muted-foreground">비밀번호는 최소 6자 이상 · 서버에서 안전하게 해시 저장됩니다.</p>
          </FieldWrapper>

          {error && (
            <p className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-[12px] text-destructive">
              {error}
            </p>
          )}

          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? <Loader2 className="size-4 animate-spin" /> : null}
            회원가입
          </Button>
        </form>

        <div className="mt-4 text-center text-[13px] text-muted-foreground">
          이미 계정이 있으신가요?{" "}
          <button onClick={onGoLogin} className="font-medium text-primary hover:underline">
            로그인
          </button>
        </div>
      </div>

      <button
        onClick={onGuest}
        className="mt-4 flex w-full items-center justify-center gap-2 text-[13px] text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" /> 로그인 없이 둘러보기
      </button>
    </AuthCard>
  );
}