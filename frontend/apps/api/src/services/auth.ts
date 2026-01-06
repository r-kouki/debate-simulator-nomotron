import { readFile, writeFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHmac, timingSafeEqual } from "node:crypto";

const __dirname = dirname(fileURLToPath(import.meta.url));
const USERS_FILE = join(__dirname, "../data/users.json");
const SECRET_KEY = process.env.AUTH_SECRET || "debate-simulator-secret-key-change-in-production";

export type User = {
    id: string;
    username: string;
    passwordHash: string;
    playerId: string;
    createdAt: string;
    lastLoginAt: string;
};

type UsersData = {
    users: User[];
};

// Simple password hashing using HMAC-SHA256 (for production, use bcrypt)
const hashPassword = (password: string): string => {
    return createHmac("sha256", SECRET_KEY).update(password).digest("hex");
};

const verifyPassword = (password: string, hash: string): boolean => {
    const inputHash = hashPassword(password);
    try {
        return timingSafeEqual(Buffer.from(inputHash), Buffer.from(hash));
    } catch {
        return false;
    }
};

// Generate a simple signed token
const generateToken = (userId: string, username: string): string => {
    const payload = JSON.stringify({ userId, username, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 });
    const encoded = Buffer.from(payload).toString("base64");
    const signature = createHmac("sha256", SECRET_KEY).update(encoded).digest("hex");
    return `${encoded}.${signature}`;
};

// Verify a token
export const verifyToken = (token: string): { userId: string; username: string } | null => {
    try {
        const [encoded, signature] = token.split(".");
        if (!encoded || !signature) return null;

        const expectedSignature = createHmac("sha256", SECRET_KEY).update(encoded).digest("hex");
        if (!timingSafeEqual(Buffer.from(signature), Buffer.from(expectedSignature))) return null;

        const payload = JSON.parse(Buffer.from(encoded, "base64").toString());
        if (payload.exp < Date.now()) return null;

        return { userId: payload.userId, username: payload.username };
    } catch {
        return null;
    }
};

// Read users from file
const readUsers = async (): Promise<UsersData> => {
    try {
        const data = await readFile(USERS_FILE, "utf-8");
        return JSON.parse(data);
    } catch {
        return { users: [] };
    }
};

// Write users to file
const writeUsers = async (data: UsersData): Promise<void> => {
    await writeFile(USERS_FILE, JSON.stringify(data, null, 2));
};

// Register a new user
export const registerUser = async (
    username: string,
    password: string
): Promise<{ success: true; token: string; user: Omit<User, "passwordHash"> } | { success: false; error: string }> => {
    const data = await readUsers();

    // Check if username already exists
    if (data.users.find((u) => u.username.toLowerCase() === username.toLowerCase())) {
        return { success: false, error: "Username already exists" };
    }

    // Validate inputs
    if (username.length < 3 || username.length > 20) {
        return { success: false, error: "Username must be 3-20 characters" };
    }
    if (password.length < 6) {
        return { success: false, error: "Password must be at least 6 characters" };
    }

    const now = new Date().toISOString();
    const newUser: User = {
        id: randomUUID(),
        username,
        passwordHash: hashPassword(password),
        playerId: randomUUID(),
        createdAt: now,
        lastLoginAt: now
    };

    data.users.push(newUser);
    await writeUsers(data);

    const token = generateToken(newUser.id, newUser.username);
    const { passwordHash: _, ...userWithoutPassword } = newUser;

    return { success: true, token, user: userWithoutPassword };
};

// Login a user
export const loginUser = async (
    username: string,
    password: string
): Promise<{ success: true; token: string; user: Omit<User, "passwordHash"> } | { success: false; error: string }> => {
    const data = await readUsers();

    const user = data.users.find((u) => u.username.toLowerCase() === username.toLowerCase());
    if (!user) {
        return { success: false, error: "Invalid username or password" };
    }

    if (!verifyPassword(password, user.passwordHash)) {
        return { success: false, error: "Invalid username or password" };
    }

    // Update last login
    user.lastLoginAt = new Date().toISOString();
    await writeUsers(data);

    const token = generateToken(user.id, user.username);
    const { passwordHash: _, ...userWithoutPassword } = user;

    return { success: true, token, user: userWithoutPassword };
};

// Get user by token
export const getUserFromToken = async (
    token: string
): Promise<{ success: true; user: Omit<User, "passwordHash"> } | { success: false; error: string }> => {
    const verified = verifyToken(token);
    if (!verified) {
        return { success: false, error: "Invalid or expired token" };
    }

    const data = await readUsers();
    const user = data.users.find((u) => u.id === verified.userId);
    if (!user) {
        return { success: false, error: "User not found" };
    }

    const { passwordHash: _, ...userWithoutPassword } = user;
    return { success: true, user: userWithoutPassword };
};
