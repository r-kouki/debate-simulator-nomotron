import type { FastifyInstance } from "fastify";
import { ZodTypeProvider } from "@fastify/type-provider-zod";
import { z } from "zod";
import { registerUser, loginUser, getUserFromToken } from "../services/auth";

// Request/Response schemas
const AuthRequestSchema = z.object({
    username: z.string().min(3).max(20),
    password: z.string().min(6)
});

const AuthUserSchema = z.object({
    id: z.string(),
    username: z.string(),
    playerId: z.string(),
    createdAt: z.string(),
    lastLoginAt: z.string()
});

const AuthSuccessSchema = z.object({
    success: z.literal(true),
    token: z.string(),
    user: AuthUserSchema
});

const AuthErrorSchema = z.object({
    success: z.literal(false),
    error: z.string()
});

const AuthResponseSchema = z.union([AuthSuccessSchema, AuthErrorSchema]);

const MeSuccessSchema = z.object({
    success: z.literal(true),
    user: AuthUserSchema
});

const MeResponseSchema = z.union([MeSuccessSchema, AuthErrorSchema]);

export const registerAuthRoutes = (app: FastifyInstance) => {
    const api = app.withTypeProvider<ZodTypeProvider>();

    // Register a new user
    api.post(
        "/auth/register",
        {
            schema: {
                body: AuthRequestSchema,
                response: { 200: AuthResponseSchema }
            }
        },
        async (request) => {
            const { username, password } = request.body;
            const result = await registerUser(username, password);
            return result;
        }
    );

    // Login an existing user
    api.post(
        "/auth/login",
        {
            schema: {
                body: AuthRequestSchema,
                response: { 200: AuthResponseSchema }
            }
        },
        async (request) => {
            const { username, password } = request.body;
            const result = await loginUser(username, password);
            return result;
        }
    );

    // Verify current session / get current user
    api.get(
        "/auth/me",
        {
            schema: {
                response: { 200: MeResponseSchema }
            }
        },
        async (request) => {
            const authHeader = request.headers.authorization;
            if (!authHeader || !authHeader.startsWith("Bearer ")) {
                return { success: false as const, error: "No authorization header" };
            }

            const token = authHeader.substring(7);
            const result = await getUserFromToken(token);
            return result;
        }
    );
};
