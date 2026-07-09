// Mock auth store — simulates NextAuth + bcrypt on the frontend
// Users and sessions are persisted to localStorage (mock DB)
// Passwords are "hashed" with a simple salted sha-style fingerprint (demo only)

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: "user";
  createdAt: string;
}

interface StoredUser extends AuthUser {
  passwordHash: string;
}

const USERS_KEY = "greenspot.users";
const SESSION_KEY = "greenspot.session";

// ── Simple deterministic hash (demo, not cryptographic) ─────────────
function hashPassword(password: string, salt: string): string {
  let h = 0;
  const str = salt + password + "gs2026";
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h + str.charCodeAt(i)) | 0;
  }
  return `$gs$${salt}$${Math.abs(h).toString(36)}`;
}

function makeSalt(): string {
  return Math.random().toString(36).slice(2, 10);
}

function verifyPassword(password: string, hash: string): boolean {
  const parts = hash.split("$");
  if (parts[1] !== "gs" || parts.length < 4) return false;
  return hashPassword(password, parts[2]) === hash;
}

function makeCuid(): string {
  return "c" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8);
}

// ── User store ───────────────────────────────────────────────────────
function loadUsers(): StoredUser[] {
  try {
    return JSON.parse(localStorage.getItem(USERS_KEY) ?? "[]");
  } catch {
    return [];
  }
}

function saveUsers(users: StoredUser[]) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

// ── Session ──────────────────────────────────────────────────────────
export function loadSession(): AuthUser | null {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSession(user: AuthUser) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

// ── Auth actions ─────────────────────────────────────────────────────
export type AuthError =
  | "EMAIL_REQUIRED"
  | "NAME_REQUIRED"
  | "PASSWORD_TOO_SHORT"
  | "EMAIL_INVALID"
  | "EMAIL_TAKEN"
  | "INVALID_CREDENTIALS";

export interface RegisterInput {
  name: string;
  email: string;
  password: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export function register(input: RegisterInput): { user: AuthUser } | { error: AuthError } {
  const name = input.name.trim();
  const email = input.email.trim().toLowerCase();
  const { password } = input;

  if (!name || name.length < 2) return { error: "NAME_REQUIRED" };
  if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return { error: "EMAIL_INVALID" };
  if (!password || password.length < 6) return { error: "PASSWORD_TOO_SHORT" };

  const users = loadUsers();
  if (users.some((u) => u.email === email)) return { error: "EMAIL_TAKEN" };

  const salt = makeSalt();
  const user: AuthUser = {
    id: makeCuid(),
    name,
    email,
    role: "user",
    createdAt: new Date().toISOString(),
  };
  users.push({ ...user, passwordHash: hashPassword(password, salt) });
  saveUsers(users);
  saveSession(user);
  return { user };
}

export function login(input: LoginInput): { user: AuthUser } | { error: AuthError } {
  const email = input.email.trim().toLowerCase();
  const users = loadUsers();
  const stored = users.find((u) => u.email === email);
  if (!stored || !verifyPassword(input.password, stored.passwordHash)) {
    return { error: "INVALID_CREDENTIALS" };
  }
  const user: AuthUser = { id: stored.id, name: stored.name, email: stored.email, role: stored.role, createdAt: stored.createdAt };
  saveSession(user);
  return { user };
}

export const AUTH_ERROR_MSG: Record<AuthError, string> = {
  EMAIL_REQUIRED: "올바른 이메일을 입력해 주세요.",
  NAME_REQUIRED: "이름은 2자 이상 입력해 주세요.",
  PASSWORD_TOO_SHORT: "비밀번호는 최소 6자 이상이어야 합니다.",
  EMAIL_INVALID: "올바른 이메일 형식을 입력해 주세요.",
  EMAIL_TAKEN: "이미 사용 중인 이메일입니다.",
  INVALID_CREDENTIALS: "이메일 또는 비밀번호가 올바르지 않습니다.",
};

// ── Per-user bookmark store ──────────────────────────────────────────
export interface UserBookmark {
  id: string;
  userId: string;
  parcelId: string;
  parcelName: string;
  district: string;
  topRecommendation: string;
  topScore: number;
  sumokScore?: number;
  feasibilityStatus?: string;
  createdAt: string;
}

function bookmarkKey(userId: string) {
  return `greenspot.bookmarks.${userId}`;
}

export function loadBookmarks(userId: string): UserBookmark[] {
  try {
    return JSON.parse(localStorage.getItem(bookmarkKey(userId)) ?? "[]");
  } catch {
    return [];
  }
}

function saveBookmarks(userId: string, items: UserBookmark[]) {
  localStorage.setItem(bookmarkKey(userId), JSON.stringify(items));
}

export function toggleBookmarkForUser(
  userId: string,
  data: Omit<UserBookmark, "id" | "userId" | "createdAt">,
): { bookmarks: UserBookmark[]; bookmarked: boolean } {
  const items = loadBookmarks(userId);
  const idx = items.findIndex((b) => b.parcelId === data.parcelId);
  if (idx >= 0) {
    items.splice(idx, 1);
    saveBookmarks(userId, items);
    return { bookmarks: items, bookmarked: false };
  }
  const next: UserBookmark = { id: makeCuid(), userId, createdAt: new Date().toISOString(), ...data };
  const updated = [next, ...items];
  saveBookmarks(userId, updated);
  return { bookmarks: updated, bookmarked: true };
}

export function isBookmarkedByUser(userId: string, parcelId: string): boolean {
  return loadBookmarks(userId).some((b) => b.parcelId === parcelId);
}
