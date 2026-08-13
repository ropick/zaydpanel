import { NextRequest, NextResponse } from "next/server";

const AGENT_URL = process.env.AGENT_URL || "http://127.0.0.1:8442";
const AGENT_SECRET = process.env.AGENT_SECRET || "zc-agent-2026-secret";

async function proxyRequest(request: NextRequest, pathSegments: string[]): Promise<NextResponse> {
  const agentPath = "/" + pathSegments.join("/");
  try {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${AGENT_SECRET}`,
      "Content-Type": "application/json",
    };
    // Pass user JWT token if present
    const authHeader = request.headers.get("Authorization");
    if (authHeader && authHeader.startsWith("Bearer ") && !authHeader.includes(AGENT_SECRET)) {
      headers["X-User-Token"] = authHeader.replace("Bearer ", "");
    }
    // Also check cookie
    const cookies = request.headers.get("Cookie") || "";
    const match = cookies.match(/zaydpanel_token=([^;]+)/);
    if (match) headers["X-User-Token"] = match[1];

    const body = request.method !== "GET" ? await request.text() : undefined;
    const res = await fetch(`${AGENT_URL}${agentPath}`, { method: request.method, headers, body });
    const data = await res.text();
    return new NextResponse(data, { status: res.status, headers: { "Content-Type": res.headers.get("Content-Type") || "application/json" } });
  } catch (err) {
    return NextResponse.json({ success: false, error: err instanceof Error ? err.message : "Agent unreachable" }, { status: 502 });
  }
}

export async function GET(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(request, path);
}
export async function POST(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(request, path);
}
export async function PUT(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(request, path);
}
export async function DELETE(request: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  return proxyRequest(request, path);
}
