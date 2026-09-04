import { NextRequest, NextResponse } from "next/server";

const PROTECTED_PREFIXES = ["/dashboard", "/verification", "/checkpoints", "/users", "/settings"];

export function middleware(request: NextRequest) {
  const token = request.cookies.get("bvp_access_token")?.value;
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));

  if (isProtected && !token) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*", "/verification/:path*", "/checkpoints/:path*", "/users/:path*", "/settings/:path*"],
};
